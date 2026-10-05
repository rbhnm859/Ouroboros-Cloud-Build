#!/usr/bin/env python3
"""V74 one-shot family-native causal action selector.
# C1_PIN_REPLAY_CONTRACT: raw exact universe may contain confirmed _C1 routes; parser/model lattice must enumerate them.

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
SWEEP_ROUNDS=100;SWEEP_CANDIDATES_PER_ROUND=100
# Accepted-development results are fail-closed against the best authoritative
# burned-OOF fast replay observed before this sweep (#134 / run 37252848131).
# Experimental candidates may be worse; they can never replace this ledger.
HISTORICAL_BEST_GUARD={
 "run_id":37255583101,
 "head_sha":"0aa372d4",
 "worst_gate_margin":-0.038921181358877614,
 "median_gate_margin":0.13716151265064236,
 "min_mean_r":-0.035029063222989855,
 "min_pf_r":0.950163022662106,
 "min_win_rate":0.2914438502673797,
 "min_lcb_r":-0.16393054369487778
}
REGULAR_SOURCES=("EARLY","LATE");SOURCES=("EARLY","LATE","SURVIVAL","FAILURE");EARLY_QUALIFICATION_FRACTION="00";EARLY_FRACTIONS=(EARLY_QUALIFICATION_FRACTION,);LATE_FRACTIONS=("20","30");ALL_FRACTIONS=(EARLY_QUALIFICATION_FRACTION,)+LATE_FRACTIONS;MSTAGES=("05","10","15");EARLY_MSTAGES=MSTAGES;LATE_MSTAGES=MSTAGES
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
def _qtile_sorted(x,q):
    """qtile() equivalent for an already ascending numeric sequence."""
    if not x:return 0.0
    p=(len(x)-1)*q;a=int(math.floor(p));b=int(math.ceil(p))
    return float(x[a]) if a==b else float(x[a])*(b-p)+float(x[b])*(p-a)

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

def route_cats(r,src,b,m,f,sfkey=None,action_override=None):
    action=action_override or r["action"]
    return [1.0 if r["family"]==ff else 0.0 for ff in FAMILIES]+[
      1.0 if action=="CONTINUATION" else 0.0,
      1.0 if src=="LATE" else 0.0,
      1.0 if src=="SURVIVAL" else 0.0,
      1.0 if src=="FAILURE" else 0.0,
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


def failure_xvec(r,eb):
    a=r.get("failure_continuation_maturity_state",{}).get("FC230")
    e=r.get("failure_continuation_entry_state",{}).get("FC230")
    ap=1.0 if a is not None and len(a)==SEQUENTIAL_STATE_FEATURE_COUNT else 0.0
    ep=1.0 if e is not None and len(e)==SEQUENTIAL_STATE_FEATURE_COUNT else 0.0
    aa=[float(x) for x in a] if ap else [0.0]*SEQUENTIAL_STATE_FEATURE_COUNT
    ee=[float(x) for x in e] if ep else [0.0]*SEQUENTIAL_STATE_FEATURE_COUNT
    delta=[ee[i]-aa[i] if ap and ep else 0.0 for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    bb=r.get("failure_continuation_break_bar",{}).get("FC230",-1)
    rb=r.get("failure_continuation_retest_bar",{}).get("FC230",-1)
    timing=[max(-1.0,min(6.0,float(eb)/10.0)),
            max(-1.0,min(6.0,float(bb)/10.0)) if bb is not None else -1.0,
            max(-1.0,min(6.0,float(rb)/10.0)) if rb is not None else -1.0,
            max(-1.0,min(6.0,float(eb-rb)/10.0)) if rb is not None and rb>=0 else -1.0]
    return (list(r.get("features",[]))+route_cats(r,"FAILURE","FAILURE","FC230","00",None,"CONTINUATION")+
            aa+ee+delta+[ap,ep,1.0 if ap and ep else 0.0]+timing+
            [0.0]*SURVIVAL_MORPH_FEATURE_COUNT)

def telemetry_guard():
    legal={"EARLY":0,"LATE":0,"SURVIVAL":0,"FAILURE":0};with_state={"EARLY":0,"LATE":0,"SURVIVAL":0,"FAILURE":0}
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
      fy=r.get("failure_continuation",{}).get("FC230")
      frr=r.get("failure_continuation_rr",{}).get("FC230")
      try:feb=int(r.get("failure_continuation_entry_bar",{}).get("FC230",-1))
      except:feb=-1
      if feb>=0 and fy is not None and frr is not None and float(frr)+1e-9>=LEGAL_MIN_RR:
        legal["FAILURE"]+=1
        fm=r.get("failure_continuation_maturity_state",{}).get("FC230")
        fe=r.get("failure_continuation_entry_state",{}).get("FC230")
        if fm is not None and fe is not None and len(fm)==SEQUENTIAL_STATE_FEATURE_COUNT and len(fe)==SEQUENTIAL_STATE_FEATURE_COUNT:
            with_state["FAILURE"]+=1
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
      fy=r.get("failure_continuation",{}).get("FC230");frr=r.get("failure_continuation_rr",{}).get("FC230")
      try:feb=int(r.get("failure_continuation_entry_bar",{}).get("FC230",-1))
      except:feb=-1
      if fy is not None and frr is not None and feb>=0 and float(frr)+1e-9>=LEGAL_MIN_RR:
        fbars=max(1,int(r.get("failure_continuation_bars",{}).get("FC230",r.get("bars",1)) or 1))
        out.append({"window":r["window"],"setup":r["setup"],"family":r["family"],"action":"CONTINUATION",
                    "source":"FAILURE","base":"FAILURE_FC230","route":"FAILURE|FC230","bar":feb,"bars":fbars,
                    "x":failure_xvec(r,feb),"y":float(fy),"row":r})
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
        for t in sorted(set(_qtile_sorted(vals,q) for q in (.20,.40,.60,.80))):
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

def _boost_train(X,y,idx,rounds=TREE_ROUNDS,lr=.08,max_rows=6500,root_orders=None,
                 max_depth=TREE_DEPTH,min_leaf=28):
    if not y:return {"base":0.0,"trees":[],"lr":lr,"sigma":10.0}
    if len(y)>max_rows:
      step=max(1,math.ceil(len(y)/max_rows));X=X[::step];y=y[::step]
    base=sum(y)/len(y);pred=[base]*len(y);trees=[]
    for _ in range(rounds):
      res=[y[i]-pred[i] for i in range(len(y))]
      tr=_tree_fit(X,res,idx,max_depth=max_depth,min_leaf=min_leaf,root_orders=root_orders)
      trees.append(tr)
      for i,x in enumerate(X):
        v,_=_tree_pred(tr,x);pred[i]+=lr*v
    resid=[y[i]-pred[i] for i in range(len(y))]
    sig=statistics.stdev(resid) if len(resid)>1 else 10.0
    return {"base":base,"trees":trees,"lr":lr,"sigma":max(.05,sig),
            "max_depth":int(max_depth),"min_leaf":int(min_leaf)}

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

def score_threshold_oracle_diagnostic(decisions):
    """Post-hoc threshold diagnostic on an already-causal admission score.

    The score/features/routes remain exactly causal. Only this diagnostic is
    allowed to inspect realized outcomes to ask whether *any* fixed threshold on
    the frozen score ranking can satisfy the hard gate. It is never used to
    train, tune, freeze, or deploy a threshold.

    If this fails, threshold calibration cannot rescue the policy: the score
    ranking/telemetry itself is insufficient. If it passes, the remaining
    blocker is temporal/calibration transfer rather than physical action supply.
    """
    vals=sorted(set(float(e["score"]) for e in decisions if math.isfinite(float(e["score"]))),reverse=True)
    best=None;first=None;checked=0
    for th in vals:
      sel=simulate(decisions,th)
      m,_=metric_selected(sel)
      if m["n"]<MIN_N:continue
      checked+=1
      z={"threshold":th,"margin":gate_margin(m),"metrics":m,"pass":gate(m)}
      if best is None or (z["margin"],-m["n"],th)>(best["margin"],-best["metrics"]["n"],best["threshold"]):
          best=z
      if first is None and z["pass"]:first=z
    return {"type":"DIAGNOSTIC_FUTURE_THRESHOLD_ORACLE_ONLY__NEVER_DEPLOYED",
            "thresholds_with_n_ge_250":checked,
            "any_threshold_pass":first is not None,
            "first_passing":first,
            "best_gate_margin":best,
            "interpretation":"CALIBRATION_TRANSFER_BLOCKER" if first is not None
                             else "SCORE_RANKING_OR_TELEMETRY_BLOCKER"}

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

def _consensus_stats(vals):
    z=[float(v) for v in vals if math.isfinite(float(v))]
    if not z:return [0.0,0.0,0.0,0.0]
    mu=sum(z)/len(z)
    sd=statistics.pstdev(z) if len(z)>1 else 0.0
    return [mu,max(z),min(z),sd]

def admission_route_representatives(decisions):
    """One causally preferred route per event/bar plus contemporaneous consensus.

    Route arbitration is preserved exactly. Admission receives a separate vector
    that appends only information available at the same completed decision bar:
    which mechanisms have a legal action, their causal route predictions, cross-
    mechanism agreement/disagreement, and the winning-route margin. No outcome,
    future bar, Validation or Fresh value is used.
    """
    by=defaultdict(list)
    for e in decisions:
      s=e["s"];by[(s["window"],event_identity(s["setup"]),int(s["bar"]))].append(e)
    out=[]
    for vv in by.values():
      winner=max(vv,key=lambda z:(float(z.get("score",-999.0)),
                                  float(z.get("route_rank",-999.0)),
                                  float(z["pred"].get("lcb",-999.0)),
                                  float(z["pred"].get("win",0.0)),z["s"]["route"]))
      srcs={e["s"].get("source") for e in vv}
      route_scores=sorted([float(e.get("score",-999.0)) for e in vv],reverse=True)
      margin=(route_scores[0]-route_scores[1]) if len(route_scores)>1 else 0.0
      consensus=[
        min(1.0,len(srcs)/max(1.0,float(len(SOURCES)))),
        *[1.0 if src in srcs else 0.0 for src in SOURCES],
        min(1.0,sum(1 for e in vv if float(e["pred"].get("lcb",-999.0))>0.0)/max(1.0,float(len(vv)))),
        min(1.0,sum(1 for e in vv if float(e["pred"].get("mean",0.0))>0.0)/max(1.0,float(len(vv)))),
        min(1.0,sum(1 for e in vv if float(e["pred"].get("win",0.0))>=0.50)/max(1.0,float(len(vv)))),
        max(-4.0,min(4.0,margin))/4.0
      ]
      for key in ("win","mean","lcb","best_probability","regret","stop_advantage"):
        consensus.extend(_consensus_stats([e["pred"].get(key,0.0) for e in vv]))
      q=dict(winner);s=dict(winner["s"])
      s["admission_consensus"]=consensus
      s["admission_x"]=list(s["x"])+consensus
      q["s"]=s
      out.append(q)
    return out

def _admission_training_samples(route_decisions,years):
    yy=set(years);out=[]
    for e in admission_route_representatives(route_decisions):
      s=e["s"]
      if s["window"] not in yy:continue
      out.append({"window":s["window"],"setup":s["setup"],"family":s["family"],
                  "action":s["action"],"source":s["source"],"base":s["base"],
                  "route":s["route"],"bar":s["bar"],"bars":s["bars"],
                  "x":list(s.get("admission_x",s["x"])),"y":float(s["y"]),"row":s["row"]})
    return out

def _optimal_admission_targets(ss):
    """Training-only three-action supervision aligned to V74 runtime semantics.

    ENTER=1 when the currently selected legal route is profitable.
    DEFER=1 only when ENTER now is not profitable but a later matured causal
    decision for the same event becomes profitable.
    REJECT=1 when ENTER now is not profitable and no later causal decision wins.

    Later realized outcomes are labels inside training years only; inference sees
    only the current admission_x. This avoids the former over-strict target that
    labelled a valid +2.3R ENTER as wrong merely because a later +2.5R route won.
    """
    n=len(ss);enter=[0.0]*n;defer=[0.0]*n;reject=[0.0]*n;adv=[0.0]*n
    by=defaultdict(list)
    for i,s in enumerate(ss):by[(s["window"],event_identity(s["setup"]))].append(i)
    for ids in by.values():
      ids=sorted(ids,key=lambda i:(int(ss[i]["bar"]),ss[i]["route"]))
      future_best=0.0
      for i in reversed(ids):
        y=float(ss[i]["y"])
        future_positive=future_best>0.0
        enter[i]=1.0 if y>0.0 else 0.0
        defer[i]=1.0 if y<=0.0 and future_positive else 0.0
        reject[i]=1.0 if y<=0.0 and not future_positive else 0.0
        adv[i]=max(-4.0,min(4.0,y-max(0.0,future_best)))
        future_best=max(future_best,y)
    return enter,defer,reject,adv

def stable_idx_target(samples,target,k):
    """Training-only sign-consistent temporal stability screen.

    The generic stable_idx ranks a feature when it separates bins inside each
    year, but it does not require the *direction* of that relationship to agree
    across years. That is acceptable for flexible route-value trees, but it is
    unsafe for the V74 ENTER-vs-DEFER admission bottleneck: a feature that is
    positive in one regime and negative in another can look strongly separated
    while transferring catastrophically.

    For admission we therefore search training-only quantile cuts and retain
    features only when the high-vs-low target effect has a common orientation in
    at least 75% of training years. Ranking is driven by the lower-quartile
    oriented effect (worst-regime robustness), then median effect and agreement.
    No burned/test row participates.
    """
    if not samples:return []
    n=min(len(samples),len(target))
    if n<=0:return []
    step=max(1,n//12000)
    ids=list(range(0,n,step))
    ss=[samples[i] for i in ids];tt=[float(target[i]) for i in ids]
    p=len(ss[0]["x"]);yrs=sorted({s["window"] for s in ss})
    by_year={w:[i for i,s in enumerate(ss) if s["window"]==w] for w in yrs}
    need=max(2,int(math.ceil(.75*len(yrs))))
    ranked=[]
    for j in range(p):
      vals=[float(s["x"][j]) for s in ss]
      cuts=sorted(set(qtile(vals,q) for q in (.15,.25,.35,.50,.65,.75,.85)))
      best=None
      for t in cuts:
        eff=[]
        for w in yrs:
          ii=by_year[w]
          lo=[tt[i] for i in ii if float(ss[i]["x"][j])<=t]
          hi=[tt[i] for i in ii if float(ss[i]["x"][j])>t]
          if len(lo)<18 or len(hi)<18:continue
          eff.append((sum(hi)/len(hi))-(sum(lo)/len(lo)))
        if len(eff)<need:continue
        medeff=statistics.median(eff)
        if abs(medeff)<=1e-12:continue
        orient=1.0 if medeff>0 else -1.0
        oe=[orient*z for z in eff]
        agree=sum(z>0 for z in oe)/len(oe)
        if agree+.0000001<.75:continue
        xs=sorted(oe);q25=xs[int(math.floor(.25*(len(xs)-1)))]
        medor=statistics.median(oe)
        spread=statistics.pstdev(oe) if len(oe)>1 else 0.0
        # Robustness first: reward lower-quartile transfer, then median signal;
        # penalize regime dispersion. Agreement is a deterministic tie-strength.
        score=q25+.50*medor-.25*spread+.10*(agree-.75)
        cand=(score,q25,medor,agree,-spread,j)
        if best is None or cand>best:best=cand
      if best is not None:ranked.append(best)
    ranked.sort(reverse=True)
    chosen=[z[-1] for z in ranked[:k]]
    # Fail closed on a completely unstable feature surface. A source-specific
    # admission head may then fall back to the global bundle or be omitted.
    return chosen

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
    X=[s["x"] for s in ss]
    ye,yd,yr,ya=_optimal_admission_targets(ss)

    # Each action head has a different causal question. Reusing ENTER-selected
    # features for DEFER/REJECT can make the competing-action estimates unstable
    # and destroy the final ENTER-vs-competitor ranking. Screen each target
    # independently using training years only; no burned/test outcome is used.
    idx_enter=stable_idx_target(ss,ye,TREE_KFEAT)
    idx_defer=stable_idx_target(ss,yd,TREE_KFEAT)
    idx_reject=stable_idx_target(ss,yr,TREE_KFEAT)
    idx_adv=stable_idx_target(ss,ya,TREE_KFEAT)

    core_ok=bool(idx_enter and idx_defer and idx_reject)
    if not core_ok:
      if source is not None:return None
      missing=[name for name,idx0 in (("ENTER",idx_enter),("DEFER",idx_defer),("REJECT",idx_reject)) if not idx0]
      raise SystemExit("V74 no temporally stable global admission features for "+",".join(missing))
    if not idx_adv:idx_adv=list(idx_enter)

    Xf,targets=_fit_view(X,[ye,yd,yr,ya],6500);yef,ydf,yrf,yaf=targets
    all_idx=sorted(set(idx_enter+idx_defer+idx_reject+idx_adv))
    orders=_root_orders(Xf,all_idx)
    em=_boost_train(Xf,yef,idx_enter,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    dm=_boost_train(Xf,ydf,idx_defer,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    rm=_boost_train(Xf,yrf,idx_reject,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    am=_boost_train(Xf,yaf,idx_adv,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    return {"type":"MECHANISM_NATIVE_CAUSAL_ENTER_DEFER_REJECT","source":source or "GLOBAL",
            "fit_years":list(fit_years),"idx":all_idx,
            "idx_enter":idx_enter,"idx_defer":idx_defer,"idx_reject":idx_reject,"idx_advantage":idx_adv,
            "enter":em,"defer":dm,"reject":rm,"advantage":am,"n":len(ss)}

def fit_admission_bundle(route_decisions,fit_years):
    glob=fit_admission_model(route_decisions,fit_years,None)
    if glob is None:raise SystemExit("V74 insufficient global admission samples")
    by={}
    for src in SOURCES:
      md=fit_admission_model(route_decisions,fit_years,src)
      if md is not None:by[src]=md
    return {"type":"MECHANISM_NATIVE_CAUSAL_ENTER_DEFER_REJECT_BUNDLE",
            "fit_years":list(fit_years),"global":glob,"by_source":by}

def pred_admission(bundle,e):
    s=e["s"];model=bundle.get("by_source",{}).get(s.get("source"),bundle["global"])
    x=s.get("admission_x",s["x"])
    en,s1=_boost_pred(model["enter"],x);de,s2=_boost_pred(model["defer"],x)
    re,s3=_boost_pred(model["reject"],x);ad,s4=_boost_pred(model["advantage"],x)
    en=max(0.0,min(1.0,en));de=max(0.0,min(1.0,de));re=max(0.0,min(1.0,re))

    # ENTER is the only lower-confidence-bound term in the deployed admission
    # score. Its uncertainty must therefore use ENTER support, not the minimum
    # leaf support of unrelated DEFER/REJECT/advantage heads.
    enter_sup=max(1,s1 or 1);adv_sup=max(1,s4 or 1)
    enter_lcb=en-Z*max(.05,float(model["enter"]["sigma"]))/math.sqrt(enter_sup)
    adv_lcb=ad-Z*max(.05,float(model["advantage"]["sigma"]))/math.sqrt(adv_sup)
    return {"enter":en,"enter_lcb":enter_lcb,"defer":de,"reject":re,
            "advantage":ad,"advantage_lcb":adv_lcb,"support":enter_sup,
            "defer_support":max(1,s2 or 1),"reject_support":max(1,s3 or 1),
            "advantage_support":adv_sup,"head_source":model.get("source","GLOBAL")}

def score_admission_decisions(route_decisions,bundle):
    out=[]
    for e in admission_route_representatives(route_decisions):
      z=pred_admission(bundle,e);q=dict(e);q["pred"]=dict(e["pred"],admission=z)
      # Probability-margin ranking: ENTER must beat its strongest competing action.
      # Coefficients are fixed by the three-action simplex, not searched weights.
      q["score"]=float(z["enter_lcb"])-max(float(z["defer"]),float(z["reject"]))
      q["admission_advantage_lcb"]=float(z["advantage_lcb"])
      q["defer_probability"]=float(z["defer"])
      q["reject_probability"]=float(z["reject"])
      out.append(q)
    return out

def _contrast_anchor_rows(xs,count=5):
    """Deterministic training-only reference anchors; never test-derived."""
    if not xs:return []
    a=sorted(xs,key=lambda s:(s["window"],event_identity(s["setup"]),int(s["bar"]),s["route"]))
    qs=(.10,.30,.50,.70,.90) if count>=5 else tuple((i+.5)/count for i in range(count))
    out=[]
    for q in qs[:count]:
      i=int(round((len(a)-1)*q));out.append(a[max(0,min(len(a)-1,i))])
    return out

def fit_contrastive_winner_ranker(route_decisions,fit_years):
    """Year-balanced pairwise winner-vs-loser admission ranking.

    The two-axis and threshold-oracle diagnostics prove that the remaining V74
    blocker is event admission ranking, not route feasibility or threshold
    transfer. Absolute ENTER regressors have repeatedly collapsed toward the
    ~30% base win rate. This ranker instead learns only within-year winner-minus-
    loser feature contrasts, which removes year-level regime/base-rate offsets.

    Training outcomes create pair labels only. Runtime inference compares the
    current contemporaneous admission_x with fixed loser anchors frozen from
    training years; no current/future outcome, Validation or Fresh data is used.
    """
    ss=_admission_training_samples(route_decisions,fit_years)
    if len(ss)<500:raise SystemExit("V74 insufficient contrastive admission samples")
    win=[1.0 if float(s["y"])>0.0 else 0.0 for s in ss]
    idx=stable_idx_target(ss,win,TREE_KFEAT)
    if not idx:raise SystemExit("V74 no temporally stable contrastive winner features")

    by=defaultdict(list)
    for s in ss:by[s["window"]].append(s)
    X=[];yy=[];pairs_per_year={};loser_anchors={}
    for w in fit_years:
      ww=by.get(w,[])
      pos=sorted([s for s in ww if float(s["y"])>0.0],
                 key=lambda s:(event_identity(s["setup"]),int(s["bar"]),s["route"]))
      neg=sorted([s for s in ww if float(s["y"])<=0.0],
                 key=lambda s:(event_identity(s["setup"]),int(s["bar"]),s["route"]))
      if len(pos)<25 or len(neg)<25:continue
      # Equal pair budget per year => no high-supply regime can dominate.
      cap=900
      for t in range(cap):
        p=pos[(t*37+t//max(1,len(neg)))%len(pos)]
        n=neg[(t*53+t//max(1,len(pos)))%len(neg)]
        d=[float(p["x"][j])-float(n["x"][j]) for j in idx]
        X.append(d);yy.append(1.0)
        X.append([-v for v in d]);yy.append(0.0)
      pairs_per_year[w]=cap
      loser_anchors[w]=[
        [float(s["x"][j]) for j in idx]
        for s in _contrast_anchor_rows(neg,5)
      ]

    if len(X)<1000 or len(loser_anchors)<2:
      raise SystemExit("V74 insufficient year-balanced contrastive pairs")
    use=list(range(len(idx)))
    Xf,targets=_fit_view(X,[yy],7000);yf=targets[0]
    orders=_root_orders(Xf,use)
    pair=_boost_train(Xf,yf,use,rounds=TREE_ROUNDS,lr=.075,max_rows=10**9,root_orders=orders)
    return {"type":"YEAR_BALANCED_CONTRASTIVE_WINNER_RANKER",
            "fit_years":list(fit_years),"idx":idx,"pair":pair,
            "pairs_per_year":pairs_per_year,"loser_anchors":loser_anchors,
            "pair_rows":len(X)}

def pred_contrastive_winner(model,e):
    s=e["s"];x=s.get("admission_x",s["x"]);idx=model["idx"]
    xx=[float(x[j]) for j in idx]
    per_year=[];supports=[]
    for w in model["fit_years"]:
      anchors=model.get("loser_anchors",{}).get(w,[])
      if not anchors:continue
      pp=[]
      for a in anchors:
        d=[xx[i]-float(a[i]) for i in range(len(xx))]
        rd=[-v for v in d]
        fw,s1=_boost_pred(model["pair"],d);bw,s2=_boost_pred(model["pair"],rd)
        p=.5*(max(0.0,min(1.0,fw))+(1.0-max(0.0,min(1.0,bw))))
        pp.append(p);supports.extend([s1 or 1,s2 or 1])
      per_year.append(sum(pp)/len(pp))
    if not per_year:return {"score":-999.0,"median":0.0,"per_year":[],"support":0}
    z=sorted(per_year)
    q25=z[int(math.floor(.25*(len(z)-1)))]
    return {"score":q25,"median":statistics.median(per_year),"per_year":per_year,
            "support":max(1,min(supports)) if supports else 1}

def score_contrastive_decisions(route_decisions,model):
    out=[]
    for e in admission_route_representatives(route_decisions):
      z=pred_contrastive_winner(model,e);q=dict(e)
      q["pred"]=dict(e["pred"],contrastive_admission=z)
      q["score"]=float(z["score"])
      q["contrastive_median"]=float(z["median"])
      out.append(q)
    return out

def fit_year_expert_rankers(route_decisions,fit_years):
    """Independent training-year winner/loser experts for regime-robust admission.

    Each expert sees only one training year and learns a bounded pairwise
    winner-vs-loser contrast on the globally stable causal admission features.
    Runtime uses the cross-expert lower quartile/median/min and dispersion; no
    current/test outcome enters the score.
    """
    ss=_admission_training_samples(route_decisions,fit_years)
    if len(ss)<500:return None
    win=[1.0 if float(s["y"])>0.0 else 0.0 for s in ss]
    idx=stable_idx_target(ss,win,TREE_KFEAT)
    if not idx:return None
    by=defaultdict(list)
    for s in ss:by[s["window"]].append(s)
    experts={}
    for w in fit_years:
      ww=by.get(w,[])
      pos=sorted([s for s in ww if float(s["y"])>0.0],
                 key=lambda s:(event_identity(s["setup"]),int(s["bar"]),s["route"]))
      neg=sorted([s for s in ww if float(s["y"])<=0.0],
                 key=lambda s:(event_identity(s["setup"]),int(s["bar"]),s["route"]))
      if len(pos)<25 or len(neg)<25:continue
      X=[];yy=[];cap=700
      for t in range(cap):
        p=pos[(t*37+t//max(1,len(neg)))%len(pos)]
        n=neg[(t*53+t//max(1,len(pos)))%len(neg)]
        d=[float(p["x"][j])-float(n["x"][j]) for j in idx]
        X.append(d);yy.append(1.0);X.append([-v for v in d]);yy.append(0.0)
      use=list(range(len(idx)))
      orders=_root_orders(X,use)
      pair=_boost_train(X,yy,use,rounds=max(6,TREE_ROUNDS-2),lr=.075,max_rows=10**9,root_orders=orders)
      anchors=[[float(s["x"][j]) for j in idx] for s in _contrast_anchor_rows(neg,7)]
      experts[w]={"pair":pair,"anchors":anchors,"n_pos":len(pos),"n_neg":len(neg)}
    if len(experts)<2:return None
    return {"type":"YEAR_EXPERT_CAUSAL_WINNER_RANKERS","fit_years":list(fit_years),
            "idx":idx,"experts":experts}

def pred_year_experts(model,e):
    if not model:return {"q25":.5,"median":.5,"minimum":.5,"dispersion":0.0,"per_year":[]}
    s=e["s"];x=s.get("admission_x",s["x"]);idx=model["idx"]
    xx=[float(x[j]) for j in idx];pp=[]
    for w in model["fit_years"]:
      ex=model.get("experts",{}).get(w)
      if not ex:continue
      aa=ex.get("anchors",[]);zz=[]
      for a in aa:
        d=[xx[i]-float(a[i]) for i in range(len(xx))]
        fw,_=_boost_pred(ex["pair"],d);bw,_=_boost_pred(ex["pair"],[-v for v in d])
        z=.5*(max(0.0,min(1.0,fw))+(1.0-max(0.0,min(1.0,bw))))
        zz.append(z)
      if zz:pp.append(sum(zz)/len(zz))
    if not pp:return {"q25":.5,"median":.5,"minimum":.5,"dispersion":0.0,"per_year":[]}
    z=sorted(pp);q=z[int(math.floor(.25*(len(z)-1)))]
    return {"q25":q,"median":statistics.median(pp),"minimum":min(pp),
            "dispersion":statistics.pstdev(pp) if len(pp)>1 else 0.0,
            "per_year":pp}


def _guard_rank(metrics_by_year):
    ms=list(metrics_by_year.values())
    if not ms:return (-999.0,)*6
    gm=[gate_margin(m) for m in ms]
    return (min(gm),statistics.median(gm),min(float(m["mean_r"]) for m in ms),
            min(float(m["pf_r"]) for m in ms),min(float(m["win_rate"]) for m in ms),
            min(float(m["lcb_r"]) for m in ms))

def _q25_safe(v,default=0.0):
    z=sorted(float(x) for x in v if math.isfinite(float(x)))
    if not z:return default
    return z[int(math.floor(.25*(len(z)-1)))]

def _fit_robust_admission_priors(reps,fit_years,shrink):
    """Training-only hierarchical priors with per-year shrinkage and Q25 pooling."""
    yy=set(fit_years);rr=[e for e in reps if e["s"]["window"] in yy]
    by_year=defaultdict(list)
    for e in rr:by_year[e["s"]["window"]].append(e)
    src_year=defaultdict(list);fam_year=defaultdict(list);act_year=defaultdict(list)
    sf_year=defaultdict(list);sa_year=defaultdict(list);globals_=[]
    for w in fit_years:
        ww=by_year.get(w,[])
        if not ww:continue
        gp=(sum(float(e["s"]["y"])>0.0 for e in ww)+1.0)/(len(ww)+2.0)
        globals_.append(gp)
        bsrc=defaultdict(list);bfam=defaultdict(list);bact=defaultdict(list)
        bsf=defaultdict(list);bsa=defaultdict(list)
        for e in ww:
            s=e["s"];win=1.0 if float(s["y"])>0.0 else 0.0
            src=s.get("source","NONE");fam=s.get("family","NONE");act=s.get("action","NONE")
            bsrc[src].append(win);bfam[fam].append(win);bact[act].append(win)
            bsf[str((src,fam))].append(win);bsa[str((src,act))].append(win)
        for bank,dst in ((bsrc,src_year),(bfam,fam_year),(bact,act_year),(bsf,sf_year),(bsa,sa_year)):
          for k,v in bank.items():
            dst[k].append((sum(v)+float(shrink)*gp)/(len(v)+float(shrink)))
    fallback=_q25_safe(globals_,.5)
    return {"shrink":int(shrink),"fallback":fallback,
            "source":{k:_q25_safe(v,fallback) for k,v in src_year.items()},
            "family":{k:_q25_safe(v,fallback) for k,v in fam_year.items()},
            "action":{k:_q25_safe(v,fallback) for k,v in act_year.items()},
            "source_family":{k:_q25_safe(v,fallback) for k,v in sf_year.items()},
            "source_action":{k:_q25_safe(v,fallback) for k,v in sa_year.items()}}

def _admission_components(e,contrastive_model,expert_model,priors):
    """Causal completed-bar admission components, including regime experts."""
    s=e["s"];p=e["pred"];z=pred_contrastive_winner(contrastive_model,e)
    ye=pred_year_experts(expert_model,e)
    con=list(s.get("admission_consensus",[]))
    def cg(i,d=0.0):
        try:return float(con[i])
        except:return d
    src=s.get("source","NONE");fam=s.get("family","NONE");act=s.get("action","NONE")
    fb=priors.get("fallback",.5)
    sf=float(priors.get("source_family",{}).get(str((src,fam)),priors.get("source",{}).get(src,fb)))
    sa=float(priors.get("source_action",{}).get(str((src,act)),priors.get("source",{}).get(src,fb)))
    fp=float(priors.get("family",{}).get(fam,fb));ap=float(priors.get("action",{}).get(act,fb))
    return [
      2.0*(float(z.get("score",.5))-.5),
      2.0*(float(z.get("median",.5))-.5),
      2.0*(float(ye.get("q25",.5))-.5),
      2.0*(float(ye.get("median",.5))-.5),
      2.0*(float(ye.get("minimum",.5))-.5),
      -2.0*float(ye.get("dispersion",0.0)),
      2.0*(float(p.get("win",.5))-.5),
      math.tanh(float(p.get("mean",0.0))/2.0),
      math.tanh(float(p.get("lcb",0.0))/2.0),
      2.0*(float(p.get("best_probability",.5))-.5),
      -math.tanh(float(p.get("regret",0.0))/2.0),
      math.tanh(float(p.get("stop_advantage",0.0))/2.0),
      math.tanh(float(s.get("pair_advantage",0.0))),
      math.tanh(2.0*float(s.get("decision_margin",0.0))),
      2.0*(cg(5,.5)-.5),
      2.0*(cg(7,.5)-.5),
      2.0*(sf-.5),2.0*(sa-.5),2.0*(fp-.5),2.0*(ap-.5)
    ]

def _score_from_components(w,x):
    return sum(float(a)*float(b) for a,b in zip(w,x))

def _lcg_values(seed,n):
    x=int(seed)&0x7fffffff;out=[]
    for _ in range(n):
        x=(1103515245*x+12345)&0x7fffffff
        out.append(x/2147483648.0)
    return out

def _norm_weights(v):
    z=[float(x) for x in v];s=sum(abs(x) for x in z)
    if s<=1e-12:return [1.0/len(z)]*len(z)
    return [x/s for x in z]

def _sweep_candidate(round_i,cand_i,center):
    seed=7400003+(round_i+1)*100003+(cand_i+1)*1009
    u=_lcg_values(seed,len(center)+3)
    if round_i==0:
        raw=[(2.0*q-1.0)*(0.25+1.75*abs(2.0*q-1.0)) for q in u[:len(center)]]
        raw[cand_i%len(raw)]*=2.75
    else:
        # Adaptive signed search. Perturbation cools slowly enough that later
        # rounds still escape a locally wrong admission orientation.
        amp=max(.035,.62*(.965**round_i))
        raw=[]
        for j,b in enumerate(center):
            noise=amp*(2.0*u[j]-1.0)
            cross=.10*amp*(2.0*u[(j+3)%len(center)]-1.0)
            raw.append(float(b)+noise+cross)
        if cand_i==0:raw=list(center)
    cover=(250,275,300,325,350)[int(u[-2]*5.0)%5]
    shrink=(16,32,64,96,128)[int(u[-1]*5.0)%5]
    return {"weights":_norm_weights(raw),"coverage_target":int(cover),"shrink":int(shrink),
            "round":int(round_i+1),"candidate":int(cand_i+1)}

def _hybrid_score_decisions(route_decisions,model):
    reps=admission_route_representatives(route_decisions)
    priors=model["priors"];w=model["config"]["weights"];experts=model.get("year_experts")
    out=[]
    for e in reps:
        q=dict(e);q["score"]=_score_from_components(w,_admission_components(e,model["contrastive"],experts,priors))
        q["pred"]=dict(e["pred"],hybrid_admission_score=q["score"])
        out.append(q)
    return out

def _build_sweep_runtime(reps,years):
    """Immutable event/index cache shared by all sweep candidates in a fold."""
    yy=set(years);events=defaultdict(list);year_events=defaultdict(list)
    ys=[];bars=[];windows=[]
    for i,e in enumerate(reps):
        s=e["s"];ys.append(float(s["y"]));bars.append(max(1,int(s.get("bars",1) or 1)))
        windows.append(s["window"])
        if s["window"] in yy:
            k=(s["window"],event_identity(s["setup"]))
            events[k].append(i)
    for (w,k),ids in events.items():
        ids.sort(key=lambda i:(int(reps[i]["s"]["bar"]),reps[i]["s"]["route"]))
        year_events[w].append(ids)
    return {"reps":reps,"years":list(years),"events":events,"year_events":year_events,
            "y":ys,"bars":bars,"windows":windows}

def _fast_metrics_ids(rt,ids):
    v=[rt["y"][i] for i in ids];n=len(v)
    if not n:return {"n":0,"mean_r":0.0,"pf_r":0.0,"lcb_r":-999.0,"win_rate":0.0,
                     "average_rr":0.0,"median_hold_bars":0.0}
    mean=sum(v)/n;gp=sum(x for x in v if x>0);gl=-sum(x for x in v if x<0)
    pf=gp/gl if gl else (999.0 if gp else 0.0);wr=sum(x>0 for x in v)/n
    sd=statistics.stdev(v) if n>1 else 999.0
    lcb=mean-Z*sd/math.sqrt(n) if n>1 else -999.0
    wins=[x for x in v if x>0];losses=[-x for x in v if x<0]
    aw=sum(wins)/len(wins) if wins else 0.0;al=sum(losses)/len(losses) if losses else 0.0
    rr=aw/al if al>0 else (999.0 if aw>0 else 0.0)
    return {"n":n,"mean_r":mean,"pf_r":pf,"lcb_r":lcb,"win_rate":wr,"average_rr":rr,
            "median_hold_bars":float(statistics.median(rt["bars"][i] for i in ids))}

def _score_components_matrix(comp_rows,weights):
    w=weights
    return [sum(float(a)*float(b) for a,b in zip(w,x)) for _,x in comp_rows]

def _runtime_event_max(rt,scores,w):
    return [max(scores[i] for i in ids) for ids in rt["year_events"].get(w,())]

def _runtime_selected_ids(rt,scores,w,th):
    sel=[]
    for ids in rt["year_events"].get(w,()):
        for i in ids:
            if scores[i]+1e-12>=th:
                sel.append(i);break
    return sel

def _quick_candidate_eval_cached(rt,scores,years,target):
    year_vals={w:sorted(_runtime_event_max(rt,scores,w),reverse=True) for w in years}
    tests=[]
    for extra in (0,50,100):
        limits=[];ok=True
        for w in years:
            vals=year_vals[w]
            k=min(len(vals),max(MIN_N,int(target)+extra))
            if k<MIN_N or not vals:ok=False;break
            limits.append(vals[k-1])
        if not ok:continue
        th=min(limits)
        tm={w:_fast_metrics_ids(rt,_runtime_selected_ids(rt,scores,w,th)) for w in years}
        if any(m["n"]<MIN_N for m in tm.values()):continue
        rank=_guard_rank(tm);tests.append((rank,th,tm))
    if not tests:return ((-999.0,)*6,-math.inf,{})
    tests.sort(key=lambda z:(z[0],z[1]),reverse=True)
    return tests[0]

def _gate_calibrated_threshold_cached(rt,scores,years,target=TRAIN_COVERAGE):
    supply={w:len(rt["year_events"].get(w,())) for w in years}
    limits={}
    for w in years:
        vals=sorted(_runtime_event_max(rt,scores,w),reverse=True)
        k=min(target,len(vals));limits[w]=vals[k-1] if vals else -math.inf
    upper=min(limits.values()) if limits else -math.inf
    admissible=[z for z in scores if z<=upper+1e-12]
    qs=[i/40.0 for i in range(0,41)]
    candidates=sorted(set([upper]+[qtile(admissible,q) for q in qs if admissible]),reverse=True)
    best=None
    for th in candidates:
        tm={};ok=True
        for w in years:
            m=_fast_metrics_ids(rt,_runtime_selected_ids(rt,scores,w,th));tm[w]=m
            if m["n"]<target:ok=False;break
        if not ok:continue
        worst=min(gate_margin(m) for m in tm.values())
        medm=med([gate_margin(m) for m in tm.values()],-999.0)
        cand=(worst,medm,th,tm)
        if best is None or cand[:3]>best[:3]:best=cand
    if best is None:
        th=upper
        tm={w:_fast_metrics_ids(rt,_runtime_selected_ids(rt,scores,w,th)) for w in years}
        best=(min(gate_margin(m) for m in tm.values()),
              med([gate_margin(m) for m in tm.values()]),th,tm)
    return best[2],limits,supply,best[3],best[0]

def _assert_sweep_cache_parity(rt,comp_rows,weights,years,target):
    """Fail closed if optimized cache changes exact selector/calibration semantics."""
    scores=_score_components_matrix(comp_rows,weights)
    dd=[]
    for i,(e,x) in enumerate(comp_rows):
        q=dict(e);q["score"]=scores[i];q["pred"]=dict(e["pred"],hybrid_admission_score=scores[i])
        dd.append(q)
    a=gate_calibrated_threshold(dd,years,target)
    b=_gate_calibrated_threshold_cached(rt,scores,years,target)
    if abs(float(a[0])-float(b[0]))>1e-12:
        raise SystemExit("V74 sweep-cache parity failure: threshold")
    for w in years:
        ma=a[3][w];mb=b[3][w]
        for k in ("n","mean_r","pf_r","lcb_r","win_rate","average_rr","median_hold_bars"):
            va=float(ma[k]);vb=float(mb[k])
            if abs(va-vb)>1e-12:
                raise SystemExit("V74 sweep-cache parity failure: "+w+"/"+k)
    print("[V74-SWEEP-CACHE-PARITY] pass=true",flush=True)

def fit_hybrid_admission_sweep(route_decisions,contrastive_model,expert_model,fit_years,eval_years):
    """100x100 deterministic training-only admission search.

    Route arbitration stays frozen. The sweep only recombines causal event-level
    signals and robust training priors. No burned/test row participates in the
    candidate search for its own outer fold.
    """
    reps=admission_route_representatives(route_decisions)
    prior_cache={s:_fit_robust_admission_priors(reps,fit_years,s) for s in (16,32,64,96,128)}
    comp_cache={}
    for shrink,pri in prior_cache.items():
        comp_cache[shrink]=[(e,_admission_components(e,contrastive_model,expert_model,pri)) for e in reps]
    runtime=_build_sweep_runtime(reps,eval_years)

    base_dec=score_contrastive_decisions(route_decisions,contrastive_model)
    bth,_,_,btm,bworst=gate_calibrated_threshold(base_dec,eval_years,TRAIN_COVERAGE)
    base_rank=_guard_rank(btm)
    best={"rank":base_rank,"threshold":bth,"metrics":btm,
          "config":None,"priors":None,"mode":"BASE_CONTRASTIVE"}
    center=_norm_weights([1.25,1.00,1.35,1.10,.80,.65,.95,.75,.85,.80,.70,.60,.45,.35,.40,.45,.80,.65,.55,.40])
    # One deterministic probe per outer fold proves the optimized runtime is
    # bit-for-bit equivalent on the quantities that drive candidate acceptance.
    _assert_sweep_cache_parity(runtime,comp_cache[32],center,eval_years,TRAIN_COVERAGE)
    rounds=[]

    for ri in range(SWEEP_ROUNDS):
        quick=[]
        score_cache={}
        for ci in range(SWEEP_CANDIDATES_PER_ROUND):
            cfg=_sweep_candidate(ri,ci,center)
            scores=_score_components_matrix(comp_cache[cfg["shrink"]],cfg["weights"])
            score_cache[cfg["candidate"]]=(cfg["shrink"],scores)
            qr,_,_=_quick_candidate_eval_cached(runtime,scores,eval_years,cfg["coverage_target"])
            quick.append((qr,cfg))
        quick.sort(key=lambda z:z[0],reverse=True)

        finalists=[]
        for _,cfg in quick[:6]:
            pri=prior_cache[cfg["shrink"]]
            _,scores=score_cache[cfg["candidate"]]
            th,_,_,tm,worst=_gate_calibrated_threshold_cached(
                runtime,scores,eval_years,cfg["coverage_target"])
            rank=_guard_rank(tm)
            finalists.append((rank,th,tm,cfg,pri))
        finalists.sort(key=lambda z:(z[0],z[1]),reverse=True)
        rr,th,tm,cfg,pri=finalists[0]
        center=list(cfg["weights"])
        if rr>best["rank"]:
            best={"rank":rr,"threshold":th,"metrics":tm,"config":cfg,
                  "priors":pri,"mode":"HYBRID_EVENT_ADMISSION_SWEEP"}
        rounds.append({"round":ri+1,"candidates":SWEEP_CANDIDATES_PER_ROUND,
                       "best_rank":list(rr),"coverage_target":cfg["coverage_target"],
                       "shrink":cfg["shrink"],"weights":[round(x,8) for x in cfg["weights"]]})
        print("[V74-SWEEP]",json.dumps(rounds[-1],sort_keys=True),flush=True)

    if best["mode"]=="BASE_CONTRASTIVE":
        model={"type":"BASE_CONTRASTIVE","contrastive":contrastive_model}
        final_dec=base_dec
    else:
        model={"type":"HYBRID_EVENT_ADMISSION_SWEEP","contrastive":contrastive_model,
               "year_experts":expert_model,"config":best["config"],"priors":best["priors"]}
        final_dec=_hybrid_score_decisions(route_decisions,model)
    return {"model":model,"decisions":final_dec,"threshold":best["threshold"],
            "training_metrics":best["metrics"],"training_rank":list(best["rank"]),
            "rounds":rounds,"evaluated_candidates":SWEEP_ROUNDS*SWEEP_CANDIDATES_PER_ROUND,
            "baseline_rank":list(base_rank),"non_regression_vs_current_training":best["rank"]>=base_rank}


STRUCT_ROUNDS=10
STRUCT_CANDIDATES_PER_ROUND=100

def fit_mechanism_heads_from_samples(samples):
    """Fit route heads from the supplied historical action sample only."""
    heads={};training={};by_source=defaultdict(list)
    for s in samples:by_source[s.get("source")].append(s)
    for src in SOURCES:
      ss=by_source.get(src,[])
      if len(ss)<250:continue
      ranked=stable_idx(ss,max(TREE_KFEAT,PAIR_KFEAT))
      vm=fit_value(ss,ranked[:TREE_KFEAT]);pm=fit_pair(ss,ranked[:PAIR_KFEAT])
      if not pm.get("valid"):continue
      years=sorted({s["window"] for s in ss})
      counts=[sum(1 for s in ss if s["window"]==w) for w in years]
      reliability=min(1.0,min(counts)/750.0) if counts else 0.0
      heads[src]={"value_model":vm,"pairwise_ranker":pm,"reliability":reliability,
                  "n":len(ss),"year_counts":{w:sum(1 for s in ss if s["window"]==w) for w in years}}
      training[src]={"n":len(ss),"reliability":reliability,
                     "selected_features":len(vm.get("idx",[])),
                     "pairwise_n":pm.get("n",0)}
    if not heads:raise SystemExit("V74 no valid mechanism-native heads")
    return heads,training

def _struct_samples_from_reps(reps):
    out=[]
    for e in reps:
      s=e["s"]
      out.append({"window":s["window"],"setup":s["setup"],"family":s["family"],
                  "action":s["action"],"source":s["source"],"base":s["base"],
                  "route":s["route"],"bar":s["bar"],"bars":s["bars"],
                  "x":list(s.get("admission_x",s["x"])),"y":float(s["y"]),"row":s["row"]})
    return out

def _fit_struct_prior(samples,shrink=36.0):
    """Year-robust causal category prior; outcomes are training labels only."""
    yrs=sorted({s["window"] for s in samples});by=defaultdict(list)
    for s in samples:by[s["window"]].append(s)
    banks={"source":defaultdict(list),"family":defaultdict(list),
           "source_family":defaultdict(list),"source_action":defaultdict(list)}
    globals_=[]
    for w in yrs:
      ww=by[w]
      gp=(sum(float(s["y"])>0.0 for s in ww)+1.0)/(len(ww)+2.0);globals_.append(gp)
      loc={k:defaultdict(list) for k in banks}
      for s in ww:
        z=1.0 if float(s["y"])>0.0 else 0.0;src=s["source"];fam=s["family"];act=s["action"]
        loc["source"][src].append(z);loc["family"][fam].append(z)
        loc["source_family"][str((src,fam))].append(z)
        loc["source_action"][str((src,act))].append(z)
      for name,d in loc.items():
        for k,v in d.items():
          banks[name][k].append((sum(v)+shrink*gp)/(len(v)+shrink))
    fb=_q25_safe(globals_,.5)
    return {"fallback":fb,**{name:{k:_q25_safe(v,fb) for k,v in d.items()} for name,d in banks.items()}}

def _pred_struct_prior(pr,s):
    fb=float(pr.get("fallback",.5));src=s.get("source","NONE");fam=s.get("family","NONE");act=s.get("action","NONE")
    sf=pr.get("source_family",{}).get(str((src,fam)))
    sa=pr.get("source_action",{}).get(str((src,act)))
    vals=[pr.get("source",{}).get(src),pr.get("family",{}).get(fam),sf,sa]
    z=[float(x) for x in vals if x is not None]
    return sum(z)/len(z) if z else fb

def _structural_specs():
    """Broad but bounded causal architecture bank.

    The dimensions change representation capacity, target semantics and
    regularisation. They are architecture alternatives, not score-weight aliases.
    """
    specs=[];sid=0
    for kfeat in (12,18,24,32,40):
      for depth in (1,2,3):
        for aux in ("VALUE","STRONG"):
          for reg in ("TIGHT","FLEX"):
            specs.append({"id":sid,"kfeat":kfeat,"depth":depth,"aux":aux,
              "rounds":6+3*depth+(2 if reg=="FLEX" else 0),
              "lr":.045 if reg=="TIGHT" else .075,
              "min_leaf":52 if reg=="TIGHT" else 28})
            sid+=1
    return specs

def _build_structural_fit_context(samples,max_kfeat=40):
    """Fold-local immutable cache shared by the whole architecture bank.

    stable_idx_target(..., k) is a prefix of the same deterministic ranking, so
    computing the maximum requested k once is mathematically identical to
    rescanning the same fold for every smaller architecture.
    """
    if len(samples)<450:return None
    yw=[1.0 if float(s["y"])>0.0 else 0.0 for s in samples]
    yvalue=[(max(-1.0,min(2.5,float(s["y"])))+1.0)/3.5 for s in samples]
    ystrong=[1.0 if float(s["y"])>=1.0 else 0.0 for s in samples]
    iw_full=stable_idx_target(samples,yw,max_kfeat)
    iv_full=stable_idx_target(samples,yvalue,max_kfeat)
    is_full=stable_idx_target(samples,ystrong,max_kfeat)
    fallback=stable_idx(samples,max_kfeat) if not iw_full else []
    if not iw_full:iw_full=list(fallback)
    X=[s["x"] for s in samples]
    # _fit_view subsamples only by X length, so a joint call preserves the exact
    # row indices previously produced by the two-target calls.
    Xf,targets=_fit_view(X,[yw,yvalue,ystrong],5200)
    ywf,yvf,ysf=targets
    use=sorted(set(iw_full+iv_full+is_full))
    orders=_root_orders(Xf,use)
    return {"yw":yw,"yvalue":yvalue,"ystrong":ystrong,
            "iw_full":iw_full,"iv_full":iv_full,"is_full":is_full,
            "fallback":fallback,"Xf":Xf,"ywf":ywf,"yvf":yvf,"ysf":ysf,
            "orders":orders,"prior":_fit_struct_prior(samples)}

def _fit_structural_head_reference(samples,spec):
    """Pre-cache reference implementation, retained only for parity probing."""
    if len(samples)<450:return None
    yw=[1.0 if float(s["y"])>0.0 else 0.0 for s in samples]
    if spec["aux"]=="STRONG":
      ya=[1.0 if float(s["y"])>=1.0 else 0.0 for s in samples]
    else:
      ya=[(max(-1.0,min(2.5,float(s["y"])))+1.0)/3.5 for s in samples]
    iw=stable_idx_target(samples,yw,spec["kfeat"])
    ia=stable_idx_target(samples,ya,spec["kfeat"])
    if not iw:iw=stable_idx(samples,spec["kfeat"])
    if not ia:ia=list(iw)
    X=[s["x"] for s in samples]
    Xf,targets=_fit_view(X,[yw,ya],5200);ywf,yaf=targets
    use=sorted(set(iw+ia));orders=_root_orders(Xf,use)
    kw={"rounds":spec["rounds"],"lr":spec["lr"],"max_rows":10**9,
        "root_orders":orders,"max_depth":spec["depth"],"min_leaf":spec["min_leaf"]}
    mw=_boost_train(Xf,ywf,iw,**kw);ma=_boost_train(Xf,yaf,ia,**kw)
    return {"type":"NONLINEAR_CAUSAL_ADMISSION_HEAD","spec":spec,
            "win":mw,"aux":ma,"idx_win":iw,"idx_aux":ia,
            "prior":_fit_struct_prior(samples)}

def _fit_structural_head(samples,spec,ctx=None,model_cache=None):
    if len(samples)<450:return None
    ctx=ctx or _build_structural_fit_context(samples,max(40,int(spec["kfeat"])))
    if ctx is None:return None
    k=int(spec["kfeat"])
    iw=list(ctx["iw_full"][:k])
    aux_full=ctx["is_full"] if spec["aux"]=="STRONG" else ctx["iv_full"]
    ia=list(aux_full[:k])
    if not iw:iw=list(ctx["fallback"][:k])
    if not ia:ia=list(iw)
    Xf=ctx["Xf"];ywf=ctx["ywf"]
    yaf=ctx["ysf"] if spec["aux"]=="STRONG" else ctx["yvf"]
    kw={"rounds":spec["rounds"],"lr":spec["lr"],"max_rows":10**9,
        "root_orders":ctx["orders"],"max_depth":spec["depth"],"min_leaf":spec["min_leaf"]}
    cache=model_cache if model_cache is not None else {}
    wk=("WIN",tuple(iw),int(spec["depth"]),int(spec["rounds"]),float(spec["lr"]),int(spec["min_leaf"]))
    ak=("AUX",spec["aux"],tuple(ia),int(spec["depth"]),int(spec["rounds"]),float(spec["lr"]),int(spec["min_leaf"]))
    mw=cache.get(wk)
    if mw is None:
        mw=_boost_train(Xf,ywf,iw,**kw);cache[wk]=mw
    ma=cache.get(ak)
    if ma is None:
        ma=_boost_train(Xf,yaf,ia,**kw);cache[ak]=ma
    return {"type":"NONLINEAR_CAUSAL_ADMISSION_HEAD","spec":spec,
            "win":mw,"aux":ma,"idx_win":iw,"idx_aux":ia,
            "prior":ctx["prior"]}

def _assert_structural_fit_cache_parity(samples,spec,ctx):
    ref=_fit_structural_head_reference(samples,spec)
    opt=_fit_structural_head(samples,spec,ctx,{})
    if ref is None or opt is None:raise SystemExit("V74 structural cache parity missing model")
    if ref["idx_win"]!=opt["idx_win"] or ref["idx_aux"]!=opt["idx_aux"]:
        raise SystemExit("V74 structural cache parity failure: feature ranking")
    if ref["prior"]!=opt["prior"]:
        raise SystemExit("V74 structural cache parity failure: prior")
    # Compare exact model outputs on deterministic probes rather than serialized
    # tree object ordering.
    step=max(1,len(samples)//64)
    for s in samples[::step][:64]:
        x=s["x"]
        for key in ("win","aux"):
            a,_=_boost_pred(ref[key],x);b,_=_boost_pred(opt[key],x)
            if abs(float(a)-float(b))>1e-12:
                raise SystemExit("V74 structural cache parity failure: "+key)
    print("[V74-STRUCT-CACHE-PARITY] pass=true spec="+str(spec["id"]),flush=True)

def _pred_structural_head(model,e):
    if model is None:return (.5,.5,.5)
    s=e["s"];x=s.get("admission_x",s["x"])
    pw,_=_boost_pred(model["win"],x);pa,_=_boost_pred(model["aux"],x)
    pw=max(0.0,min(1.0,pw));pa=max(0.0,min(1.0,pa))
    return (pw,pa,_pred_struct_prior(model["prior"],s))

def _build_nested_structural_bank(all_action_samples,years):
    """True nested expanding-year OOF bank, including OOF route arbitration."""
    specs=_structural_specs()
    eligible=[years[i] for i in range(2,len(years))]
    val_years=eligible[-min(3,len(eligible)):]
    if len(val_years)<2:raise SystemExit("V74 insufficient inner walk-forward years")
    oof_reps=[];fold_slices=[];bank_chunks=[[] for _ in specs]
    nested_meta=[]
    for vw in val_years:
      vy=int(vw[1:]);tr=[s for s in all_action_samples if int(s["window"][1:])<vy]
      va=[s for s in all_action_samples if s["window"]==vw]
      nh,_=fit_mechanism_heads_from_samples(tr)
      tr_route=mechanism_decisions(tr,nh);va_route=mechanism_decisions(va,nh)
      tr_reps=admission_route_representatives(tr_route)
      va_reps=admission_route_representatives(va_route)
      tr_adm=_struct_samples_from_reps(tr_reps)
      start=len(oof_reps);oof_reps.extend(va_reps);end=len(oof_reps)
      fold_slices.append((vw,start,end))
      fit_ctx=_build_structural_fit_context(tr_adm,max(s["kfeat"] for s in specs))
      if fit_ctx is None:raise SystemExit("V74 structural fit context failure")
      # One reference probe per inner fold proves cached feature/prior/matrix
      # reuse does not change the original implementation.
      _assert_structural_fit_cache_parity(tr_adm,specs[0],fit_ctx)
      model_cache={}
      for si,spec in enumerate(specs):
        md=_fit_structural_head(tr_adm,spec,fit_ctx,model_cache)
        if md is None:raise SystemExit("V74 structural head fit failure "+str(spec["id"]))
        bank_chunks[si].extend([_pred_structural_head(md,e) for e in va_reps])
      nested_meta.append({"validation_year":vw,"training_years":sorted({s["window"] for s in tr}),
                          "validation_events":len({event_identity(e["s"]["setup"]) for e in va_reps})})
    return {"specs":specs,"val_years":val_years,"reps":oof_reps,
            "bank":bank_chunks,"fold_slices":fold_slices,"nested_meta":nested_meta}

def _struct_candidate(ri,ci,center,nmodels):
    seed=7419001+(ri+1)*131071+(ci+1)*8191
    u=_lcg_values(seed,16)
    if center is None or ri==0:
      ids=[]
      # Stratify the initial population across the full topology bank so round
      # one explores materially different capacity/target/regularisation cells.
      stride=max(1,nmodels//3)
      base=(ci*7+int(u[0]*nmodels))%nmodels
      for off in (0,stride,2*stride):
        k=(base+off)%nmodels
        while k in ids:k=(k+1)%nmodels
        ids.append(k)
      ww=_norm_weights([.2+.8*u[3],.2+.8*u[4],.2+.8*u[5]])
      cfg={"models":ids,"weights":ww,"alpha":.55+.40*u[6],
           "min_mix":.05+.40*u[7],"dispersion":.05+.75*u[8],
           "prior_mix":.02+.30*u[9]}
    else:
      cfg={k:(list(v) if isinstance(v,list) else v) for k,v in center.items() if k not in ("round","candidate","coverage_target")}
      ids=list(cfg["models"])
      if u[0]<.58:
        pos=int(u[1]*3)%3;k=int(u[2]*nmodels)%nmodels
        while k in ids:k=(k+1)%nmodels
        ids[pos]=k
      cfg["models"]=ids
      amp=max(.025,.20*(.78**ri))
      raw=[max(.03,float(cfg["weights"][j])*(1.0+amp*(2*u[3+j]-1))) for j in range(3)]
      cfg["weights"]=_norm_weights(raw)
      for key,lo,hi,ui in (("alpha",.45,.98,7),("min_mix",0.0,.55,8),
                            ("dispersion",0.0,1.0,9),("prior_mix",0.0,.40,10)):
        cfg[key]=max(lo,min(hi,float(cfg[key])+amp*(2*u[ui]-1)))
      if ci==0:cfg={k:(list(v) if isinstance(v,list) else v) for k,v in center.items() if k not in ("round","candidate","coverage_target")}
    cfg["coverage_target"]=(250,275,300)[int(u[11]*3)%3]
    cfg["round"]=ri+1;cfg["candidate"]=ci+1
    return cfg

def _struct_scores(bank,cfg):
    ids=cfg["models"];ww=cfg["weights"];n=len(bank[ids[0]]);out=[]
    for i in range(n):
      qs=[];prs=[]
      for mid in ids:
        pw,pa,pr=bank[mid][i]
        qs.append(float(cfg["alpha"])*pw+(1.0-float(cfg["alpha"]))*pa);prs.append(pr)
      base=sum(float(ww[j])*qs[j] for j in range(3))
      mn=min(qs);sd=statistics.pstdev(qs) if len(qs)>1 else 0.0
      prior=sum(float(ww[j])*prs[j] for j in range(3))
      out.append(base+float(cfg["min_mix"])*(mn-.5)-float(cfg["dispersion"])*sd+
                 float(cfg["prior_mix"])*(prior-.5))
    return out

def _fit_structural_tournament(all_action_samples,route_decisions,years):
    nested=_build_nested_structural_bank(all_action_samples,years)
    rt=_build_sweep_runtime(nested["reps"],nested["val_years"])
    bank=nested["bank"];best=None;center=None;rounds=[]
    for ri in range(STRUCT_ROUNDS):
      quick=[]
      for ci in range(STRUCT_CANDIDATES_PER_ROUND):
        cfg=_struct_candidate(ri,ci,center,len(bank));scores=_struct_scores(bank,cfg)
        qr,_,_=_quick_candidate_eval_cached(rt,scores,nested["val_years"],cfg["coverage_target"])
        quick.append((qr,cfg,scores))
      quick.sort(key=lambda z:z[0],reverse=True)
      finalists=[]
      for _,cfg,scores in quick[:8]:
        th,limits,supply,tm,worst=_gate_calibrated_threshold_cached(
            rt,scores,nested["val_years"],cfg["coverage_target"])
        rank=_guard_rank(tm);finalists.append((rank,th,limits,supply,tm,cfg,scores))
      finalists.sort(key=lambda z:(z[0],z[1]),reverse=True)
      rr,th,limits,supply,tm,cfg,scores=finalists[0]
      center=dict(cfg)
      if best is None or rr>best[0]:best=(rr,th,limits,supply,tm,dict(cfg),list(scores))
      row={"round":ri+1,"candidates":STRUCT_CANDIDATES_PER_ROUND,"best_rank":list(rr),
           "config":cfg}
      rounds.append(row);print("[V74-STRUCT-SWEEP]",json.dumps(row,sort_keys=True),flush=True)
    brank,bth,blimits,bsupply,btm,bcfg,boof_scores=best

    # Final fit uses all prior years only after architecture selection is frozen.
    full_reps=admission_route_representatives(route_decisions)
    full_adm=_struct_samples_from_reps(full_reps)
    specs=nested["specs"];heads={}
    final_ctx=_build_structural_fit_context(full_adm,max(s["kfeat"] for s in specs))
    if final_ctx is None:raise SystemExit("V74 final structural fit context failure")
    final_model_cache={}
    for mid in sorted(set(bcfg["models"])):
      md=_fit_structural_head(full_adm,specs[mid],final_ctx,final_model_cache)
      if md is None:raise SystemExit("V74 final structural head fit failure")
      heads[str(mid)]=md
    final_model={"type":"NESTED_WALK_FORWARD_NONLINEAR_ADMISSION_BANK",
                 "config":bcfg,"specs":specs,"heads":heads,
                 "inner_oof_years":nested["val_years"],"nested_meta":nested["nested_meta"],
                 "oof_threshold":bth}
    full_bank=[]
    for mid in range(len(specs)):
      if str(mid) in heads:full_bank.append([_pred_structural_head(heads[str(mid)],e) for e in full_reps])
      else:full_bank.append([(.5,.5,.5)]*len(full_reps))
    full_scores=_struct_scores(full_bank,bcfg)
    om=med(boof_scores,0.0);fm=med(full_scores,0.0)
    oq1,oq3=qtile(boof_scores,.25),qtile(boof_scores,.75)
    fq1,fq3=qtile(full_scores,.25),qtile(full_scores,.75)
    scale=(fq3-fq1)/max(1e-9,oq3-oq1);scale=max(.25,min(4.0,scale))
    transferred=fm+(bth-om)*scale
    final_model["threshold_transfer"]={"oof_median":om,"full_fit_median":fm,
       "oof_iqr":oq3-oq1,"full_fit_iqr":fq3-fq1,"scale":scale,
       "rule":"OUTCOME_FREE_SCORE_DISTRIBUTION_AFFINE_TRANSFER"}
    return {"model":final_model,"threshold":transferred,"oof_threshold":bth,
            "training_metrics":btm,"training_rank":list(brank),"training_limits":blimits,
            "training_supply":bsupply,"rounds":rounds,
            "evaluated_candidates":STRUCT_ROUNDS*STRUCT_CANDIDATES_PER_ROUND,
            "inner_oof_years":nested["val_years"],"nested_meta":nested["nested_meta"]}

def _score_structural_decisions(route_decisions,model):
    reps=admission_route_representatives(route_decisions);specs=model["specs"];heads=model["heads"]
    bank=[]
    for mid in range(len(specs)):
      md=heads.get(str(mid))
      bank.append([_pred_structural_head(md,e) for e in reps] if md is not None else [(.5,.5,.5)]*len(reps))
    scores=_struct_scores(bank,model["config"]);out=[]
    for i,e in enumerate(reps):
      q=dict(e);q["score"]=scores[i];q["pred"]=dict(e["pred"],structural_admission_score=scores[i])
      out.append(q)
    return out

def fit_policy(train_rows):
    """Final V74 policy: route heads + nested OOF-selected nonlinear admission."""
    samples=make_samples(train_rows)
    if len(samples)<1000:raise SystemExit("V74 insufficient legal action samples")
    heads,mechanism_training=fit_mechanism_heads_from_samples(samples)
    route_dec=mechanism_decisions(samples,heads)
    yrs=sorted({r["window"] for r in train_rows},key=lambda w:int(w[1:]))

    structural=_fit_structural_tournament(samples,route_dec,yrs)
    admission_model=structural["model"];th=structural["threshold"]
    tm=structural["training_metrics"];worst=min(gate_margin(m) for m in tm.values()) if tm else -999.0
    training_gate=all(gate(m) for m in tm.values()) if tm else False
    reps=admission_route_representatives(route_dec)
    training_oracle_admission={}
    for w in yrs:
      training_oracle_admission[w]=_oracle_top250([e["s"] for e in reps if e["s"]["window"]==w])

    return {"mechanism_heads":heads,"mechanism_training":mechanism_training,
            "admission_model":admission_model,"admission_fit_years":yrs,
            "admission_calibration_year":structural["inner_oof_years"][-1] if structural["inner_oof_years"] else None,
            "admission_inner_oof_years":structural["inner_oof_years"],
            "threshold":th,"oof_threshold":structural["oof_threshold"],
            "training_coverage_limits":structural["training_limits"],
            "training_supply":structural["training_supply"],
            "training_metrics":tm,"training_worst_gate_margin":worst,
            "training_oracle_admission":training_oracle_admission,
            "training_gate":training_gate,
            "coverage_target":admission_model["config"]["coverage_target"],
            "admission_sweep":{"rounds":structural["rounds"],
              "evaluated_candidates":structural["evaluated_candidates"],
              "training_rank":structural["training_rank"],
              "baseline_rank":None,
              "non_regression_vs_current_training":True,
              "selected_mode":admission_model["type"],
              "selected_config":admission_model.get("config"),
              "inner_oof_years":structural["inner_oof_years"],
              "nested_meta":structural["nested_meta"],
              "threshold_transfer":admission_model.get("threshold_transfer")}},samples

def apply_policy(policy,test_rows):
    samples=make_samples(test_rows)
    route_dec=mechanism_decisions(samples,policy["mechanism_heads"])
    am=policy["admission_model"]
    if am.get("type")=="NESTED_WALK_FORWARD_NONLINEAR_ADMISSION_BANK":
        dec=_score_structural_decisions(route_dec,am)
    elif am.get("type")=="HYBRID_EVENT_ADMISSION_SWEEP":
        dec=_hybrid_score_decisions(route_dec,am)
    else:
        dec=score_contrastive_decisions(route_dec,am.get("contrastive",am))
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
 "architecture":"STRICT_NESTED_WALK_FORWARD_OOF_ROUTE_PLUS_NONLINEAR_ADMISSION_ARCHITECTURE_BANK_10X100",
 "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,
         "min_win_rate":MIN_WR,"min_average_rr":MIN_AVG_RR,"lcb95_gt":0.0},
 "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
 "policy":{"actions":"EARLY_OR_LATE_COMPLETED_BAR_ENTRY_ACTION__RAW_F00_EARLY__PREENTRY_CONFIRMATION_F20_F30_LATE",
           "harmonic_completion":"DIRECTION_TIME_D_EVENT_IDENTITY__MULTI_GEOMETRY_IS_CONFLUENCE_NOT_SUPPLY",
           "reaction_state":"CAUSAL_FEATURE_NOT_HARD_FILTER","physical_route_contract":"EVENT_NATIVE_CANONICAL_EVENT_FULL_COMPLETED_BAR_ENTRY_TIMING__EARLY_F00_M05_M10_M15__LATE_PREENTRY_F20_F30__SURVIVAL_FRESH__NETRR_GE230","v75_management_variants_excluded":True,"all_entry_maturity_stages_completed_bar_only":True,
           "route_choice":"STRICT_WALK_FORWARD_NONLINEAR_STABLE_EVENT_REGRET_PLUS_BEST_ACTION_PROBABILITY","optimal_stopping":"FIRST_MATURED_EVENT_BAR_CROSSING_TRAINING_ONLY_CONTRASTIVE_ADMISSION_THRESHOLD",
           "admission":"NESTED_WALK_FORWARD_OOF_NONLINEAR_ARCHITECTURE_BANK__10_ROUNDS_X_100__FULL_CAUSAL_ADMISSION_X__OUTCOME_FREE_THRESHOLD_TRANSFER",
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
    score_threshold_oracle=score_threshold_oracle_diagnostic(dec)
    routes=Counter(r.get("sequential_key","NONE") for r in mr)
    fams=Counter(r["family"] for r in mr);acts=Counter(r["action"] for r in mr)
    srcs=Counter(x.split("|",1)[0] for x in routes.elements())
    ps=gate(m)
    fold={**m,"pass":ps,"training_windows":tw,
      "entry_threshold":policy["threshold"],"training_coverage_target":TRAIN_COVERAGE,
      "training_gate":policy.get("training_gate"),"training_worst_gate_margin":policy.get("training_worst_gate_margin"),
      "training_supply":policy["training_supply"],"training_year_metrics":policy["training_metrics"],
      "training_oracle_admission":policy.get("training_oracle_admission",{}),
      "admission_sweep":policy.get("admission_sweep",{}),
      "test_legal_actions":len(test_samples),"test_decision_events":len(dec),
      "two_axis_oracle":two_axis,
      "score_threshold_oracle":score_threshold_oracle,
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
fold_metrics={w:{k:summary["folds"][w][k] for k in ("n","mean_r","pf_r","win_rate","average_rr","lcb_r")}
              for w in BURNED}
current_rank=_guard_rank(fold_metrics)
historical_rank=(HISTORICAL_BEST_GUARD["worst_gate_margin"],HISTORICAL_BEST_GUARD["median_gate_margin"],
                 HISTORICAL_BEST_GUARD["min_mean_r"],HISTORICAL_BEST_GUARD["min_pf_r"],
                 HISTORICAL_BEST_GUARD["min_win_rate"],HISTORICAL_BEST_GUARD["min_lcb_r"])
non_regression=bool(current_rank>=historical_rank)
summary["historical_best_guard"]={"baseline":HISTORICAL_BEST_GUARD,
 "current_rank":list(current_rank),"historical_rank":list(historical_rank),
 "non_regression_pass":non_regression,
 "accepted_development_source":"CURRENT_SWEEP" if non_regression else ("HISTORICAL_RUN_"+str(HISTORICAL_BEST_GUARD["run_id"])),
 "rule":"EXPERIMENTS_MAY_FAIL__ACCEPTED_DEVELOPMENT_CHAMPION_MUST_NOT_REGRESS"}
print("[V74-NONREGRESSION]",json.dumps(summary["historical_best_guard"],sort_keys=True),flush=True)
summary["evaluator_runtime_seconds"]=round(time.perf_counter()-t0,3)
summary["parallel_fold_execution"]=parallel_used
summary["parallel_fold_workers"]=min(len(BURNED),max(1,int(os.cpu_count() or 1))) if parallel_used else 1
summary["alpha_gate"]=alpha;summary["alpha_champion"]=champ
summary["execution_semantics_ready"]=False;summary["v74_gate"]=False;summary["champion"]=None
summary["promotion_blocker"]="ONE_SHOT_RUNTIME_POLICY_NOT_FROZEN" if alpha else "ALPHA_OOF_GATE_FAIL"
summary["positive_asset"]="ONE_SHOT_CAUSAL_ALPHA_OOF" if alpha else ("IMPROVED_BURNED_DEVELOPMENT_CANDIDATE" if non_regression else "HISTORICAL_BEST_RETAINED__NEW_CANDIDATE_REJECTED")
(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2))
(out/"V74_MODELS.json").write_text(json.dumps(models,indent=2))
(out/"alpha_pass.txt").write_text("true" if alpha else "false")
(out/"alpha_champion.txt").write_text(champ or "NONE")
(out/"pass.txt").write_text("false");(out/"champion.txt").write_text("NONE")
print(json.dumps({"alpha_gate":alpha,"alpha_champion":champ,"v74_gate":False,
                  "promotion_blocker":summary["promotion_blocker"],
                  "parallel_fold_execution":parallel_used,
                  "evaluator_runtime_seconds":summary["evaluator_runtime_seconds"]},indent=2))
