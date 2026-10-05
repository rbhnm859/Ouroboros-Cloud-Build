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
import bisect,json,math,os,pathlib,statistics,sys,time,multiprocessing as mp
from collections import defaultdict,Counter
from v74_model_lib import load_rows,metrics,SEQUENTIAL_STATE_FEATURE_COUNT,SURVIVAL_MORPH_FEATURE_COUNT,FAMILIES,SURVIVAL_FRESH_KEYS
from v74_model_lib import event_identity

root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
RESEARCH=[f"Y{y}" for y in range(2016,2021)]
BURNED=["Y2021","Y2022","Y2023"];ALL=RESEARCH+BURNED
MIN_N=250;TRAIN_COVERAGE=275;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_AVG_RR=2.30;LEGAL_MIN_RR=2.0;Z=1.645
REGULAR_SOURCES=("EARLY","LATE");SOURCES=("EARLY","LATE","SURVIVAL");EARLY_QUALIFICATION_FRACTION="00";EARLY_FRACTIONS=(EARLY_QUALIFICATION_FRACTION,);LATE_FRACTIONS=("20","30");ALL_FRACTIONS=(EARLY_QUALIFICATION_FRACTION,)+LATE_FRACTIONS;MSTAGES=("05","10","15");EARLY_MSTAGES=MSTAGES;LATE_MSTAGES=MSTAGES
BASES=[f"R{r}_{h}_RR{rr}" for r in ("025","050") for h in ("H","D") for rr in ("35","40")]
TREE_KFEAT=30;PAIR_KFEAT=26;TREE_ROUNDS=10;PAIR_ROUNDS=8;TREE_DEPTH=3;TOP_PAIR=6
rows=load_rows(root,ALL)
if not rows:raise SystemExit("no V74 rows")

def gate(m):
    return bool(m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and
                m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_AVG_RR and m["lcb_r"]>0)
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
    if not all(math.isfinite(x) for x in (v,rr)) or rr+1e-9<LEGAL_MIN_RR:return None
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
            [ap,ep,1.0 if ap and ep else 0.0]+timing_state(r,src,m,b,f,eb)+
            [0.0]*SURVIVAL_MORPH_FEATURE_COUNT)

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
    q=r.get("survival_fresh_morphology",{}).get(sf)
    morph=[float(x) for x in q] if q is not None and len(q)==SURVIVAL_MORPH_FEATURE_COUNT else [0.0]*SURVIVAL_MORPH_FEATURE_COUNT
    return (list(r.get("features",[]))+route_cats(r,"SURVIVAL","SURVIVAL","FIB","00",sf)+
            aa+ee+delta+[ap,ep,1.0 if ap and ep else 0.0]+timing+morph)

def telemetry_guard():
    legal={"EARLY":0,"LATE":0,"SURVIVAL":0};with_state={"EARLY":0,"LATE":0,"SURVIVAL":0}
    survival_morphology=0
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
        if eb<0 or y is None or rr is None or float(rr)+1e-9<LEGAL_MIN_RR:continue
        legal["SURVIVAL"]+=1
        e=r.get("survival_fresh_entry_state",{}).get(sf)
        if e is not None and len(e)==SEQUENTIAL_STATE_FEATURE_COUNT:with_state["SURVIVAL"]+=1
        q=r.get("survival_fresh_morphology",{}).get(sf)
        if q is not None and len(q)==SURVIVAL_MORPH_FEATURE_COUNT:survival_morphology+=1
    if sum(legal.values())==0:raise SystemExit("V74 no legal completed-bar actions")
    return {"legal_actions":legal,"complete_path_state":with_state,
            "survival_morphology_complete":survival_morphology,
            "survival_morphology_missing":max(0,legal["SURVIVAL"]-survival_morphology),
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
        if y is None or rr is None or eb<0 or float(rr)+1e-9<LEGAL_MIN_RR:continue
        bars=max(1,int(r.get("survival_fresh_bars",{}).get(sf,r.get("bars",1)) or 1))
        out.append({"window":r["window"],"setup":r["setup"],"family":r["family"],"action":r["action"],
                    "source":"SURVIVAL","base":"SURVIVAL_"+sf,"route":"SURVIVAL|"+sf,"bar":eb,"bars":bars,
                    "x":survival_xvec(r,sf,eb),"y":float(y),"row":r})
    return out

def stable_idx(samples,k):
    """Training-only nonlinear stability screen; exact semantics, fewer scans.

    Pre-partitioning immutable sampled rows by year removes the former
    feature×year full-list rescans. Quantiles, binning, means, score formula and
    tie ordering are unchanged, so the selected feature set is identical.
    """
    if not samples:return []
    step=max(1,len(samples)//12000);ss=samples[::step];p=len(ss[0]["x"])
    yrs=sorted({s["window"] for s in ss});ranked=[]
    by_year={w:[s for s in ss if s["window"]==w] for w in yrs}
    for j in range(p):
      vals=[float(s["x"][j]) for s in ss]
      cuts=sorted(set(qtile(vals,q) for q in (.15,.30,.50,.70,.85)))
      if len(cuts)<2:continue
      yearly=[]
      for w in yrs:
        bins=[[] for _ in range(len(cuts)+1)]
        for s in by_year[w]:
          bins[bisect.bisect_right(cuts,float(s["x"][j]))].append(float(s["y"]))
        means=[statistics.mean(z) for z in bins if len(z)>=10]
        if len(means)<3:continue
        yearly.append(max(means)-min(means))
      need=max(2,(len(yrs)+1)//2)
      if len(yearly)<need:continue
      ys=sorted(yearly);lower=statistics.mean(ys[:max(1,len(ys)//2)])
      sc=.65*statistics.median(yearly)+.35*lower
      if sc>1e-8:ranked.append((sc,j))
    ranked.sort(reverse=True)
    return [j for _,j in ranked[:k]] or list(range(min(k,p)))

def grouped_events(samples):
    d=defaultdict(list)
    for s in samples:d[(s["window"],event_identity(s["setup"]),s["bar"])].append(s)
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
    for i,s in enumerate(samples):by[(s["window"],event_identity(s["setup"]))].append((s["bar"],i))
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
    for i,s in enumerate(samples):by[(s["window"],event_identity(s["setup"]),s["bar"])].append(i)
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
      d[(e["s"]["window"],event_identity(e["s"]["setup"]))].append(e)
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
               m["win_rate"]/MIN_WR,m["average_rr"]/MIN_AVG_RR,1.0+m["lcb_r"]/.25)

def gate_calibrated_threshold(decisions,years,target=TRAIN_COVERAGE):
    # Training-only constrained ERM: choose the admission threshold that maximizes
    # the weakest training-year V74 gate margin while retaining a 10% N buffer.
    by=defaultdict(lambda:defaultdict(lambda:-math.inf))
    scores=[]
    for e in decisions:
      w=e["s"]["window"];setup=event_identity(e["s"]["setup"]);z=float(e["score"])
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
    """Route arbitration is mechanism-native; exact source partition cached once."""
    out=[]
    by_source=defaultdict(list)
    for s in samples:by_source[s.get("source")].append(s)
    for src in SOURCES:
      md=heads.get(src)
      if not md:continue
      ss=by_source.get(src,[])
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

def admission_route_representatives(decisions):
    """One causally preferred route per event/bar; admission is intentionally separate."""
    by=defaultdict(list)
    for e in decisions:
      s=e["s"];by[(s["window"],event_identity(s["setup"]),int(s["bar"]))].append(e)
    out=[]
    for vv in by.values():
      # Preserve the exact cross-mechanism causal route arbitration that the
      # two-axis oracle already proved sufficient when admission is corrected.
      # The new admission head acts only after this route is fixed.
      out.append(max(vv,key=lambda z:(float(z.get("score",-999.0)),
                                      float(z.get("route_rank",-999.0)),
                                      float(z["pred"].get("lcb",-999.0)),
                                      float(z["pred"].get("win",0.0)),z["s"]["route"])))
    return out

def _admission_training_samples(route_decisions,years):
    yy=set(years);out=[]
    for e in admission_route_representatives(route_decisions):
      s=e["s"]
      if s["window"] not in yy:continue
      out.append({"window":s["window"],"setup":s["setup"],"family":s["family"],
                  "action":s["action"],"source":s["source"],"base":s["base"],
                  "route":s["route"],"bar":s["bar"],"bars":s["bars"],
                  "x":list(s["x"]),"y":float(s["y"]),"row":s["row"]})
    return out

def _optimal_admission_targets(ss):
    """Training-only optimal-stopping labels.
    Future outcomes define the supervision target, never an inference feature.
    stop=1 only when ENTER now is positive and no later matured causal route
    offers a strictly better realized payoff for the same event.
    """
    n=len(ss);win=[0.0]*n;stop=[0.0]*n;adv=[0.0]*n;future_win=[0.0]*n
    by=defaultdict(list)
    for i,s in enumerate(ss):by[(s["window"],event_identity(s["setup"]))].append(i)
    for ids in by.values():
      ids=sorted(ids,key=lambda i:(int(ss[i]["bar"]),ss[i]["route"]))
      future_best=0.0
      for i in reversed(ids):
        y=float(ss[i]["y"])
        win[i]=1.0 if y>0 else 0.0
        future_win[i]=1.0 if future_best>0 else 0.0
        adv[i]=max(-4.0,min(4.0,y-max(0.0,future_best)))
        stop[i]=1.0 if y>0 and y+1e-12>=future_best else 0.0
        future_best=max(future_best,y)
    return win,stop,adv,future_win

def fit_admission_model(route_decisions,fit_years,source=None):
    """Mechanism-native causal optimal-stopping admission head.
    Route arbitration is frozen first. Each source learns ENTER-vs-DEFER on its
    own causal state manifold so SURVIVAL-only Fibonacci rejection morphology is
    not diluted by zero-padded EARLY/LATE rows. Training labels may use later
    outcomes only inside training years; runtime inference uses current x only.
    """
    ss=_admission_training_samples(route_decisions,fit_years)
    if source is not None:ss=[s for s in ss if s.get("source")==source]
    if len(ss)<350:return None
    idx=stable_idx(ss,TREE_KFEAT)
    X=[s["x"] for s in ss]
    yw,ys,ya,yf=_optimal_admission_targets(ss)
    Xf,targets=_fit_view(X,[yw,ys,ya,yf],6500);ywf,ysf,yaf,yff=targets
    orders=_root_orders(Xf,idx)
    wm=_boost_train(Xf,ywf,idx,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    sm=_boost_train(Xf,ysf,idx,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    am=_boost_train(Xf,yaf,idx,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    fm=_boost_train(Xf,yff,idx,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    return {"type":"MECHANISM_NATIVE_CAUSAL_OPTIMAL_STOPPING","source":source or "GLOBAL",
            "fit_years":list(fit_years),"idx":idx,"win":wm,"stop":sm,
            "advantage":am,"future_win":fm,"n":len(ss)}

def fit_admission_bundle(route_decisions,fit_years):
    glob=fit_admission_model(route_decisions,fit_years,None)
    if glob is None:raise SystemExit("V74 insufficient global admission samples")
    by={}
    for src in SOURCES:
      md=fit_admission_model(route_decisions,fit_years,src)
      if md is not None:by[src]=md
    return {"type":"MECHANISM_NATIVE_CAUSAL_OPTIMAL_STOPPING_BUNDLE",
            "fit_years":list(fit_years),"global":glob,"by_source":by}

def pred_admission(bundle,e):
    s=e["s"];model=bundle.get("by_source",{}).get(s.get("source"),bundle["global"])
    wi,s1=_boost_pred(model["win"],s["x"]);st,s2=_boost_pred(model["stop"],s["x"])
    ad,s3=_boost_pred(model["advantage"],s["x"]);fw,s4=_boost_pred(model["future_win"],s["x"])
    wi=max(0.0,min(1.0,wi));st=max(0.0,min(1.0,st));fw=max(0.0,min(1.0,fw))
    sup=max(1,min(s1 or 1,s2 or 1,s3 or 1,s4 or 1))
    win_lcb=wi-Z*max(.05,float(model["win"]["sigma"]))/math.sqrt(sup)
    stop_lcb=st-Z*max(.05,float(model["stop"]["sigma"]))/math.sqrt(sup)
    adv_lcb=ad-Z*max(.05,float(model["advantage"]["sigma"]))/math.sqrt(sup)
    return {"win":wi,"win_lcb":win_lcb,"stop":st,"stop_lcb":stop_lcb,
            "advantage":ad,"advantage_lcb":adv_lcb,"future_win":fw,"support":sup,
            "head_source":model.get("source","GLOBAL")}

def score_admission_decisions(route_decisions,bundle):
    out=[]
    for e in admission_route_representatives(route_decisions):
      z=pred_admission(bundle,e);q=dict(e);q["pred"]=dict(e["pred"],admission=z)
      # Conjunctive purity/optimal-stopping lower bound; no score-weight search.
      q["score"]=min(float(z["win_lcb"]),float(z["stop_lcb"]))
      q["admission_advantage_lcb"]=float(z["advantage_lcb"])
      q["defer_probability"]=float(z["future_win"])
      out.append(q)
    return out

def fit_policy(train_rows):
    samples=make_samples(train_rows)
    if len(samples)<1000:raise SystemExit("V74 insufficient legal action samples")
    heads={}
    mechanism_training={}
    by_source=defaultdict(list)
    for s in samples:by_source[s.get("source")].append(s)
    for src in SOURCES:
      ss=by_source.get(src,[])
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
    route_dec=mechanism_decisions(samples,heads)
    yrs=sorted({r["window"] for r in train_rows})
    # Hold the most recent training year out of the admission model itself. It
    # remains available to threshold calibration as a temporal transfer check.
    adm_fit_years=yrs[:-1] if len(yrs)>=3 else yrs
    admission_model=fit_admission_bundle(route_dec,adm_fit_years)
    dec=score_admission_decisions(route_dec,admission_model)
    th,limits,supply,tm,worst=gate_calibrated_threshold(dec,yrs,TRAIN_COVERAGE)
    training_gate=all(gate(m) for m in tm.values())
    reps=admission_route_representatives(route_dec)
    training_oracle_admission={}
    for w in yrs:
      training_oracle_admission[w]=_oracle_top250([e["s"] for e in reps if e["s"]["window"]==w])
    return {"mechanism_heads":heads,"mechanism_training":mechanism_training,
            "admission_model":admission_model,"admission_fit_years":adm_fit_years,
            "admission_calibration_year":yrs[-1] if yrs else None,"threshold":th,
            "training_coverage_limits":limits,"training_supply":supply,
            "training_metrics":tm,"training_worst_gate_margin":worst,
            "training_oracle_admission":training_oracle_admission,
            "training_gate":training_gate,"coverage_target":TRAIN_COVERAGE},samples

def apply_policy(policy,test_rows):
    samples=make_samples(test_rows)
    route_dec=mechanism_decisions(samples,policy["mechanism_heads"])
    dec=score_admission_decisions(route_dec,policy["admission_model"])
    sel=simulate(dec,policy["threshold"])
    return sel,samples,dec

def _diag_metrics(samples):
    rr=[]
    for s in samples:
      q=dict(s["row"]);q["r"]=float(s["y"]);q["bars"]=max(1,int(s.get("bars",1) or 1));rr.append(q)
    return metrics(rr)

def _oracle_top250(samples):
    by=defaultdict(list)
    for s in samples:by[(s["window"],event_identity(s["setup"]))].append(s)
    best=[]
    for ev in by.values():
      if ev:best.append(max(ev,key=lambda s:(float(s["y"]),s["route"],-int(s["bar"]))))
    best.sort(key=lambda s:(float(s["y"]),s["route"]),reverse=True)
    top=best[:MIN_N];m=_diag_metrics(top)
    return {"metrics":m,"pass":gate(m),"available_events":len(best)}

def two_axis_oracle_diagnostic(test_samples,dec,sel):
    """Post-hoc burned diagnostic only; outcomes never feed training/inference.
    Axis A holds causal admission time/event fixed and replaces only the route
    with the best concurrently matured selector-visible legal route.
    Axis B holds causal route arbitration fixed at each event/bar and lets an
    oracle choose which event/bar to admit. Fully-oracle is a ceiling over the
    same selector-visible action surface (FAILURE continuation is diagnosed by
    the separate physical oracle until it is added to the causal selector).
    """
    by_eb=defaultdict(list)
    for s in test_samples:
      by_eb[(s["window"],event_identity(s["setup"]),int(s["bar"]))].append(s)

    route_oracle=[]
    for e in sel:
      s=e["s"];k=(s["window"],event_identity(s["setup"]),int(s["bar"]))
      cand=by_eb.get(k,[])
      if cand:route_oracle.append(max(cand,key=lambda z:(float(z["y"]),z["route"])))

    dec_eb=defaultdict(list)
    for e in dec:
      s=e["s"];dec_eb[(s["window"],event_identity(s["setup"]),int(s["bar"]))].append(e)
    causal_reps=[]
    for vv in dec_eb.values():
      # This is the route the deployed scorer would prefer if capital were
      # admitted at this matured event/bar; no outcome participates here.
      e=max(vv,key=lambda z:(float(z["score"]),float(z.get("route_rank",-999.0)),z["s"]["route"]))
      causal_reps.append(e["s"])

    causal=_diag_metrics([e["s"] for e in sel])
    a=_diag_metrics(route_oracle)
    b=_oracle_top250(causal_reps)
    full=_oracle_top250(test_samples)
    return {
      "type":"DIAGNOSTIC_FUTURE_ORACLE_ONLY__NEVER_TRAINED",
      "fully_causal":{"metrics":causal,"pass":gate(causal)},
      "oracle_route_plus_causal_admission":{"metrics":a,"pass":gate(a),
        "definition":"SAME_CAUSAL_EVENT_AND_ADMISSION_BAR__BEST_CONCURRENT_LEGAL_ROUTE"},
      "causal_route_plus_oracle_admission":b,
      "fully_oracle_selector_visible":full,
      "interpretation":"ROUTE_ONLY" if gate(a) and not b["pass"] else
                       "ADMISSION_ONLY" if b["pass"] and not gate(a) else
                       "BOTH_AXES" if not gate(a) and not b["pass"] else
                       "BOTH_AXES_INDIVIDUALLY_SUFFICIENT"
    }

checks=telemetry_guard()
summary={"version":"HarmonyBot V74 One-Shot Family-Native Causal Action Selector",
 "architecture":"STRICT_WALK_FORWARD_CAUSAL_ROUTE_PLUS_OPTIMAL_STOPPING_ADMISSION",
 "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,
         "min_win_rate":MIN_WR,"min_average_rr":MIN_AVG_RR,"lcb95_gt":0.0},
 "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
 "policy":{"actions":"EARLY_OR_LATE_COMPLETED_BAR_ENTRY_ACTION__RAW_F00_EARLY__PREENTRY_CONFIRMATION_F20_F30_LATE",
           "harmonic_completion":"DIRECTION_TIME_D_EVENT_IDENTITY__MULTI_GEOMETRY_IS_CONFLUENCE_NOT_SUPPLY",
           "reaction_state":"CAUSAL_FEATURE_NOT_HARD_FILTER","physical_route_contract":"EVENT_NATIVE_CANONICAL_EVENT_FULL_COMPLETED_BAR_ENTRY_TIMING__EARLY_F00_M05_M10_M15__LATE_PREENTRY_F20_F30__SURVIVAL_FRESH__NETRR_GE230","v75_management_variants_excluded":True,"all_entry_maturity_stages_completed_bar_only":True,
           "route_choice":"STRICT_WALK_FORWARD_NONLINEAR_STABLE_EVENT_REGRET_PLUS_BEST_ACTION_PROBABILITY","optimal_stopping":"MECHANISM_NATIVE_TRAINING_ONLY_CONTINUATION_HEAD__EVENT_LEVEL_STOP_VS_DEFER",
           "admission":"DECISION_LEVEL_CAUSAL_OPTIMAL_STOPPING__WIN_LCB_AND_STOP_LCB__LAST_TRAIN_YEAR_TEMPORAL_CALIBRATION",
           "training_coverage_target_per_year":TRAIN_COVERAGE,
           "family_hierarchy":"WITHIN_MECHANISM_GLOBAL_TO_FAMILY_TO_FAMILY_ACTION_TO_FAMILY_BASE_SHRINKAGE",
           "no_trigger_posttrigger_lock_future_state":True,
           "canonical_family_blanket_blacklist":False,"grid":False,
           "v75_profit_capture_used":False},
 "folds":{},"validation_used":False,"fresh_used":False,"telemetry_contract_checks":checks}
models={"architecture":summary["architecture"],"folds":{}}

def evaluate_burned_fold(test):
    ft=time.perf_counter();test_year=int(test[1:])
    tw=[w for w in ALL if int(w[1:])<test_year]
    tr=[r for r in rows if r["window"] in tw];te=[r for r in rows if r["window"]==test]
    policy,_=fit_policy(tr)
    sel,test_samples,dec=apply_policy(policy,te);m,mr=metric_selected(sel)
    two_axis=two_axis_oracle_diagnostic(test_samples,dec,sel)
    routes=Counter(r.get("sequential_key","NONE") for r in mr)
    fams=Counter(r["family"] for r in mr);acts=Counter(r["action"] for r in mr)
    srcs=Counter(x.split("|",1)[0] for x in routes.elements())
    ps=gate(m)
    fold={**m,"pass":ps,"training_windows":tw,
      "entry_threshold":policy["threshold"],"training_coverage_target":TRAIN_COVERAGE,
      "training_gate":policy.get("training_gate"),"training_worst_gate_margin":policy.get("training_worst_gate_margin"),
      "training_supply":policy["training_supply"],"training_year_metrics":policy["training_metrics"],
      "training_oracle_admission":policy.get("training_oracle_admission",{}),
      "test_legal_actions":len(test_samples),"test_decision_events":len(dec),
      "two_axis_oracle":two_axis,
      "selected_route_counts":dict(routes),"selected_family_counts":dict(fams),
      "selected_action_counts":dict(acts),"selected_source_counts":dict(srcs),
      "runtime_seconds":round(time.perf_counter()-ft,3)}
    return test,fold,policy

t0=time.perf_counter()
parallel_used=False
fold_results=None
# Each burned fold is causally independent and reads immutable rows only. Fork
# preserves identical deterministic math while running folds concurrently.
if os.environ.get("V74_DISABLE_PARALLEL_FOLDS","0")!="1":
    try:
        ctx=mp.get_context("fork")
        workers=min(len(BURNED),max(1,int(os.cpu_count() or 1)))
        if workers>1:
            with ctx.Pool(processes=workers) as pool:
                fold_results=pool.map(evaluate_burned_fold,BURNED)
            parallel_used=True
    except Exception as ex:
        print("[V74-PARALLEL-FALLBACK]",repr(ex),flush=True)
if fold_results is None:
    fold_results=[evaluate_burned_fold(test) for test in BURNED]

allpass=True
for test,fold,policy in fold_results:
    summary["folds"][test]=fold
    models["folds"][test]=policy
    allpass=allpass and bool(fold["pass"])
    print("[V74-ONE-SHOT]",test,json.dumps({k:fold[k]
          for k in ("n","mean_r","pf_r","win_rate","average_rr","lcb_r","pass")}),flush=True)

alpha=bool(allpass)
champ="STRICT_WALK_FORWARD_CAUSAL_ROUTE_PLUS_OPTIMAL_STOPPING_ADMISSION" if alpha else None
summary["evaluator_runtime_seconds"]=round(time.perf_counter()-t0,3)
summary["parallel_fold_execution"]=parallel_used
summary["parallel_fold_workers"]=min(len(BURNED),max(1,int(os.cpu_count() or 1))) if parallel_used else 1
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
                  "parallel_fold_execution":parallel_used,
                  "evaluator_runtime_seconds":summary["evaluator_runtime_seconds"]},indent=2))
