#!/usr/bin/env python3
"""V74 one-shot family-native causal action selector.

Final V74 Alpha architecture:
* harmonic completion remains the setup identity;
* EARLY and LATE completed-bar actions share one legal action universe;
* reaction/pullback/reclaim state is evidence, never a hard setup-level filter;
* one fixed bounded depth-3 boosted ensemble estimates Expected-R and P(R>0);
* a bounded counterfactual pair model arbitrates concurrently legal actions;
* admission is coverage-constrained from training years only;
* burned OOF years are evaluated once; Validation/Fresh are never loaded.

No post-decision trigger/lock/outcome state is admitted as a feature. V75 exit,
profit-capture and Grid/capital-capacity mechanics are intentionally excluded.
"""
import bisect,json,math,pathlib,statistics,sys,time
from collections import defaultdict,Counter
from v74_model_lib import load_rows,metrics,SEQUENTIAL_STATE_FEATURE_COUNT,FAMILIES,SURVIVAL_FRESH_KEYS

root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
RESEARCH=[f"Y{y}" for y in range(2016,2021)]
BURNED=["Y2021","Y2022","Y2023"];ALL=RESEARCH+BURNED
MIN_N=250;TRAIN_COVERAGE=275;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_RR=2.30;Z=1.645
REGULAR_SOURCES=("EARLY","LATE");SOURCES=("EARLY","LATE","SURVIVAL");EARLY_QUALIFICATION_FRACTION="00";LATE_QUALIFICATION_FRACTION="30";EARLY_FRACTIONS=(EARLY_QUALIFICATION_FRACTION,);LATE_FRACTIONS=(LATE_QUALIFICATION_FRACTION,);ALL_FRACTIONS=(EARLY_QUALIFICATION_FRACTION,LATE_QUALIFICATION_FRACTION);MSTAGES=("05","10","15");EARLY_MSTAGES=("15",);LATE_MSTAGES=MSTAGES
BASES=[f"R{r}_{h}_RR{rr}" for r in ("025","050") for h in ("H","D") for rr in ("35","40")]
TREE_KFEAT=30;PAIR_KFEAT=26;TREE_ROUNDS=10;PAIR_ROUNDS=8;TREE_DEPTH=3;TOP_PAIR=6
rows=load_rows(root,ALL)
if not rows:raise SystemExit("no V74 rows")

def gate(m):
    return bool(m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and
                m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0)
def qtile(v,q):
    if not v:return 0.0
    x=sorted(float(z) for z in v);p=(len(x)-1)*q;a=int(math.floor(p));b=int(math.ceil(p))
    return x[a] if a==b else x[a]*(b-p)+x[b]*(p-a)
def med(v,d=0.0):return statistics.median(v) if v else d
def key(m,b,f):return f"M{m}_{b}_F{f}"
def lev(b):return "025" if b.startswith("R025_") else "050"

def source_maps(r,src):
    if src=="EARLY":
        return (r.get("sequential",{}),r.get("sequential_rr",{}),r.get("sequential_bars",{}),
                r.get("sequential_entry_bar",{}),r.get("sequential_entry_state",{}))
    return (r.get("late_auction",{}),r.get("late_auction_rr",{}),r.get("late_auction_bars",{}),
            r.get("late_auction_entry_bars",{}),r.get("late_auction_entry_state",{}))

def outcome(r,src,m,b,f):
    om,rrm,_,_,_=source_maps(r,src);k=key(m,b,f)
    v=om.get(k);rr=rrm.get(k)
    if v is None or rr is None:return None
    try:v=float(v);rr=float(rr)
    except:return None
    if not all(math.isfinite(x) for x in (v,rr)) or rr+1e-9<MIN_RR:return None
    return v

def entry_bar(r,src,m,b,f):
    _,_,_,bm,_=source_maps(r,src)
    try:return int(bm.get(key(m,b,f),-1))
    except:return -1

def hold_bars(r,src,m,b,f):
    _,_,hm,_,_=source_maps(r,src)
    try:return max(1,int(hm.get(key(m,b,f),r.get("bars",1)) or 1))
    except:return max(1,int(r.get("bars",1) or 1))

def maturity_state(r,src,m,b,f):
    if src=="EARLY":v=r.get("sequential_state",{}).get(lev(b))
    else:v=r.get("late_auction_maturity_state",{}).get(key(m,b,f))
    if v is None or len(v)!=SEQUENTIAL_STATE_FEATURE_COUNT:return None
    try:
        z=[float(x) for x in v]
        return z if all(math.isfinite(x) for x in z) else None
    except:return None

def entry_state(r,src,m,b,f):
    _,_,_,_,em=source_maps(r,src);v=em.get(key(m,b,f))
    if v is None or len(v)!=SEQUENTIAL_STATE_FEATURE_COUNT:return None
    try:
        z=[float(x) for x in v]
        return z if all(math.isfinite(x) for x in z) else None
    except:return None

def timing_state(r,src,m,b,f,eb):
    k=key(m,b,f)
    if src=="EARLY":
        rb=r.get("sequential_reaction_bar",{}).get(k,-1)
        return [max(-1.0,min(6.0,float(eb)/10.0)),
                max(-1.0,min(6.0,float(rb)/10.0)) if rb is not None else -1.0,
                0.0,0.0]
    rb=r.get("late_auction_reaction_bars",{}).get(k,-1)
    ab=r.get("late_auction_anchor_bars",{}).get(k,-1)
    tb=r.get("late_auction_trigger_bars",{}).get(k,-1)
    return [max(-1.0,min(6.0,float(eb)/10.0)),
            max(-1.0,min(6.0,float(rb)/10.0)) if rb is not None else -1.0,
            max(-1.0,min(6.0,float(ab)/10.0)) if ab is not None else -1.0,
            max(-1.0,min(6.0,float(tb)/10.0)) if tb is not None else -1.0]

def route_cats(r,src,b,m,f,sfkey=None):
    return [1.0 if r["family"]==ff else 0.0 for ff in FAMILIES]+[
      1.0 if r["action"]=="CONTINUATION" else 0.0,
      1.0 if src=="LATE" else 0.0,
      1.0 if src=="SURVIVAL" else 0.0,
      1.0 if b.startswith("R050_") else 0.0,
      1.0 if "_D_" in b else 0.0,
      1.0 if b.endswith("RR40") else 0.0]+[
      1.0 if m==mm else 0.0 for mm in MSTAGES]+[
      1.0 if f==ff else 0.0 for ff in ALL_FRACTIONS]+[
      1.0 if sfkey==kk else 0.0 for kk in SURVIVAL_FRESH_KEYS]

def xvec(r,src,m,b,f,eb):
    # Missing reaction/path snapshots are explicit evidence, not a hard rejection.
    a=maturity_state(r,src,m,b,f);e=entry_state(r,src,m,b,f)
    ap=1.0 if a is not None else 0.0;ep=1.0 if e is not None else 0.0
    aa=a if a is not None else [0.0]*SEQUENTIAL_STATE_FEATURE_COUNT
    ee=e if e is not None else [0.0]*SEQUENTIAL_STATE_FEATURE_COUNT
    delta=[ee[i]-aa[i] if ap and ep else 0.0 for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    return (list(r.get("features",[]))+route_cats(r,src,b,m,f)+aa+ee+delta+
            [ap,ep,1.0 if ap and ep else 0.0]+timing_state(r,src,m,b,f,eb))

def survival_xvec(r,sf,eb):
    a=r.get("survival_fresh_maturity_state",{}).get(sf)
    e=r.get("survival_fresh_entry_state",{}).get(sf)
    ap=1.0 if a is not None and len(a)==SEQUENTIAL_STATE_FEATURE_COUNT else 0.0
    ep=1.0 if e is not None and len(e)==SEQUENTIAL_STATE_FEATURE_COUNT else 0.0
    aa=[float(x) for x in a] if ap else [0.0]*SEQUENTIAL_STATE_FEATURE_COUNT
    ee=[float(x) for x in e] if ep else [0.0]*SEQUENTIAL_STATE_FEATURE_COUNT
    delta=[ee[i]-aa[i] if ap and ep else 0.0 for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    rb=r.get("survival_fresh_reaction_bar",{}).get(sf,-1)
    pb=r.get("survival_fresh_pullback_bar",{}).get(sf,-1)
    tb=r.get("survival_fresh_trigger_bar",{}).get(sf,-1)
    timing=[max(-1.0,min(6.0,float(eb)/10.0)),
            max(-1.0,min(6.0,float(rb)/10.0)) if rb is not None else -1.0,
            max(-1.0,min(6.0,float(pb)/10.0)) if pb is not None else -1.0,
            max(-1.0,min(6.0,float(tb)/10.0)) if tb is not None else -1.0]
    return (list(r.get("features",[]))+route_cats(r,"SURVIVAL","SURVIVAL","SI","00",sf)+
            aa+ee+delta+[ap,ep,1.0 if ap and ep else 0.0]+timing)

def telemetry_guard():
    legal={"EARLY":0,"LATE":0,"SURVIVAL":0};with_state={"EARLY":0,"LATE":0,"SURVIVAL":0}
    for r in rows:
      for b in BASES:
        for src in REGULAR_SOURCES:
          for m in (EARLY_MSTAGES if src=="EARLY" else LATE_MSTAGES):
            for f in (EARLY_FRACTIONS if src=="EARLY" else LATE_FRACTIONS):
              eb=entry_bar(r,src,m,b,f)
              if eb<0 or outcome(r,src,m,b,f) is None:continue
              legal[src]+=1
              if maturity_state(r,src,m,b,f) is not None and entry_state(r,src,m,b,f) is not None:
                  with_state[src]+=1
      for sf in SURVIVAL_FRESH_KEYS:
        try:eb=int(r.get("survival_fresh_entry_bar",{}).get(sf,-1))
        except:eb=-1
        y=r.get("survival_fresh",{}).get(sf);rr=r.get("survival_fresh_rr",{}).get(sf)
        if eb<0 or y is None or rr is None or float(rr)+1e-9<MIN_RR:continue
        legal["SURVIVAL"]+=1
        e=r.get("survival_fresh_entry_state",{}).get(sf)
        if e is not None and len(e)==SEQUENTIAL_STATE_FEATURE_COUNT:with_state["SURVIVAL"]+=1
    if sum(legal.values())==0:raise SystemExit("V74 no legal completed-bar actions")
    return {"legal_actions":legal,"complete_path_state":with_state,
            "missing_state_is_feature_not_veto":True,
            "future_trigger_decision_lock_state_used":False}

_OPTION_CACHE={}
def all_options(r,b):
    ck=(r["window"],r["setup"],b)
    if ck in _OPTION_CACHE:return _OPTION_CACHE[ck]
    z=[]
    for src in REGULAR_SOURCES:
      for m in (EARLY_MSTAGES if src=="EARLY" else LATE_MSTAGES):
        for f in (EARLY_FRACTIONS if src=="EARLY" else LATE_FRACTIONS):
          eb=entry_bar(r,src,m,b,f)
          if eb<0:continue
          y=outcome(r,src,m,b,f)
          if y is None:continue
          rid=("EARLY|"+b if src=="EARLY" else "LATE|M"+m+"_"+b)
          z.append({"rid":rid,"src":src,"m":m,"b":b,"f":f,"y":float(y),"bar":eb,
                    "bars":hold_bars(r,src,m,b,f),"x":xvec(r,src,m,b,f,eb)})
    _OPTION_CACHE[ck]=z
    return z

def make_samples(xs):
    out=[]
    for r in xs:
      for b in BASES:
        for o in all_options(r,b):
          out.append({"window":r["window"],"setup":r["setup"],"family":r["family"],"action":r["action"],
                      "source":o["src"],"base":b,"route":o["rid"],"bar":o["bar"],"bars":o["bars"],"x":o["x"],
                      "y":o["y"],"row":r})
      for sf in SURVIVAL_FRESH_KEYS:
        y=r.get("survival_fresh",{}).get(sf);rr=r.get("survival_fresh_rr",{}).get(sf)
        try:eb=int(r.get("survival_fresh_entry_bar",{}).get(sf,-1))
        except:eb=-1
        if y is None or rr is None or eb<0 or float(rr)+1e-9<MIN_RR:continue
        bars=max(1,int(r.get("survival_fresh_bars",{}).get(sf,r.get("bars",1)) or 1))
        out.append({"window":r["window"],"setup":r["setup"],"family":r["family"],"action":r["action"],
                    "source":"SURVIVAL","base":"SURVIVAL_"+sf,"route":"SURVIVAL|"+sf,"bar":eb,"bars":bars,
                    "x":survival_xvec(r,sf,eb),"y":float(y),"row":r})
    return out

def stable_idx(samples,k):
    """Training-only nonlinear stability screen.

    Harmonic/regime variables are often U-shaped or interval-optimal.  The old
    median-sign screen discarded those effects.  Rank a feature by payoff
    dispersion across quantile bins, but only when the dispersion is present in
    multiple training years.  No burned/test outcome participates.
    """
    if not samples:return []
    step=max(1,len(samples)//12000);ss=samples[::step];p=len(ss[0]["x"])
    yrs=sorted({s["window"] for s in ss});ranked=[]
    for j in range(p):
      vals=[float(s["x"][j]) for s in ss]
      cuts=sorted(set(qtile(vals,q) for q in (.15,.30,.50,.70,.85)))
      if len(cuts)<2:continue
      yearly=[]
      for w in yrs:
        q=[s for s in ss if s["window"]==w]
        bins=[[] for _ in range(len(cuts)+1)]
        for s in q:bins[bisect.bisect_right(cuts,float(s["x"][j]))].append(float(s["y"]))
        means=[statistics.mean(z) for z in bins if len(z)>=10]
        if len(means)<3:continue
        yearly.append(max(means)-min(means))
      need=max(2,(len(yrs)+1)//2)
      if len(yearly)<need:continue
      # Robust to one exceptional year: median signal plus weakest-half support.
      ys=sorted(yearly);lower=statistics.mean(ys[:max(1,len(ys)//2)])
      sc=.65*statistics.median(yearly)+.35*lower
      if sc>1e-8:ranked.append((sc,j))
    ranked.sort(reverse=True)
    return [j for _,j in ranked[:k]] or list(range(min(k,p)))

def grouped_events(samples):
    d=defaultdict(list)
    for s in samples:d[(s["window"],s["setup"],s["bar"])].append(s)
    return d

def _tree_fit(X,y,idx,max_depth=TREE_DEPTH,min_leaf=28,root_orders=None):
    # Exact same quantile split search as the reference implementation. Root
    # feature order is invariant across heads/boost rounds, so compute it once.
    def node(ids,depth,is_root=False):
      n=len(ids);sy=sum(y[i] for i in ids);sy2=sum(y[i]*y[i] for i in ids);mu=sy/n
      leaf={"leaf":mu,"n":n}
      if depth<=0 or n<2*min_leaf:return leaf
      base=sy2-sy*sy/n;best=None
      for j in idx:
        ordered=(root_orders[j] if is_root and root_orders is not None
                 else sorted(ids,key=lambda i:X[i][j]))
        vals=[X[i][j] for i in ordered]
        ps=[0.0];ps2=[0.0]
        for i in ordered:
          v=y[i];ps.append(ps[-1]+v);ps2.append(ps2[-1]+v*v)
        for t in sorted(set(qtile(vals,q) for q in (.20,.40,.60,.80))):
          p=bisect.bisect_right(vals,t);ln=p;rn=n-p
          if ln<min_leaf or rn<min_leaf:continue
          ls=ps[p];ls2=ps2[p];rs=sy-ls;rs2=sy2-ls2
          sse=(ls2-ls*ls/ln)+(rs2-rs*rs/rn);gain=base-sse
          if best is None or gain>best[0]:
            best=(gain,j,t,ordered[:p],ordered[p:])
      if best is None or best[0]<=1e-10:return leaf
      _,j,t,li,ri=best
      return {"j":j,"t":t,"n":n,"left":node(li,depth-1,False),"right":node(ri,depth-1,False)}
    return node(list(range(len(y))),max_depth,True)

def _tree_pred(t,x):
    n=t
    support=int(n.get("n",1))
    while "leaf" not in n:
      n=n["left"] if x[n["j"]]<=n["t"] else n["right"]
      support=min(support,int(n.get("n",1)))
    return float(n["leaf"]),support

def _boost_train(X,y,idx,rounds=TREE_ROUNDS,lr=.08,max_rows=6500,root_orders=None):
    if not y:return {"base":0.0,"trees":[],"lr":lr,"sigma":10.0}
    if len(y)>max_rows:
      step=max(1,math.ceil(len(y)/max_rows));X=X[::step];y=y[::step]
    base=sum(y)/len(y);pred=[base]*len(y);trees=[]
    for _ in range(rounds):
      res=[y[i]-pred[i] for i in range(len(y))]
      tr=_tree_fit(X,res,idx,root_orders=root_orders)
      trees.append(tr)
      for i,x in enumerate(X):
        v,_=_tree_pred(tr,x);pred[i]+=lr*v
    resid=[y[i]-pred[i] for i in range(len(y))]
    sig=statistics.stdev(resid) if len(resid)>1 else 10.0
    return {"base":base,"trees":trees,"lr":lr,"sigma":max(.05,sig)}

def _fit_view(X,ys,max_rows):
    if len(X)<=max_rows:return X,[list(y) for y in ys]
    step=max(1,math.ceil(len(X)/max_rows))
    return X[::step],[list(y)[::step] for y in ys]

def _root_orders(X,idx):
    ids=list(range(len(X)))
    return {j:sorted(ids,key=lambda i:X[i][j]) for j in idx}

def _boost_pred(m,x):
    v=float(m["base"]);support=10**9
    for tr in m["trees"]:
      z,n=_tree_pred(tr,x);v+=float(m["lr"])*z;support=min(support,n)
    return v,(0 if support==10**9 else support)

def _residual_cells(samples,pred_mean,pred_win):
    levels={}
    fns={
      "family":lambda s:s["family"],
      "family_action":lambda s:(s["family"],s["action"]),
      "family_base":lambda s:(s["family"],s["base"])}
    for name,fn in fns.items():
      d=defaultdict(list)
      for i,s in enumerate(samples):
        d[str(fn(s))].append((float(s["y"])-pred_mean[i],(1.0 if s["y"]>0 else 0.0)-pred_win[i]))
      levels[name]={}
      for k,v in d.items():
        n=len(v)
        if n<10:continue
        dm=sum(a for a,_ in v)/(n+24.0);dw=sum(b for _,b in v)/(n+24.0)
        levels[name][k]={"n":n,"dm":dm,"dw":dw}
    return levels

def training_continuation_targets(samples):
    """Training label only: best future matured payoff after the current event bar.
    This target may use later training outcomes, but it is never appended to x and
    is never computed from a burned/test row at inference time."""
    target=[0.0]*len(samples);by=defaultdict(list)
    for i,s in enumerate(samples):by[(s["window"],s["setup"])].append((s["bar"],i))
    for items in by.values():
      bars=defaultdict(list)
      for b,i in items:bars[b].append(i)
      ordered=sorted(bars)
      event_best={b:max(float(samples[i]["y"]) for i in bars[b]) for b in ordered}
      future=0.0
      for b in reversed(ordered):
        for i in bars[b]:target[i]=max(0.0,future)
        future=max(future,event_best[b])
    return target

def event_regret_targets(samples):
    """Training-only counterfactual labels aligned to the deployed decision:
    at each event/bar, learn regret to the best concurrently matured legal action
    and probability of being the event-best action. No target is ever appended to
    x or computed for burned rows during inference."""
    regret=[0.0]*len(samples);bestp=[0.0]*len(samples);by=defaultdict(list)
    for i,s in enumerate(samples):by[(s["window"],s["setup"],s["bar"])].append(i)
    for ids in by.values():
      top=max(float(samples[i]["y"]) for i in ids)
      ties=[i for i in ids if abs(float(samples[i]["y"])-top)<=1e-12]
      for i in ids:
        regret[i]=max(0.0,min(6.0,top-float(samples[i]["y"])))
        bestp[i]=1.0 if i in ties else 0.0
    return regret,bestp

def fit_value(samples,idx=None):
    idx=list(idx) if idx is not None else stable_idx(samples,TREE_KFEAT)
    Xall=[s["x"] for s in samples]
    ym=[float(s["y"]) for s in samples];yw=[1.0 if s["y"]>0 else 0.0 for s in samples]
    yc=training_continuation_targets(samples)
    yr,yb=event_regret_targets(samples)
    X,targets=_fit_view(Xall,[ym,yw,yc,yr,yb],6500)
    ymf,ywf,ycf,yrf,ybf=targets
    orders=_root_orders(X,idx)
    mm=_boost_train(X,ymf,idx,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    wm=_boost_train(X,ywf,idx,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    cm=_boost_train(X,ycf,idx,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    rm=_boost_train(X,yrf,idx,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    bm=_boost_train(X,ybf,idx,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    pm=[_boost_pred(mm,x)[0] for x in Xall];pw=[max(0.0,min(1.0,_boost_pred(wm,x)[0])) for x in Xall]
    return {"idx":idx,"mean":mm,"win":wm,"continuation":cm,"regret":rm,"best":bm,
            "residuals":_residual_cells(samples,pm,pw)}

def pred_value(md,s):
    mu,s1=_boost_pred(md["mean"],s["x"]);wi,s2=_boost_pred(md["win"],s["x"])
    co,s3=_boost_pred(md["continuation"],s["x"])
    rg,s4=_boost_pred(md["regret"],s["x"]);bp,s5=_boost_pred(md["best"],s["x"])
    wi=max(0.0,min(1.0,wi));co=max(0.0,co);rg=max(0.0,rg);bp=max(0.0,min(1.0,bp))
    adds_m=[];adds_w=[];supports=[s1 or 1,s2 or 1,s3 or 1,s4 or 1,s5 or 1]
    for lvl,k in (("family",str(s["family"])),
                  ("family_action",str((s["family"],s["action"]))),
                  ("family_base",str((s["family"],s["base"])))):
      z=md["residuals"].get(lvl,{}).get(k)
      if z:adds_m.append(z["dm"]);adds_w.append(z["dw"]);supports.append(z["n"])
    if adds_m:mu+=med(adds_m)
    if adds_w:wi=max(0.0,min(1.0,wi+med(adds_w)))
    sup=max(1,min(supports));lc=mu-Z*float(md["mean"]["sigma"])/math.sqrt(sup)
    stop_adv=mu-co
    # Regret is the primary route-ranking objective because the physical oracle
    # feasibility comes from choosing the right concurrently legal action inside
    # each event. Absolute payoff remains the capital-admission objective.
    route_score=(-1.35*rg)+(1.75*bp)+.35*mu+.45*wi+.20*lc
    admission_score=.55*stop_adv+.75*mu+1.30*wi+.40*lc-.65*rg+.80*bp
    return {"mean":mu,"win":wi,"lcb":lc,"continuation":co,"regret":rg,"best_probability":bp,
            "stop_advantage":stop_adv,"support":sup,"value_score":route_score,
            "admission_score":admission_score}

def fit_pair(samples,idx=None):
    idx=list(idx) if idx is not None else stable_idx(samples,PAIR_KFEAT);X=[];yw=[];yd=[]
    for ev in grouped_events(samples).values():
      if len(ev)<2:continue
      a=sorted(ev,key=lambda z:(z["base"],z["route"]));n=len(a)
      offs=sorted(set([1,max(1,n//4),max(1,n//2),max(1,(3*n)//4)]))
      for i in range(n):
        for off in offs:
          j=(i+off)%n
          if i>=j:continue
          aa,bb=a[i],a[j];delta=float(aa["y"])-float(bb["y"])
          if abs(delta)<1e-12:continue
          d=[aa["x"][q]-bb["x"][q] for q in idx]
          X.append(d);yw.append(1.0 if delta>0 else 0.0);yd.append(max(-4.0,min(4.0,delta)))
          X.append([-z for z in d]);yw.append(0.0 if delta>0 else 1.0);yd.append(max(-4.0,min(4.0,-delta)))
    if len(X)<200:return {"valid":False,"idx":idx,"n":len(X)}
    if len(X)>10000:
      step=max(1,math.ceil(len(X)/10000));X=X[::step];yw=yw[::step];yd=yd[::step]
    use=list(range(len(idx)))
    Xfit,targets=_fit_view(X,[yw,yd],7000);ywf,ydf=targets
    orders=_root_orders(Xfit,use)
    return {"valid":True,"idx":idx,"n":len(X),
            "win":_boost_train(Xfit,ywf,use,rounds=PAIR_ROUNDS,lr=.08,max_rows=10**9,root_orders=orders),
            "delta":_boost_train(Xfit,ydf,use,rounds=PAIR_ROUNDS,lr=.08,max_rows=10**9,root_orders=orders)}

def pair_pref(pm,a,b):
    if not pm.get("valid"):return 0.0
    d=[a["x"][q]-b["x"][q] for q in pm["idx"]];rd=[-z for z in d]
    fw,_=_boost_pred(pm["win"],d);bw,_=_boost_pred(pm["win"],rd)
    fd,_=_boost_pred(pm["delta"],d);bd,_=_boost_pred(pm["delta"],rd)
    p=.5*(fw+(1.0-bw));dr=.5*(fd-bd)
    return 2.0*(max(0.0,min(1.0,p))-.5)+.40*math.tanh(dr/1.5)

def event_decisions(samples,vm,pm):
    out=[]
    for ev in grouped_events(samples).values():
      if not ev:continue
      direct=[]
      for s in ev:
        p=pred_value(vm,s);direct.append((p["value_score"],p,s))
      direct.sort(key=lambda z:(z[0],z[1]["lcb"],z[1]["win"],z[2]["route"]),reverse=True)
      cand=direct[:min(TOP_PAIR,len(direct))]
      pair=[0.0]*len(cand)
      for i in range(len(cand)):
        for j in range(i+1,len(cand)):
          z=pair_pref(pm,cand[i][2],cand[j][2]);pair[i]+=z;pair[j]-=z
      scored=[]
      for i,(route_score,p,s) in enumerate(cand):
        adv=pair[i]/max(1,len(cand)-1)
        route_rank=route_score+.35*adv
        admission=p["admission_score"]+.20*adv
        scored.append((route_rank,admission,adv,p,s))
      scored.sort(key=lambda z:(z[0],z[3]["lcb"],z[3]["win"],z[4]["route"]),reverse=True)
      route_rank,admission,adv,p,s=scored[0]
      second=scored[1][0] if len(scored)>1 else route_rank
      q=dict(s);q["pair_advantage"]=adv;q["decision_score"]=admission;q["decision_margin"]=route_rank-second
      out.append({"score":admission,"route_rank":route_rank,
                  "pred":dict(p,pair_advantage=adv),"s":q})
    return out

def simulate(decisions,th,window=None):
    d=defaultdict(list)
    for e in decisions:
      if window is not None and e["s"]["window"]!=window:continue
      d[(e["s"]["window"],e["s"]["setup"])].append(e)
    sel=[]
    for ev in d.values():
      ev.sort(key=lambda e:(e["s"]["bar"],-e["score"],e["s"]["route"]))
      for e in ev:
        if e["score"]+1e-12>=th:
          sel.append(e);break
    return sel

def metric_selected(sel):
    rr=[]
    for e in sel:
      s=e["s"];q=dict(s["row"]);q["r"]=s["y"];q["bars"]=s["bars"];q["sequential_key"]=s["route"];rr.append(q)
    return metrics(rr),rr

def gate_margin(m):
    if m["n"]<=0:return -999.0
    return min(m["n"]/MIN_N,m["mean_r"]/MIN_MEAN,m["pf_r"]/MIN_PF,
               m["win_rate"]/MIN_WR,m["average_rr"]/MIN_RR,1.0+m["lcb_r"]/.25)

def gate_calibrated_threshold(decisions,years,target=TRAIN_COVERAGE):
    # Training-only constrained ERM: choose the admission threshold that maximizes
    # the weakest training-year V74 gate margin while retaining a 10% N buffer.
    by=defaultdict(lambda:defaultdict(lambda:-math.inf))
    scores=[]
    for e in decisions:
      w=e["s"]["window"];setup=e["s"]["setup"];z=float(e["score"])
      by[w][setup]=max(by[w][setup],z);scores.append(z)
    supply={w:len(by[w]) for w in years}
    limits={}
    for w in years:
      vals=sorted(by[w].values(),reverse=True)
      k=min(target,len(vals));limits[w]=vals[k-1] if vals else -math.inf
    upper=min(limits.values()) if limits else -math.inf
    admissible=[z for z in scores if z<=upper+1e-12]
    qs=[i/40.0 for i in range(0,41)]
    candidates=sorted(set([upper]+[qtile(admissible,q) for q in qs if admissible]),reverse=True)
    best=None
    for th in candidates:
      tm={};ok=True
      for w in years:
        m,_=metric_selected(simulate(decisions,th,w));tm[w]=m
        if m["n"]<target:ok=False;break
      if not ok:continue
      worst=min(gate_margin(m) for m in tm.values())
      medm=med([gate_margin(m) for m in tm.values()],-999.0)
      cand=(worst,medm,th,tm)
      if best is None or cand[:3]>best[:3]:best=cand
    if best is None:
      th=upper;tm={w:metric_selected(simulate(decisions,th,w))[0] for w in years}
      best=(min(gate_margin(m) for m in tm.values()),med([gate_margin(m) for m in tm.values()]),th,tm)
    return best[2],limits,supply,best[3],best[0]

def mechanism_decisions(samples,heads):
    """Route arbitration is mechanism-native; only calibrated action values meet
    at the event-level capital decision. This prevents EARLY/LATE/SURVIVAL from
    contaminating each other's feature selection, continuation target and pair model."""
    out=[]
    for src in SOURCES:
      md=heads.get(src)
      if not md:continue
      ss=[s for s in samples if s.get("source")==src]
      if not ss:continue
      dd=event_decisions(ss,md["value_model"],md["pairwise_ranker"])
      for e in dd:
        e["mechanism"]=src
        # Expected-R and P(win) are already on common physical units. Apply only
        # a training-derived reliability penalty for weak-support mechanism heads.
        rel=float(md.get("reliability",1.0))
        e["score"]=rel*float(e["score"])+(1.0-rel)*float(e["pred"]["lcb"])
        e["s"]["mechanism"]=src
      out.extend(dd)
    return out

def fit_policy(train_rows):
    samples=make_samples(train_rows)
    if len(samples)<1000:raise SystemExit("V74 insufficient legal action samples")
    heads={}
    mechanism_training={}
    for src in SOURCES:
      ss=[s for s in samples if s.get("source")==src]
      if len(ss)<250:continue
      ranked=stable_idx(ss,max(TREE_KFEAT,PAIR_KFEAT))
      vm=fit_value(ss,ranked[:TREE_KFEAT]);pm=fit_pair(ss,ranked[:PAIR_KFEAT])
      if not pm.get("valid"):continue
      # Reliability is a causal training-only shrinkage term. It cannot improve a
      # weak head by invention; it only shrinks low-support heads toward their LCB.
      years=sorted({s["window"] for s in ss})
      counts=[sum(1 for s in ss if s["window"]==w) for w in years]
      reliability=min(1.0,min(counts)/750.0) if counts else 0.0
      heads[src]={"value_model":vm,"pairwise_ranker":pm,"reliability":reliability,
                  "n":len(ss),"year_counts":dict((w,sum(1 for s in ss if s["window"]==w)) for w in years)}
      mechanism_training[src]={"n":len(ss),"reliability":reliability,
                               "selected_features":len(vm.get("idx",[])),
                               "pairwise_n":pm.get("n",0)}
    if not heads:raise SystemExit("V74 no valid mechanism-native heads")
    dec=mechanism_decisions(samples,heads)
    yrs=sorted({r["window"] for r in train_rows})
    th,limits,supply,tm,worst=gate_calibrated_threshold(dec,yrs,TRAIN_COVERAGE)
    training_gate=all(gate(m) for m in tm.values())
    return {"mechanism_heads":heads,"mechanism_training":mechanism_training,"threshold":th,
            "training_coverage_limits":limits,"training_supply":supply,
            "training_metrics":tm,"training_worst_gate_margin":worst,
            "training_gate":training_gate,"coverage_target":TRAIN_COVERAGE},samples

def apply_policy(policy,test_rows):
    samples=make_samples(test_rows)
    dec=mechanism_decisions(samples,policy["mechanism_heads"])
    sel=simulate(dec,policy["threshold"])
    return sel,samples,dec

checks=telemetry_guard()
summary={"version":"HarmonyBot V74 One-Shot Family-Native Causal Action Selector",
 "architecture":"STRICT_WALK_FORWARD_NONLINEAR_STABLE_EVENT_REGRET_POLICY",
 "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,
         "min_win_rate":MIN_WR,"min_average_rr":MIN_RR,"lcb95_gt":0.0},
 "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
 "policy":{"actions":"EARLY_RAW_F00_OR_LATE_PREENTRY_F30_OR_STRONG_IMPULSE_FRESH",
           "harmonic_completion":"DIRECTION_TIME_D_EVENT_IDENTITY__MULTI_GEOMETRY_IS_CONFLUENCE_NOT_SUPPLY",
           "reaction_state":"CAUSAL_FEATURE_NOT_HARD_FILTER","physical_route_contract":"EVENT_NATIVE_EARLY_RAW_F00_PLUS_LATE_PREENTRY_F30_PLUS_STRONG_IMPULSE_PULLBACK_RECLAIM_RAW_230R","v75_management_variants_excluded":True,"early_post_entry_m_stage_excluded":True,
           "route_choice":"STRICT_WALK_FORWARD_NONLINEAR_STABLE_EVENT_REGRET_PLUS_BEST_ACTION_PROBABILITY","optimal_stopping":"MECHANISM_NATIVE_TRAINING_ONLY_CONTINUATION_HEAD__EVENT_LEVEL_STOP_VS_DEFER",
           "admission":"PAST_ONLY_WORST_YEAR_GATE_CALIBRATED_STOP_ADVANTAGE_THRESHOLD",
           "training_coverage_target_per_year":TRAIN_COVERAGE,
           "family_hierarchy":"WITHIN_MECHANISM_GLOBAL_TO_FAMILY_TO_FAMILY_ACTION_TO_FAMILY_BASE_SHRINKAGE",
           "no_trigger_posttrigger_lock_future_state":True,
           "canonical_family_blanket_blacklist":False,"grid":False,
           "v75_profit_capture_used":False},
 "folds":{},"validation_used":False,"fresh_used":False,"telemetry_contract_checks":checks}
models={"architecture":summary["architecture"],"folds":{}}
t0=time.perf_counter();allpass=True

for test in BURNED:
  # Strict deployable OOF: a burned year may only learn from years that ended
  # before it.  Never train a 2021 decision on 2022/2023, etc.
  ft=time.perf_counter();test_year=int(test[1:])
  tw=[w for w in ALL if int(w[1:])<test_year]
  tr=[r for r in rows if r["window"] in tw];te=[r for r in rows if r["window"]==test]
  policy,_=fit_policy(tr)
  sel,test_samples,dec=apply_policy(policy,te);m,mr=metric_selected(sel)
  routes=Counter(r.get("sequential_key","NONE") for r in mr)
  fams=Counter(r["family"] for r in mr);acts=Counter(r["action"] for r in mr)
  srcs=Counter(x.split("|",1)[0] for x in routes.elements())
  ps=gate(m);allpass=allpass and ps
  summary["folds"][test]={**m,"pass":ps,"training_windows":tw,
    "entry_threshold":policy["threshold"],"training_coverage_target":TRAIN_COVERAGE,"training_gate":policy.get("training_gate"),"training_worst_gate_margin":policy.get("training_worst_gate_margin"),
    "training_supply":policy["training_supply"],"training_year_metrics":policy["training_metrics"],
    "test_legal_actions":len(test_samples),"test_decision_events":len(dec),
    "selected_route_counts":dict(routes),"selected_family_counts":dict(fams),
    "selected_action_counts":dict(acts),"selected_source_counts":dict(srcs),
    "runtime_seconds":round(time.perf_counter()-ft,3)}
  models["folds"][test]=policy
  print("[V74-ONE-SHOT]",test,json.dumps({k:summary["folds"][test][k]
        for k in ("n","mean_r","pf_r","win_rate","average_rr","lcb_r","pass")}),flush=True)

alpha=bool(allpass)
champ="STRICT_WALK_FORWARD_NONLINEAR_STABLE_EVENT_REGRET_POLICY" if alpha else None
summary["evaluator_runtime_seconds"]=round(time.perf_counter()-t0,3)
summary["alpha_gate"]=alpha;summary["alpha_champion"]=champ
summary["execution_semantics_ready"]=False;summary["v74_gate"]=False;summary["champion"]=None
summary["promotion_blocker"]="ONE_SHOT_RUNTIME_POLICY_NOT_FROZEN" if alpha else "ALPHA_OOF_GATE_FAIL"
summary["positive_asset"]="ONE_SHOT_CAUSAL_ALPHA_OOF" if alpha else "NO_MODEL_EARNED_VERSION_PROMOTION"
(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2))
(out/"V74_MODELS.json").write_text(json.dumps(models,indent=2))
(out/"alpha_pass.txt").write_text("true" if alpha else "false")
(out/"alpha_champion.txt").write_text(champ or "NONE")
(out/"pass.txt").write_text("false");(out/"champion.txt").write_text("NONE")
print(json.dumps({"alpha_gate":alpha,"alpha_champion":champ,"v74_gate":False,
                  "promotion_blocker":summary["promotion_blocker"],
                  "evaluator_runtime_seconds":summary["evaluator_runtime_seconds"]},indent=2))
