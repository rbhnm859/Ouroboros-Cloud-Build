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
# V74 performance-engine generation: immutable-prebuild/shared-inner-context-v1
from collections import defaultdict,Counter
from v74_model_lib import load_rows,metrics,SEQUENTIAL_STATE_FEATURE_COUNT,SURVIVAL_MORPH_FEATURE_COUNT,SURVIVAL_PATH_V2_FEATURE_COUNT,R7_COMMON_PATH_FEATURE_COUNT,FAMILIES,SURVIVAL_FRESH_KEYS,FEATURE_NAMES
from v74_model_lib import event_identity
from harmonic_precision_contract import harmonic_precision_vector

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

def common_path_r7(r,src,m,b,f):
    k=key(m,b,f)
    bank=r.get("sequential_path_r7",{}) if src=="EARLY" else r.get("late_auction_path_r7",{})
    v=bank.get(k)
    if v is None or len(v)!=R7_COMMON_PATH_FEATURE_COUNT:return None
    try:
        z=[float(x) for x in v]
        return z if all(math.isfinite(x) for x in z) else None
    except:return None

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

_HARMONIC_PRECISION_CACHE={}
def _precision_vector(r):
    k=(r.get("window"),r.get("setup"))
    z=_HARMONIC_PRECISION_CACHE.get(k)
    if z is None:
        z=tuple(harmonic_precision_vector(r.get("family","ABCD"),list(r.get("features",[]))))
        _HARMONIC_PRECISION_CACHE[k]=z
    return list(z)

def xvec(r,src,m,b,f,eb):
    # Missing reaction/path snapshots are explicit evidence, not a hard rejection.
    a=maturity_state(r,src,m,b,f);e=entry_state(r,src,m,b,f)
    ap=1.0 if a is not None else 0.0;ep=1.0 if e is not None else 0.0
    aa=a if a is not None else [0.0]*SEQUENTIAL_STATE_FEATURE_COUNT
    ee=e if e is not None else [0.0]*SEQUENTIAL_STATE_FEATURE_COUNT
    delta=[ee[i]-aa[i] if ap and ep else 0.0 for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    hp=_precision_vector(r)
    return (list(r.get("features",[]))+hp+route_cats(r,src,b,m,f)+aa+ee+delta+
            [ap,ep,1.0 if ap and ep else 0.0]+timing_state(r,src,m,b,f,eb)+
            [0.0]*SURVIVAL_MORPH_FEATURE_COUNT+
            (common_path_r7(r,src,m,b,f) or [0.0]*R7_COMMON_PATH_FEATURE_COUNT))

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
    # Legacy field name path_v2 now carries the authoritative 32-dimensional
    # Path V3 multiscale completed-M1 telemetry.  Completeness is fail-closed in
    # telemetry_guard(); append it here so the unified SURVIVAL expert actually
    # consumes the already-approved causal telemetry instead of merely auditing it.
    pv=r.get("survival_fresh_path_v2",{}).get(sf)
    path_v3=[float(x) for x in pv] if pv is not None and len(pv)==SURVIVAL_PATH_V2_FEATURE_COUNT else [0.0]*SURVIVAL_PATH_V2_FEATURE_COUNT
    hp=_precision_vector(r)
    return (list(r.get("features",[]))+hp+route_cats(r,"SURVIVAL","SURVIVAL","FIB","00",sf)+
            aa+ee+delta+[ap,ep,1.0 if ap and ep else 0.0]+timing+morph+path_v3)


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
    hp=_precision_vector(r)
    pv=r.get("failure_continuation_path_r7",{}).get("FC230")
    path_r7=[float(x) for x in pv] if pv is not None and len(pv)==R7_COMMON_PATH_FEATURE_COUNT else [0.0]*R7_COMMON_PATH_FEATURE_COUNT
    return (list(r.get("features",[]))+hp+route_cats(r,"FAILURE","FAILURE","FC230","00",None,"CONTINUATION")+
            aa+ee+delta+[ap,ep,1.0 if ap and ep else 0.0]+timing+
            [0.0]*SURVIVAL_MORPH_FEATURE_COUNT+path_r7)

def telemetry_guard():
    legal={"EARLY":0,"LATE":0,"SURVIVAL":0,"FAILURE":0};with_state={"EARLY":0,"LATE":0,"SURVIVAL":0,"FAILURE":0}
    survival_morphology=0;survival_path_v2=0;r7_common_legal=0;r7_common_complete=0
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
              r7_common_legal+=1
              if common_path_r7(r,src,m,b,f) is not None:r7_common_complete+=1
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
        pv=r.get("survival_fresh_path_v2",{}).get(sf)
        if pv is not None and len(pv)==SURVIVAL_PATH_V2_FEATURE_COUNT:survival_path_v2+=1
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
        r7_common_legal+=1
        fp=r.get("failure_continuation_path_r7",{}).get("FC230")
        if fp is not None and len(fp)==R7_COMMON_PATH_FEATURE_COUNT:r7_common_complete+=1
    if sum(legal.values())==0:raise SystemExit("V74 no legal completed-bar actions")
    if r7_common_legal>0 and r7_common_complete!=r7_common_legal:
        raise SystemExit("V74-R7 common path completeness contract failure "+str(r7_common_complete)+"/"+str(r7_common_legal))
    if legal["SURVIVAL"]>0 and survival_path_v2!=legal["SURVIVAL"]:
        raise SystemExit("V74 R7 survival path-v4 completeness contract failure "+
                         str(survival_path_v2)+"/"+str(legal["SURVIVAL"]))
    return {"legal_actions":legal,"complete_path_state":with_state,
            "survival_morphology_complete":survival_morphology,
            "survival_morphology_missing":max(0,legal["SURVIVAL"]-survival_morphology),
            "survival_path_v4_complete":survival_path_v2,
            "survival_path_v4_missing":max(0,legal["SURVIVAL"]-survival_path_v2),
            "survival_path_v4_contract_pass":survival_path_v2==legal["SURVIVAL"],
            "r7_common_path_complete":r7_common_complete,"r7_common_path_legal":r7_common_legal,
            "r7_common_path_contract_pass":r7_common_complete==r7_common_legal,
            "survival_path_v3_compat_complete":survival_path_v2,
            "missing_state_is_feature_not_veto":True,
            "future_trigger_decision_lock_state_used":False}

_OPTION_CACHE={}
def all_options(r,b):
    ck=(r["window"],r["setup"],b)
    if ck in _OPTION_CACHE:return _OPTION_CACHE[ck]
    z=[];seen_early=set()
    for src in REGULAR_SOURCES:
      for m in (EARLY_MSTAGES if src=="EARLY" else LATE_MSTAGES):
        for f in (EARLY_FRACTIONS if src=="EARLY" else LATE_FRACTIONS):
          eb=entry_bar(r,src,m,b,f)
          if eb<0:continue
          y=outcome(r,src,m,b,f)
          if y is None:continue
          bars=hold_bars(r,src,m,b,f)
          # Formal EARLY qualification is F00. In the current source semantics
          # M05/M10/M15 affect only downstream F10/F20/F30 management; for F00
          # they can therefore emit exact duplicate entry/outcome rows.  Treating
          # those aliases as independent observations violates Event Identity.
          # De-duplicate only when the observable action semantics are identical;
          # future genuinely distinct M-stage entry bars/outcomes remain separate.
          if src=="EARLY":
            sig=(b,f,int(eb),int(bars),round(float(y),12))
            if sig in seen_early:continue
            seen_early.add(sig)
          rid=("EARLY|"+b if src=="EARLY" else "LATE|M"+m+"_"+b)
          z.append({"rid":rid,"src":src,"m":m,"b":b,"f":f,"y":float(y),"bar":eb,
                    "bars":bars,"x":xvec(r,src,m,b,f,eb)})
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

def _balanced_weights_from_keys(keys):
    """Equal year mass; equal independent-event mass inside each year."""
    by=defaultdict(list)
    for i,k in enumerate(keys):by[(str(k[0]),str(k[1]))].append(i)
    years=defaultdict(list)
    for (w,eid),ids in by.items():years[w].append(ids)
    out=[0.0]*len(keys)
    for w,events in years.items():
      if not events:continue
      ew=1.0/len(events)
      for ids in events:
        q=ew/max(1,len(ids))
        for i in ids:out[i]=q
    sw=sum(out)
    if sw<=1e-18:return [1.0]*len(keys)
    scale=len(out)/sw
    return [z*scale for z in out]

def _event_year_balanced_weights(samples):
    return _balanced_weights_from_keys([
      (s["window"],event_identity(s["setup"])) for s in samples
    ])


def _tree_fit(X,y,idx,max_depth=TREE_DEPTH,min_leaf=28,root_orders=None,weights=None):
    # Event-balanced weighted SSE.  With weights=None this is exactly the former
    # unweighted objective.  SURVIVAL supplies cluster weights so one harmonic
    # event/time contributes unit mass regardless of how many legal route rows it
    # expands into (up to 80), removing pseudo-replication without discarding any
    # route geometry.
    w=[1.0]*len(y) if weights is None else [max(0.0,float(z)) for z in weights]
    if len(w)!=len(y):raise SystemExit("V74 tree weight length contract failure")
    def stats(ids):
      sw=sum(w[i] for i in ids);sw2=sum(w[i]*w[i] for i in ids)
      sy=sum(w[i]*y[i] for i in ids);sy2=sum(w[i]*y[i]*y[i] for i in ids)
      en=(sw*sw/max(1e-18,sw2)) if sw2>0 else 0.0
      return sw,sy,sy2,en
    def node(ids,depth,is_root=False):
      sw,sy,sy2,en=stats(ids)
      if sw<=1e-18:return {"leaf":0.0,"n":0}
      mu=sy/sw;leaf={"leaf":mu,"n":max(1,int(round(en)))}
      if depth<=0 or en<2*min_leaf:return leaf
      base=sy2-sy*sy/sw;best=None
      for j in idx:
        ordered=(root_orders[j] if is_root and root_orders is not None
                 else sorted(ids,key=lambda i:X[i][j]))
        vals=[X[i][j] for i in ordered]
        pw=[0.0];pw2=[0.0];py=[0.0];py2=[0.0]
        for i in ordered:
          wi=w[i];yi=y[i]
          pw.append(pw[-1]+wi);pw2.append(pw2[-1]+wi*wi)
          py.append(py[-1]+wi*yi);py2.append(py2[-1]+wi*yi*yi)
        for t in sorted(set(_qtile_sorted(vals,q) for q in (.20,.40,.60,.80))):
          p=bisect.bisect_right(vals,t)
          lw=pw[p];rw=sw-lw
          if lw<=1e-18 or rw<=1e-18:continue
          le=lw*lw/max(1e-18,pw2[p])
          rw2=pw2[-1]-pw2[p];re=rw*rw/max(1e-18,rw2)
          if le<min_leaf or re<min_leaf:continue
          ly=py[p];ly2=py2[p];ry=sy-ly;ry2=sy2-ly2
          sse=(ly2-ly*ly/lw)+(ry2-ry*ry/rw);gain=base-sse
          if best is None or gain>best[0]:
            best=(gain,j,t,ordered[:p],ordered[p:])
      if best is None or best[0]<=1e-10:return leaf
      _,j,t,li,ri=best
      return {"j":j,"t":t,"n":max(1,int(round(en))),
              "left":node(li,depth-1,False),"right":node(ri,depth-1,False)}
    return node(list(range(len(y))),max_depth,True)

def _tree_pred(t,x):
    n=t
    support=int(n.get("n",1))
    while "leaf" not in n:
      n=n["left"] if x[n["j"]]<=n["t"] else n["right"]
      support=min(support,int(n.get("n",1)))
    return float(n["leaf"]),support

def _boost_train(X,y,idx,rounds=TREE_ROUNDS,lr=.08,max_rows=6500,root_orders=None,
                 max_depth=TREE_DEPTH,min_leaf=28,weights=None):
    if not y:return {"base":0.0,"trees":[],"lr":lr,"sigma":10.0}
    if len(X)!=len(y):
      raise SystemExit("V74 booster X/y length contract failure")
    w=[1.0]*len(y) if weights is None else [max(0.0,float(z)) for z in weights]
    if len(w)!=len(y):raise SystemExit("V74 booster weight length contract failure")
    if len(y)>max_rows:
      if root_orders is not None:
        raise SystemExit("V74 booster root-order/subsample contract failure")
      step=max(1,math.ceil(len(y)/max_rows));X=X[::step];y=y[::step];w=w[::step]
    dim=len(X[0]) if X else 0
    if any(len(x)!=dim for x in X) or any(j<0 or j>=dim for j in idx):
      raise SystemExit("V74 booster feature dimension contract failure")
    if root_orders is not None:
      n=len(X)
      for j in idx:
        oo=root_orders.get(j)
        if oo is None or len(oo)!=n or sorted(oo)!=list(range(n)):
          raise SystemExit("V74 booster root-order index contract failure")
    sw=sum(w)
    if sw<=1e-18:raise SystemExit("V74 booster zero weight mass")
    base=sum(w[i]*y[i] for i in range(len(y)))/sw
    pred=[base]*len(y);trees=[]
    for _ in range(rounds):
      res=[y[i]-pred[i] for i in range(len(y))]
      tr=_tree_fit(X,res,idx,max_depth=max_depth,min_leaf=min_leaf,
                   root_orders=root_orders,weights=w)
      trees.append(tr)
      for i,x in enumerate(X):
        v,_=_tree_pred(tr,x);pred[i]+=lr*v
    resid=[y[i]-pred[i] for i in range(len(y))]
    sig=math.sqrt(sum(w[i]*resid[i]*resid[i] for i in range(len(y)))/sw) if len(resid)>1 else 10.0
    return {"base":base,"trees":trees,"lr":lr,"sigma":max(.05,sig),
            "max_depth":int(max_depth),"min_leaf":int(min_leaf),
            "event_balanced":weights is not None}

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
    # Slot occupancy is an outcome label in training only. Runtime sees only the
    # causal pre-entry x-vector and therefore gets an expected hold, never the
    # realized future hold of the candidate being scored.
    yh=[max(1.0,min(180.0,float(s.get("bars",1) or 1)))/180.0 for s in samples]
    w0=_event_year_balanced_weights(samples)
    X,targets=_fit_view(Xall,[ym,yw,yc,yr,yb,yh,w0],6500)
    ymf,ywf,ycf,yrf,ybf,yhf,wf=targets
    orders=_root_orders(X,idx)
    kw={"rounds":TREE_ROUNDS,"lr":.075,"max_rows":10**9,
        "root_orders":orders,"weights":wf}
    mm=_boost_train(X,ymf,idx,**kw)
    wm=_boost_train(X,ywf,idx,**kw)
    cm=_boost_train(X,ycf,idx,**kw)
    rm=_boost_train(X,yrf,idx,**kw)
    bm=_boost_train(X,ybf,idx,**kw)
    hm=_boost_train(X,yhf,idx,rounds=max(6,TREE_ROUNDS-2),lr=.075,max_rows=10**9,
                    root_orders=orders,weights=wf)
    pm=[_boost_pred(mm,x)[0] for x in Xall];pw=[max(0.0,min(1.0,_boost_pred(wm,x)[0])) for x in Xall]
    return {"idx":idx,"mean":mm,"win":wm,"continuation":cm,"regret":rm,"best":bm,"hold":hm,
            "residuals":_residual_cells(samples,pm,pw)}

def pred_value(md,s):
    mu,s1=_boost_pred(md["mean"],s["x"]);wi,s2=_boost_pred(md["win"],s["x"])
    co,s3=_boost_pred(md["continuation"],s["x"])
    rg,s4=_boost_pred(md["regret"],s["x"]);bp,s5=_boost_pred(md["best"],s["x"])
    hh,s6=_boost_pred(md["hold"],s["x"])
    wi=max(0.0,min(1.0,wi));co=max(0.0,co);rg=max(0.0,rg);bp=max(0.0,min(1.0,bp))
    hold=max(1.0,min(180.0,180.0*float(hh)))
    adds_m=[];adds_w=[];supports=[s1 or 1,s2 or 1,s3 or 1,s4 or 1,s5 or 1,s6 or 1]
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
    # MaxActiveBasket=1: expected slot occupancy is a causal predicted cost.
    slot_cost=.10*math.tanh(hold/60.0)
    admission_score=.55*stop_adv+.75*mu+1.30*wi+.40*lc-.65*rg+.80*bp-slot_cost
    return {"mean":mu,"win":wi,"lcb":lc,"continuation":co,"regret":rg,"best_probability":bp,
            "expected_hold_bars":hold,"stop_advantage":stop_adv,"support":sup,
            "value_score":route_score-.05*math.tanh(hold/60.0),
            "admission_score":admission_score}

def fit_pair(samples,idx=None):
    """Event/year-balanced route ranking with exact streaming subsampling.

    The former implementation materialized every route-difference vector and
    only afterwards kept X[::step] up to 10k rows.  SURVIVAL can create a very
    large pair surface, so most vectors were built just to be discarded.  This
    two-pass implementation first counts legal pair rows, derives the identical
    deterministic step, then constructs only rows that the original slice would
    retain.  Pair order/labels/subsampling are unchanged; statistical weighting
    is corrected so each independent event and each year have equal mass.
    """
    idx=list(idx) if idx is not None else stable_idx(samples,PAIR_KFEAT)
    groups=[];total_rows=0
    for key,ev in grouped_events(samples).items():
      if len(ev)<2:continue
      a=sorted(ev,key=lambda z:(z["base"],z["route"]));n=len(a)
      offs=sorted(set([1,max(1,n//4),max(1,n//2),max(1,(3*n)//4)]))
      groups.append((key,a,offs))
      for i in range(n):
        for off in offs:
          j=(i+off)%n
          if i>=j:continue
          if abs(float(a[i]["y"])-float(a[j]["y"]))<1e-12:continue
          total_rows+=2
    if total_rows<200:return {"valid":False,"idx":idx,"n":total_rows}

    step=max(1,math.ceil(total_rows/10000))
    X=[];yw=[];yd=[];pair_keys=[];row_i=0
    for key,a,offs in groups:
      n=len(a);event_key=(key[0],key[1])
      for i in range(n):
        for off in offs:
          j=(i+off)%n
          if i>=j:continue
          aa,bb=a[i],a[j];delta=float(aa["y"])-float(bb["y"])
          if abs(delta)<1e-12:continue
          take0=(row_i%step)==0;take1=((row_i+1)%step)==0
          if take0 or take1:
            d=[aa["x"][q]-bb["x"][q] for q in idx]
            if take0:
              X.append(d);yw.append(1.0 if delta>0 else 0.0)
              yd.append(max(-4.0,min(4.0,delta)));pair_keys.append(event_key)
            if take1:
              X.append([-z for z in d]);yw.append(0.0 if delta>0 else 1.0)
              yd.append(max(-4.0,min(4.0,-delta)));pair_keys.append(event_key)
          row_i+=2

    pw0=_balanced_weights_from_keys(pair_keys)
    use=list(range(len(idx)))
    Xfit,targets=_fit_view(X,[yw,yd,pw0],7000);ywf,ydf,pwf=targets
    orders=_root_orders(Xfit,use)
    return {"valid":True,"idx":idx,"n":len(X),
            "prestream_pair_rows":total_rows,"stream_step":step,
            "win":_boost_train(Xfit,ywf,use,rounds=PAIR_ROUNDS,lr=.08,max_rows=10**9,
                               root_orders=orders,weights=pwf),
            "delta":_boost_train(Xfit,ydf,use,rounds=PAIR_ROUNDS,lr=.08,max_rows=10**9,
                                 root_orders=orders,weights=pwf)}

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


def meta_lane_decisions(samples,vm):
    """Preserve every source lane through admission.

    Source-native route arbitration already happened in mechanism_decisions().
    The meta layer must therefore score each lane independently and defer the
    MaxActiveBasket=1 cross-source choice until after calibrated admission.
    """
    out=[]
    for s in samples:
      p=pred_value(vm,s)
      q=dict(s);q["pair_advantage"]=0.0
      q["decision_score"]=float(p["admission_score"])
      q["decision_margin"]=0.0
      out.append({"score":float(p["admission_score"]),
                  "route_rank":float(p["value_score"]),
                  "pred":dict(p,pair_advantage=0.0),"s":q})
    return out

def simulate(decisions,th,window=None,stop_margin=-math.inf):
    d=defaultdict(list)
    for e in decisions:
      if window is not None and e["s"]["window"]!=window:continue
      d[(e["s"]["window"],event_identity(e["s"]["setup"]))].append(e)
    sel=[]
    for ev in d.values():
      ev.sort(key=lambda e:(e["s"]["bar"],-e["score"],e["s"]["route"]))
      for e in ev:
        # Explicit causal optimal-stopping gate.  If the current ENTER value does
        # not dominate learned continuation value by the training-only margin,
        # capital waits; a later completed-bar decision may still enter.
        if float(e.get("stop_advantage",math.inf))+1e-12<stop_margin:continue
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
        q=dict(e);q["mechanism"]=src
        # Expected-R and P(win) are already on common physical units. Apply only
        # a training-derived reliability penalty for weak-support mechanism heads.
        rel=float(md.get("reliability",1.0))
        q["score"]=rel*float(e["score"])+(1.0-rel)*float(e["pred"]["lcb"])
        ss=dict(e["s"]);ss["mechanism"]=src;q["s"]=ss
        out.append(q)
    return out

def _consensus_stats(vals):
    z=[float(v) for v in vals if math.isfinite(float(v))]
    if not z:return [0.0,0.0,0.0,0.0]
    mu=sum(z)/len(z)
    sd=statistics.pstdev(z) if len(z)>1 else 0.0
    return [mu,max(z),min(z),sd]


def admission_lane_context(decisions):
    """Attach same-bar cross-source context without discarding any lane."""
    by=defaultdict(list)
    for e in decisions:
      s=e["s"];by[(s["window"],event_identity(s["setup"]),int(s["bar"]))].append(e)
    out=[]
    for vv in by.values():
      srcs={e["s"].get("source") for e in vv}
      scores=[float(e.get("score",-999.0)) for e in vv]
      route_scores=sorted(scores,reverse=True)
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
      ordered=sorted(vv,key=lambda e:(float(e.get("score",-999.0)),
                                      float(e.get("route_rank",-999.0)),
                                      e["s"]["route"]),reverse=True)
      rank={id(e):i for i,e in enumerate(ordered)}
      mx=max(scores) if scores else 0.0
      med0=statistics.median(scores) if scores else 0.0
      for e in vv:
        s=dict(e["s"]);p=e["pred"];sc=float(e.get("score",-999.0))
        rr=float(rank[id(e)])/max(1.0,float(len(vv)-1)) if len(vv)>1 else 0.0
        relative=[
          1.0-rr,
          math.tanh((sc-med0)/1.5),
          math.tanh((sc-mx)/1.5),
          float(p.get("win",0.0)),
          math.tanh(float(p.get("mean",0.0))/2.0),
          math.tanh(float(p.get("lcb",0.0))/2.0)
        ]
        s["admission_consensus"]=consensus
        s["admission_x"]=list(s["x"])+consensus+relative
        q=dict(e);q["s"]=s;q["pre_admission_lane_rank"]=int(rank[id(e)])
        out.append(q)
    return out

def admission_route_representatives(decisions):
    """Compatibility helper for diagnostics that explicitly need one lane/bar."""
    by=defaultdict(list)
    for e in admission_lane_context(decisions):
      s=e["s"];by[(s["window"],event_identity(s["setup"]),int(s["bar"]))].append(e)
    return [max(vv,key=lambda z:(float(z.get("score",-999.0)),
                                 float(z.get("route_rank",-999.0)),
                                 z["s"]["route"])) for vv in by.values()]


def _admission_training_samples(route_decisions,years):
    yy=set(years);out=[]
    for e in admission_lane_context(route_decisions):
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
    """Strict source-native admission; missing source features use source priors.

    No source may silently inherit the GLOBAL runtime head. Stable targets use
    source-specific trees. A target without temporally stable features uses only
    that source's own event/year-balanced empirical prior.
    """
    ss=_admission_training_samples(route_decisions,fit_years)
    if source is not None:ss=[s for s in ss if s.get("source")==source]
    min_rows=180 if source is not None else 500
    if len(ss)<min_rows:return None

    X=[s["x"] for s in ss]
    ye,yd,yr,ya=_optimal_admission_targets(ss)
    idx_enter=stable_idx_target(ss,ye,TREE_KFEAT)
    idx_defer=stable_idx_target(ss,yd,TREE_KFEAT)
    idx_reject=stable_idx_target(ss,yr,TREE_KFEAT)
    idx_adv=stable_idx_target(ss,ya,TREE_KFEAT)

    if source is None:
      missing=[name for name,idx0 in (("ENTER",idx_enter),("DEFER",idx_defer),("REJECT",idx_reject)) if not idx0]
      if missing:raise SystemExit("V74 no temporally stable global admission features for "+",".join(missing))
      if not idx_adv:idx_adv=list(idx_enter)

    w0=_event_year_balanced_weights(ss)
    Xf,targets=_fit_view(X,[ye,yd,yr,ya,w0],6500)
    yef,ydf,yrf,yaf,wf=targets
    valid=[z for z in (idx_enter,idx_defer,idx_reject,idx_adv) if z]
    all_idx=sorted(set(q for z in valid for q in z))
    if not all_idx and source is None:
      raise SystemExit("V74 global admission has no stable features")
    orders=_root_orders(Xf,all_idx) if all_idx else {}

    sw=max(1e-18,sum(w0))
    def wmean(vals):
      return sum(float(v)*float(w) for v,w in zip(vals,w0))/sw
    def prior_binary(vals):
      p=max(0.0,min(1.0,wmean(vals)))
      return {"mean":p,"sigma":math.sqrt(max(1e-9,p*(1.0-p)))}
    def prior_cont(vals):
      mu=wmean(vals)
      var=sum(float(w)*(float(v)-mu)**2 for v,w in zip(vals,w0))/sw
      return {"mean":mu,"sigma":max(.05,math.sqrt(max(0.0,var)))}

    evn=max(1,len({(s["window"],event_identity(s["setup"])) for s in ss}))
    priors={"enter":prior_binary(ye),"defer":prior_binary(yd),
            "reject":prior_binary(yr),"advantage":prior_cont(ya)}
    for q in priors.values():q["support"]=evn

    def fit_head(target,idx0):
      if not idx0:return None
      return _boost_train(Xf,target,idx0,rounds=TREE_ROUNDS,lr=.075,
                          max_rows=10**9,root_orders=orders,weights=wf)

    em=fit_head(yef,idx_enter)
    dm=fit_head(ydf,idx_defer)
    rm=fit_head(yrf,idx_reject)
    am=fit_head(yaf,idx_adv)
    return {"type":"SOURCE_NATIVE_CAUSAL_ADMISSION_WITH_EMPIRICAL_PRIOR_FALLBACK",
            "source":source or "GLOBAL","fit_years":list(fit_years),"idx":all_idx,
            "idx_enter":idx_enter or [],"idx_defer":idx_defer or [],
            "idx_reject":idx_reject or [],"idx_advantage":idx_adv or [],
            "enter":em,"defer":dm,"reject":rm,"advantage":am,
            "priors":priors,"n":len(ss),"event_support":evn,
            "head_origin":{"enter":"TREE" if em is not None else "SOURCE_PRIOR",
                           "defer":"TREE" if dm is not None else "SOURCE_PRIOR",
                           "reject":"TREE" if rm is not None else "SOURCE_PRIOR",
                           "advantage":"TREE" if am is not None else "SOURCE_PRIOR"}}


def fit_admission_bundle(route_decisions,fit_years):
    glob=fit_admission_model(route_decisions,fit_years,None)
    if glob is None:raise SystemExit("V74 insufficient global admission samples")
    active=sorted({e["s"].get("source") for e in admission_lane_context(route_decisions)})
    by={}
    for src in active:
      md=fit_admission_model(route_decisions,fit_years,src)
      if md is None:
        raise SystemExit("V74 source-native admission insufficient support "+str(src))
      by[src]=md
    missing=[src for src in active if src not in by]
    if missing:
      raise SystemExit("V74 source-native admission completeness failure "+",".join(missing))
    return {"type":"STRICT_SOURCE_NATIVE_CAUSAL_ENTER_DEFER_REJECT_BUNDLE",
            "fit_years":list(fit_years),"global_diagnostic_only":glob,
            "by_source":by,"active_sources":active,
            "source_native_complete":True}


def _admission_head_pred(model,name,x):
    md=model.get(name)
    if md is not None:
      p,s=_boost_pred(md,x)
      return float(p),max(1,s or 1),float(md.get("sigma",.10)),"TREE"
    pr=model.get("priors",{}).get(name)
    if pr is None:raise SystemExit("V74 missing source admission prior "+name)
    return float(pr["mean"]),max(1,int(pr.get("support",1))),float(pr.get("sigma",.10)),"SOURCE_PRIOR"

def pred_admission(bundle,e):
    s=e["s"];src=s.get("source")
    model=bundle.get("by_source",{}).get(src)
    if model is None:
      raise SystemExit("V74 runtime missing source-native admission head "+str(src))
    x=s.get("admission_x",s["x"])
    en,s1,se,o1=_admission_head_pred(model,"enter",x)
    de,s2,sd,o2=_admission_head_pred(model,"defer",x)
    re,s3,sr,o3=_admission_head_pred(model,"reject",x)
    ad,s4,sa,o4=_admission_head_pred(model,"advantage",x)
    en=max(0.0,min(1.0,en));de=max(0.0,min(1.0,de));re=max(0.0,min(1.0,re))
    enter_lcb=en-Z*max(.05,se)/math.sqrt(max(1,s1))
    adv_lcb=ad-Z*max(.05,sa)/math.sqrt(max(1,s4))
    return {"enter":en,"enter_lcb":enter_lcb,"defer":de,"reject":re,
            "advantage":ad,"advantage_lcb":adv_lcb,"support":max(1,s1),
            "defer_support":max(1,s2),"reject_support":max(1,s3),
            "advantage_support":max(1,s4),"head_source":model.get("source"),
            "head_origin":{"enter":o1,"defer":o2,"reject":o3,"advantage":o4}}

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

def _precision_rank_cell_keys(s):
    """Most-specific -> global structural cells for hard-negative retrieval."""
    src=str(s.get("source","NONE"));fam=str(s.get("family","NONE"))
    try:bar=max(0,int(s.get("bar",0)))
    except Exception:bar=0
    bb=min(5,bar//15)
    return (
      "SFB|"+src+"|"+fam+"|"+str(bb),
      "SF|"+src+"|"+fam,
      "S|"+src,
      "F|"+fam,
      "ALL"
    )

def _precision_anchor_bank(rows,idx,count=5):
    out={}
    cells=defaultdict(list)
    for s in rows:
      for k in _precision_rank_cell_keys(s):cells[k].append(s)
    for k,v in cells.items():
      if len(v)<4:continue
      out[k]=[[float(s["x"][j]) for j in idx] for s in _contrast_anchor_rows(v,count)]
    return out

def _precision_pair_probability(pair,xx,anchor):
    d=[xx[i]-float(anchor[i]) for i in range(len(xx))]
    fw,s1=_boost_pred(pair,d);bw,s2=_boost_pred(pair,[-v for v in d])
    p=.5*(max(0.0,min(1.0,fw))+(1.0-max(0.0,min(1.0,bw))))
    return p,max(1,min(s1 or 1,s2 or 1))

def fit_contrastive_winner_ranker(route_decisions,fit_years,source=None):
    """Event-balanced hard-negative/listwise Precision@250 retrieval ranker.

    Random global winner/loser pairs were not aligned with V74's deployment
    question.  This version pairs each winning event-bar against structurally
    confusable losing event-bars from the same year, preferring source+family+
    maturity bucket, then source+family/source/family/global fallbacks.

    Every positive harmonic event has equal total pair mass inside a year and
    every training year has equal total mass.  Each year also owns an independent
    pair expert and matched positive/negative anchor banks.  Runtime therefore
    produces a semantically fixed score: higher means the current causal state
    beats matched losers and is less dominated by matched winners.  No burned
    outcome, Validation, Fresh or future bar enters inference.
    """
    ss=_admission_training_samples(route_decisions,fit_years)
    if source is not None:ss=[s for s in ss if s.get("source")==source]
    if len(ss)<500:
      if source is not None:return None
      raise SystemExit("V74 insufficient precision-retrieval samples")
    win=[1.0 if float(s["y"])>0.0 else 0.0 for s in ss]
    idx=stable_idx_target(ss,win,max(TREE_KFEAT,36))
    if not idx:
      if source is not None:return None
      raise SystemExit("V74 no temporally stable precision-retrieval features")
    idx=idx[:36]

    by=defaultdict(list)
    for s in ss:by[s["window"]].append(s)
    allX=[];allY=[];allEvent=[];experts={};pairs_per_year={}
    for w in fit_years:
      ww=by.get(w,[])
      pos=sorted([s for s in ww if float(s["y"])>0.0],
                 key=lambda s:(event_identity(s["setup"]),int(s["bar"]),s["source"],s["route"]))
      neg=sorted([s for s in ww if float(s["y"])<=0.0],
                 key=lambda s:(event_identity(s["setup"]),int(s["bar"]),s["source"],s["route"]))
      if len(pos)<25 or len(neg)<25:continue
      neg_cells=defaultdict(list)
      for n in neg:
        for k in _precision_rank_cell_keys(n):neg_cells[k].append(n)

      X=[];yy=[];event_keys=[];pair_count=0
      # At most three hierarchy levels per positive state; this is bounded and
      # deterministic while deliberately concentrating capacity on hard negatives.
      for pi,p in enumerate(pos):
        used=set()
        for level,k in enumerate(_precision_rank_cell_keys(p)):
          vv=neg_cells.get(k,[])
          if not vv:continue
          ni=(pi*53+level*97+len(vv)//3)%len(vv)
          n=vv[ni]
          nk=(event_identity(n["setup"]),int(n["bar"]),n["route"])
          if nk in used:continue
          used.add(nk)
          d=[float(p["x"][j])-float(n["x"][j]) for j in idx]
          X.append(d);yy.append(1.0);event_keys.append((w,event_identity(p["setup"])))
          X.append([-v for v in d]);yy.append(0.0);event_keys.append((w,event_identity(p["setup"])))
          pair_count+=1
          if len(used)>=3:break
        if pair_count>=1800:break
      if len(X)<300:continue

      # Unit total mass per positive event, then equal year mass.
      ev=defaultdict(list)
      for i,k in enumerate(event_keys):ev[k].append(i)
      weights=[0.0]*len(X)
      for ids in ev.values():
        q=1.0/max(1,len(ids))
        for i in ids:weights[i]=q
      sw=sum(weights);scale=len(weights)/max(1e-18,sw)
      weights=[z*scale for z in weights]

      use=list(range(len(idx)));orders=_root_orders(X,use)
      pair=_boost_train(X,yy,use,rounds=max(10,TREE_ROUNDS),lr=.065,max_rows=10**9,
                        root_orders=orders,max_depth=2,min_leaf=24,weights=weights)
      experts[w]={
        "pair":pair,
        "positive_anchors":_precision_anchor_bank(pos,idx,5),
        "negative_anchors":_precision_anchor_bank(neg,idx,7),
        "n_pos":len(pos),"n_neg":len(neg),"pair_rows":len(X)
      }
      pairs_per_year[w]=pair_count
      # Equal-year global model: normalize each year's pair weight mass.
      ysw=sum(weights)
      yw=[z/max(1e-18,ysw) for z in weights]
      allX.extend(X);allY.extend(yy);allEvent.extend([(w,z) for z in yw])

    min_pair_rows=500 if source is not None else 1000
    if len(experts)<2 or len(allX)<min_pair_rows:
      if source is not None:return None
      raise SystemExit("V74 insufficient hard-negative precision experts")

    # A global fallback sees equal mass from each contributing training year.
    gw=[z for _,z in allEvent];gs=sum(gw);gw=[z*len(gw)/max(1e-18,gs) for z in gw]
    use=list(range(len(idx)));orders=_root_orders(allX,use)
    global_pair=_boost_train(allX,allY,use,rounds=max(10,TREE_ROUNDS),lr=.065,max_rows=10**9,
                             root_orders=orders,max_depth=2,min_leaf=28,weights=gw)
    return {"type":"EVENT_BALANCED_MATCHED_HARD_NEGATIVE_PRECISION_RANKER",
            "source":source or "GLOBAL",
            "fit_years":[w for w in fit_years if w in experts],"idx":idx,
            "global_pair":global_pair,"experts":experts,
            "pairs_per_year":pairs_per_year,"pair_rows":len(allX)}

def pred_contrastive_winner(model,e,max_year_exclusive=None):
    s=e["s"];x=s.get("admission_x",s["x"]);idx=model["idx"]
    xx=[float(x[j]) for j in idx]
    per_year=[];supports=[];details=[]
    for w in model.get("fit_years",[]):
      if max_year_exclusive is not None and int(str(w)[1:])>=int(str(max_year_exclusive)[1:]):continue
      ex=model.get("experts",{}).get(w)
      if not ex:continue
      keys=_precision_rank_cell_keys(s)
      na=None;pa=None;cell=None
      for k in keys:
        n0=ex.get("negative_anchors",{}).get(k)
        p0=ex.get("positive_anchors",{}).get(k)
        if n0 and p0:
          na=n0;pa=p0;cell=k;break
      if not na:
        na=ex.get("negative_anchors",{}).get("ALL",[])
      if not pa:
        pa=ex.get("positive_anchors",{}).get("ALL",[])
      if not na or not pa:continue

      pair=ex.get("pair",model["global_pair"])
      beat_neg=[]
      for a in na:
        p0,sup=_precision_pair_probability(pair,xx,a);beat_neg.append(p0);supports.append(sup)
      # "not dominated by a known winner" is a second listwise coordinate.
      survive_pos=[]
      for a in pa:
        p0,sup=_precision_pair_probability(pair,a,xx)
        survive_pos.append(1.0-p0);supports.append(sup)
      bn=sum(beat_neg)/len(beat_neg);sp=sum(survive_pos)/len(survive_pos)
      score=.72*bn+.28*sp
      per_year.append(score)
      details.append({"year":w,"cell":cell or "ALL","beat_negative":bn,
                      "survive_positive":sp,"score":score})
    if not per_year:
      return {"score":-999.0,"q25":0.0,"median":0.0,"minimum":0.0,
              "dispersion":1.0,"per_year":[],"support":0,"details":[]}
    z=sorted(per_year);q25=z[int(math.floor(.25*(len(z)-1)))]
    return {"score":q25,"q25":q25,"median":statistics.median(per_year),
            "minimum":min(per_year),
            "dispersion":statistics.pstdev(per_year) if len(per_year)>1 else 0.0,
            "per_year":per_year,
            "support":max(1,min(supports)) if supports else 1,
            "details":details}


def fit_source_precision_bundle(route_decisions,fit_years):
    """R6 source-native hard-negative retrieval with hierarchical fallback.

    Each sufficiently supported source receives its own stable-feature pair
    ranker.  The global ranker is retained only as a shrinkage/fallback prior
    for genuinely low-support sources; SURVIVAL is fail-closed whenever it has
    enough rows to deserve an independent model.
    """
    glob=fit_contrastive_winner_ranker(route_decisions,fit_years,None)
    ss=_admission_training_samples(route_decisions,fit_years)
    active=sorted({s.get("source","NONE") for s in ss})
    counts=Counter(s.get("source","NONE") for s in ss)
    by={}
    for src in active:
        md=fit_contrastive_winner_ranker(route_decisions,fit_years,src)
        if md is not None:by[src]=md
    if counts.get("SURVIVAL",0)>=500 and "SURVIVAL" in active and "SURVIVAL" not in by:
        raise SystemExit("V74-R6 SURVIVAL has support but no source-native precision ranker")
    return {"type":"R6_SOURCE_NATIVE_HARD_NEGATIVE_PRECISION_BUNDLE",
            "fit_years":list(fit_years),"global_prior_ranker":glob,
            "by_source":by,"source_counts":dict(counts),
            "independent_sources":sorted(by)}

def pred_source_precision(bundle,e,max_year_exclusive=None):
    src=e["s"].get("source","NONE")
    md=bundle.get("by_source",{}).get(src)
    origin="SOURCE_NATIVE"
    if md is None:
        md=bundle["global_prior_ranker"];origin="HIERARCHICAL_GLOBAL_PRIOR"
    z=dict(pred_contrastive_winner(md,e,max_year_exclusive=max_year_exclusive))
    z["ranker_origin"]=origin;z["ranker_source"]=md.get("source","GLOBAL")
    z["requested_source"]=src
    return z

def _r6_calibration_stats(rows):
    """Event/year-balanced probability and R moments for calibration cells."""
    if not rows:
        return {"p":.5,"mean_r":0.0,"sd_r":2.0,"event_support":0,"row_support":0}
    per_event=Counter((r["window"],r["event"]) for r in rows)
    events_by_year=defaultdict(set)
    for r in rows:events_by_year[r["window"]].add(r["event"])
    ww=[]
    for r in rows:
        ek=(r["window"],r["event"])
        den=max(1,len(events_by_year[r["window"]]))*max(1,per_event[ek])
        ww.append(1.0/den)
    sw=max(1e-18,sum(ww))
    p=sum(w*float(r["win"]) for w,r in zip(ww,rows))/sw
    mu=sum(w*float(r["y"]) for w,r in zip(ww,rows))/sw
    sec=sum(w*float(r["y"])*float(r["y"]) for w,r in zip(ww,rows))/sw
    sd=math.sqrt(max(1e-9,sec-mu*mu))
    return {"p":max(0.0,min(1.0,p)),"mean_r":mu,"sd_r":sd,
            "event_support":len(per_event),"row_support":len(rows)}

def _r6_shrink_stats(obs,prior,k):
    if prior is None or float(k)<=0:return dict(obs)
    n=max(0.0,float(obs.get("event_support",0)));k=float(k);d=max(1e-9,n+k)
    p=(n*float(obs["p"])+k*float(prior["p"]))/d
    mu=(n*float(obs["mean_r"])+k*float(prior["mean_r"]))/d
    so=float(obs["sd_r"])**2+float(obs["mean_r"])**2
    sp=float(prior["sd_r"])**2+float(prior["mean_r"])**2
    sec=(n*so+k*sp)/d
    q=dict(obs);q.update({"p":max(0.0,min(1.0,p)),"mean_r":mu,
                          "sd_r":math.sqrt(max(1e-9,sec-mu*mu)),
                          "effective_support":d})
    return q

def _r6_build_calibration_bank(rows,global_prior=None):
    vals=[float(r["score"]) for r in rows if math.isfinite(float(r["score"]))]
    prior=_r6_calibration_stats(rows)
    if global_prior is not None:
        prior=_r6_shrink_stats(prior,global_prior,24.0)
    if not vals:
        return {"cuts":[],"prior":prior,"cells":{},"rows":0}
    cuts=sorted(set(qtile(vals,q) for q in (.12,.25,.40,.55,.70,.82,.92)))
    cells={}
    for b in range(len(cuts)+1):
        rr=[r for r in rows if bisect.bisect_right(cuts,float(r["score"]))==b]
        if not rr:continue
        obs=_r6_calibration_stats(rr)
        # Bin estimates are deliberately shrunk to the source prior; this is the
        # hierarchical theta_s = theta_global + Delta_s layer.
        cells[str(b)]=_r6_shrink_stats(obs,prior,18.0)
    return {"cuts":cuts,"prior":prior,"cells":cells,"rows":len(rows)}

def _fit_r6_common_calibrator(route_decisions,precision_bundle,fit_years):
    """Forward-OOF source calibration onto one comparable capital scale.

    For a row in year Y, only independent ranker experts from years <Y may
    produce its calibration score.  The final source-native ranker can therefore
    be refit on all training years without calibrating on its own fitted labels.
    """
    reps=admission_lane_context(route_decisions);rows=[]
    yy=set(fit_years)
    for e in reps:
        s=e["s"];w=s["window"]
        if w not in yy:continue
        z=pred_source_precision(precision_bundle,e,max_year_exclusive=w)
        if int(z.get("support",0))<=0 or not math.isfinite(float(z.get("score",-999.0))):continue
        rows.append({"window":w,"event":event_identity(s["setup"]),
                     "source":s.get("source","NONE"),"score":float(z["score"]),
                     "win":1.0 if float(s["y"])>0.0 else 0.0,"y":float(s["y"])})
    if len(rows)<250:
        raise SystemExit("V74-R6 insufficient forward-OOF calibration rows")
    global_bank=_r6_build_calibration_bank(rows,None)
    by={};counts=Counter(r["source"] for r in rows)
    for src in sorted(counts):
        rr=[r for r in rows if r["source"]==src]
        if len(rr)>=60:
            by[src]=_r6_build_calibration_bank(rr,global_bank["prior"])
    return {"type":"R6_FORWARD_OOF_SOURCE_TO_COMMON_CAPITAL_CALIBRATOR",
            "fit_years":list(fit_years),"global":global_bank,"by_source":by,
            "forward_oof_rows":len(rows),"source_rows":dict(counts),
            "future_year_experts_forbidden":True}

def _pred_r6_common_calibrator(cal,precision_bundle,e):
    z=pred_source_precision(precision_bundle,e)
    src=e["s"].get("source","NONE")
    bank=cal.get("by_source",{}).get(src)
    cal_origin="SOURCE_NATIVE"
    if bank is None:
        bank=cal["global"];cal_origin="HIERARCHICAL_GLOBAL_PRIOR"
    raw=float(z.get("score",-999.0));cuts=bank.get("cuts",[])
    b=bisect.bisect_right(cuts,raw)
    cell=bank.get("cells",{}).get(str(b),bank.get("prior",{}))
    p=max(0.0,min(1.0,float(cell.get("p",.5))))
    mu=float(cell.get("mean_r",0.0));sd=max(.05,float(cell.get("sd_r",2.0)))
    n=max(1.0,float(cell.get("effective_support",cell.get("event_support",1))))
    win_lcb=_r4_wilson_lcb(p,n)
    mean_lcb=mu-Z*sd/math.sqrt(n)
    pct=(float(b)+.5)/max(1.0,float(len(cuts)+1))
    fallback=(1.0 if z.get("ranker_origin")!="SOURCE_NATIVE" else 0.0)+(
              1.0 if cal_origin!="SOURCE_NATIVE" else 0.0)
    dispersion=max(0.0,float(z.get("dispersion",0.0)))
    mean_quality=.5+.5*math.tanh(mean_lcb/1.25)
    mean_level=.5+.5*math.tanh(mu/1.50)
    # Gate priorities are encoded ex ante: winner purity dominates; Expected-R
    # lower bound and level break ties; uncertainty/fallbacks are penalized.
    utility=(.82*win_lcb+.12*mean_quality+.04*mean_level+.02*pct
             -.025*fallback-.035*dispersion)
    return {"raw_rank":raw,"ranker":z,"win_p":p,"win_lcb":win_lcb,
            "mean_r":mu,"mean_lcb":mean_lcb,"sd_r":sd,"effective_n":n,
            "percentile":pct,"utility":utility,"calibration_origin":cal_origin,
            "fallback_penalty":fallback,"dispersion":dispersion}


# ---------------------------------------------------------------------------
# V74-R8: source-native local matched-counterfactual admission.
#
# R7 proved that adding a richer trajectory vector to a global/semi-global
# function approximator does not create winner purity.  R8 changes the
# statistical problem instead: estimate conditional risk inside multiple small
# historical cohorts that match source/family/action/route/regime and a sparse
# quantile hash of the *current completed-bar causal state*.  Every cell is
# event/year balanced, shrunk to its own source prior and pooled conservatively
# across independently chosen subspaces.  This is a causal retrieval estimator,
# not a future-outcome oracle; burned/test outcomes are never used to fit cells,
# cuts, feature indices, thresholds, or source allocation.
# ---------------------------------------------------------------------------

R8_MAX_FEATURES=18
R8_SUBSPACES=7
R8_CELL_MIN_SUPPORT=18
R8_CELL_SHRINK=24.0

def _r8_cell_stats(rr,prior=None,shrink=R8_CELL_SHRINK):
    if not rr:
        return {"p":.5,"win_lcb":0.0,"mean_r":0.0,"mean_lcb":-999.0,
                "sd_r":2.0,"event_support":0,"year_support":0,
                "p_q25":0.0,"mean_q25":-999.0,"year_dispersion":1.0}
    per_event=Counter((r["window"],event_identity(r["setup"])) for r in rr)
    events_by_year=defaultdict(set)
    for r in rr:events_by_year[r["window"]].add(event_identity(r["setup"]))
    ww=[]
    for r in rr:
        ek=(r["window"],event_identity(r["setup"]))
        den=max(1,len(events_by_year[r["window"]]))*max(1,per_event[ek])
        ww.append(1.0/den)
    sw=max(1e-18,sum(ww))
    p=sum(w*(1.0 if float(r["y"])>0.0 else 0.0) for w,r in zip(ww,rr))/sw
    mu=sum(w*float(r["y"]) for w,r in zip(ww,rr))/sw
    sec=sum(w*float(r["y"])*float(r["y"]) for w,r in zip(ww,rr))/sw
    by_year=defaultdict(list)
    for r in rr:by_year[r["window"]].append(r)
    yp=[];ym=[]
    for w,z in sorted(by_year.items()):
        pev=Counter(event_identity(q["setup"]) for q in z)
        zw=[1.0/max(1,pev[event_identity(q["setup"])]) for q in z]
        zsw=max(1e-18,sum(zw))
        yp.append(sum(a*(1.0 if float(q["y"])>0.0 else 0.0) for a,q in zip(zw,z))/zsw)
        ym.append(sum(a*float(q["y"]) for a,q in zip(zw,z))/zsw)
    pq=_q25_safe(yp,p);mq=_q25_safe(ym,mu)
    disp=statistics.pstdev(yp) if len(yp)>1 else 0.0
    n=float(len(per_event));k=float(shrink if prior is not None else 0.0)
    if prior is not None:
        pp=float(prior.get("p",.5));pm=float(prior.get("mean_r",0.0));ps=float(prior.get("sd_r",2.0))
        p=(n*p+k*pp)/max(1e-9,n+k)
        sec=(n*sec+k*(ps*ps+pm*pm))/max(1e-9,n+k)
        mu=(n*mu+k*pm)/max(1e-9,n+k)
    sd=math.sqrt(max(1e-9,sec-mu*mu))
    en=max(1.0,n+k)
    robust_p=max(0.0,min(1.0,.70*p+.30*pq))
    robust_mu=.70*mu+.30*mq
    return {"p":p,"win_lcb":_r4_wilson_lcb(robust_p,en),
            "mean_r":mu,"mean_lcb":robust_mu-Z*sd/math.sqrt(en),
            "sd_r":sd,"event_support":int(n),"effective_n":en,
            "year_support":len(by_year),"p_q25":pq,"mean_q25":mq,
            "year_dispersion":disp}

def _r8_feature_union(ss):
    p=len(ss[0]["x"]) if ss else 0
    if p<=0:return []
    yw=[1.0 if float(z["y"])>0.0 else 0.0 for z in ss]
    ys=[1.0 if float(z["y"])>=1.0 else 0.0 for z in ss]
    yr=[(max(-1.0,min(2.5,float(z["y"])))+1.0)/3.5 for z in ss]
    banks=[
      stable_idx_target(ss,yw,min(12,p)),
      stable_idx_target(ss,ys,min(10,p)),
      stable_idx_target(ss,yr,min(10,p)),
      stable_idx(ss,min(12,p))
    ]
    out=[]
    for b in banks:
        for j in b:
            if j not in out:out.append(j)
            if len(out)>=min(R8_MAX_FEATURES,p):return out
    return out

def _r8_bin(cuts,v):
    return bisect.bisect_right(cuts,float(v))

def _r8_cat_key(level,s):
    src=str(s.get("source","NONE"));fam=str(s.get("family","NONE"))
    act=str(s.get("action","NONE"));route=str(s.get("route","NONE"))
    rid=int(s.get("regime_id",0))
    if level=="route_regime":return (src,fam,act,route,rid)
    if level=="family_regime":return (src,fam,act,rid)
    if level=="family_action":return (src,fam,act)
    if level=="family":return (src,fam)
    return (src,)

def _fit_r8_source_matcher(stage_samples,years,src):
    yy=set(years)
    ss=[z for z in stage_samples if z["window"] in yy and z.get("source")==src]
    evn=len({(z["window"],event_identity(z["setup"])) for z in ss})
    if len(ss)<240 or evn<120:return None
    idx=_r8_feature_union(ss)
    if len(idx)<4:return None
    cuts={}
    for j in idx:
        vals=[float(z["x"][j]) for z in ss if math.isfinite(float(z["x"][j]))]
        cuts[str(j)]=sorted(set(qtile(vals,q) for q in (.20,.40,.60,.80))) if vals else []
    m=min(len(idx),12)
    pairs=[]
    for i in range(min(R8_SUBSPACES,m)):
        a=idx[i]
        b=idx[(i+3)%m] if m>1 else idx[i]
        c=idx[(i+7)%m] if m>2 else b
        q=[]
        for z in (a,b,c):
            if z not in q:q.append(z)
        pairs.append(q[:3])
    prior=_r8_cell_stats(ss,None,0.0)
    levels=("route_regime","family_regime","family_action","family")
    raw={lvl:[defaultdict(list) for _ in pairs] for lvl in levels}
    for z in ss:
        for qi,sub in enumerate(pairs):
            sig=tuple(_r8_bin(cuts[str(j)],z["x"][j]) for j in sub)
            for lvl in levels:
                k=str((_r8_cat_key(lvl,z),sig))
                raw[lvl][qi][k].append(z)
    banks={lvl:[] for lvl in levels}
    for lvl in levels:
        for qbank in raw[lvl]:
            dst={}
            for k,rr in qbank.items():
                st=_r8_cell_stats(rr,prior,R8_CELL_SHRINK)
                if st["event_support"]>=8 and st["year_support"]>=2:dst[k]=st
            banks[lvl].append(dst)
    return {"type":"R8_SOURCE_NATIVE_MATCHED_COUNTERFACTUAL",
            "source":src,"fit_years":list(years),"idx":idx,
            "cuts":cuts,"subspaces":pairs,"levels":list(levels),
            "prior":prior,"banks":banks,"rows":len(ss),"event_support":evn,
            "min_support":R8_CELL_MIN_SUPPORT,"shrink":R8_CELL_SHRINK}

def fit_r8_local_matcher(stage_samples,years):
    active=sorted({z.get("source","NONE") for z in stage_samples if z["window"] in set(years)})
    by={}
    for src in active:
        md=_fit_r8_source_matcher(stage_samples,years,src)
        if md is not None:by[src]=md
    if "SURVIVAL" in active and "SURVIVAL" not in by:
        raise SystemExit("V74-R8 SURVIVAL has OOF support but no matched-counterfactual head")
    if not by:raise SystemExit("V74-R8 no source-native matched-counterfactual heads")
    return {"type":"R8_LOCAL_MATCHED_COUNTERFACTUAL_BUNDLE",
            "fit_years":list(years),"by_source":by,
            "independent_sources":sorted(by),"future_information_used":False,
            "burned_outcomes_used_for_fit":False}

def _pred_r8_local_matcher(bundle,e):
    s=e["s"];src=s.get("source","NONE")
    md=bundle.get("by_source",{}).get(src)
    if md is None:
        return {"p":0.0,"win_lcb":-1.0,"mean_r":-9.0,"mean_lcb":-9.0,
                "utility":-1.0,"support":0.0,"matched_cells":0,
                "dispersion":1.0,"match_depth":0.0,"origin":"NO_SOURCE_HEAD"}
    x=s["x"];picked=[];depths=[]
    depth={"route_regime":1.0,"family_regime":.82,"family_action":.66,"family":.50}
    for qi,sub in enumerate(md["subspaces"]):
        sig=tuple(_r8_bin(md["cuts"].get(str(j),[]),x[j]) for j in sub)
        got=None;gd=0.0
        for lvl in md["levels"]:
            k=str((_r8_cat_key(lvl,s),sig))
            q=md["banks"][lvl][qi].get(k)
            if q is None:continue
            if int(q.get("event_support",0))<int(md["min_support"]):continue
            if int(q.get("year_support",0))<2:continue
            got=q;gd=depth[lvl];break
        if got is not None:
            picked.append(got);depths.append(gd)
    if not picked:
        q=md["prior"];picked=[q];depths=[.20]
        origin="SOURCE_PRIOR"
    else:origin="MATCHED_COHORT"
    pp=sorted(float(q["p"]) for q in picked)
    wl=sorted(float(q["win_lcb"]) for q in picked)
    mm=sorted(float(q["mean_r"]) for q in picked)
    ml=sorted(float(q["mean_lcb"]) for q in picked)
    nn=sorted(float(q.get("event_support",0)) for q in picked)
    dd=[float(q.get("year_dispersion",0.0)) for q in picked]
    p=statistics.median(pp);win_lcb=wl[int(math.floor(.25*(len(wl)-1)))]
    mu=statistics.median(mm);mean_lcb=ml[int(math.floor(.25*(len(ml)-1))]
    support=statistics.median(nn);disp=statistics.median(dd)
    mdp=sum(depths)/len(depths)
    mean_quality=.5+.5*math.tanh(mean_lcb/1.25)
    support_quality=min(1.0,support/80.0)
    # Precision is the hard bottleneck: conservative P(win) LCB dominates.
    # Mean-R LCB, match specificity and support are secondary; temporal
    # dispersion is explicitly penalized to reject regime-fragile cells.
    utility=(.76*win_lcb+.14*mean_quality+.055*mdp+.045*support_quality
             -.075*disp)
    return {"p":p,"win_lcb":win_lcb,"mean_r":mu,"mean_lcb":mean_lcb,
            "utility":utility,"support":support,"matched_cells":len(picked),
            "dispersion":disp,"match_depth":mdp,"origin":origin}


R6_SEMANTIC_SCORE_MODES=(
  "R6_COMMON_UTILITY",
  "R6_WIN_LCB",
  "R6_WIN_PROB",
  "R6_MEAN_LCB",
  "R6_UTILITY_PLUS_STOP",
  "R8_MATCHED_UTILITY",
  "R8_MATCHED_WIN_LCB",
  "R8_MATCHED_MEAN_LCB"
)

def _r6_arbitrate(scored_lanes,mode):
    by=defaultdict(list)
    for e in scored_lanes:
        bank=e.get("pred",{}).get("semantic_scores",{})
        if mode not in bank:raise SystemExit("V74-R6 missing semantic score "+str(mode))
        q=dict(e);q["score"]=float(bank[mode])
        q["pred"]=dict(e["pred"],score_mode=mode,score_orientation=1.0)
        s=q["s"];by[(s["window"],event_identity(s["setup"]),int(s["bar"]))].append(q)
    out=[]
    for vv in by.values():
        out.append(max(vv,key=lambda e:(float(e["score"]),
            float(e["pred"].get("r6_win_lcb",-999.0)),
            float(e["pred"].get("r6_mean_lcb",-999.0)),
            float(e["pred"].get("r6_source_precision",{}).get("score",-999.0)),
            e["s"]["route"])))
    return out


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
      # A lane with one canonical legal route (currently FAILURE|FC230) has no
      # meaningful within-lane pairwise comparisons.  That is not evidence that
      # the lane is invalid. event_decisions()/pair_pref() already treat an
      # invalid pair ranker as zero pair advantage, so retain the value expert.
      years=sorted({s["window"] for s in ss})
      raw_counts={w:sum(1 for s in ss if s["window"]==w) for w in years}
      event_counts={w:len({event_identity(s["setup"]) for s in ss if s["window"]==w}) for w in years}
      # Reliability measures independent causal support, not how many route
      # hypotheses an event happens to expand into.  This removes the former
      # structural penalty on single-route FAILURE and the artificial advantage
      # of dense EARLY/SURVIVAL lattices.
      reliability=min(1.0,min(event_counts.values())/float(MIN_N)) if event_counts else 0.0
      heads[src]={"value_model":vm,"pairwise_ranker":pm,"reliability":reliability,
                  "n":len(ss),"year_counts":raw_counts,"year_event_counts":event_counts}
      training[src]={"n":len(ss),"reliability":reliability,
                     "year_event_counts":event_counts,
                     "selected_features":len(vm.get("idx",[])),
                     "pairwise_n":pm.get("n",0),
                     "pairwise_prestream_n":pm.get("prestream_pair_rows",pm.get("n",0)),
                     "pairwise_stream_step":pm.get("stream_step",1)}
    if not heads:raise SystemExit("V74 no valid mechanism-native heads")
    required=[src for src in SOURCES
              if len({(s["window"],event_identity(s["setup"])) for s in by_source.get(src,[])})>=MIN_N]
    missing=[src for src in required if src not in heads]
    if missing:
      raise SystemExit("V74 unified-lane expert completeness failure "+",".join(missing))
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

def _market_regime_key(s):
    """Causal discrete regime cell from pre-entry HCOG telemetry only."""
    row=s.get("row",{});x=list(row.get("features",[]))
    def g(i,d=0.0):
        try:return float(x[i])
        except:return d
    atrp=max(0.0,min(1.0,g(26,.5)))
    vol="VL" if atrp<.25 else "VM" if atrp<.70 else "VH"
    transition="T1" if g(29,0.0)>=.5 else "T0"
    ts=abs(g(9,0.0));trend="R" if ts<.25 else "M" if ts<.60 else "S"
    mt=g(11,0.0);mtf="C" if mt<-.15 else "N" if mt<.20 else "A"
    return "|".join((vol,transition,trend,mtf))

def _fit_struct_prior(samples,shrink=36.0):
    """Year-robust hierarchical Beta-like causal prior with regime adaptation.

    Regime is computed only from completed pre-entry telemetry. Per-year cell
    rates are shrunk to that year's global rate, then pooled by lower-quartile
    robustness so one favourable regime/year cannot dominate deployment.
    """
    yrs=sorted({s["window"] for s in samples});by=defaultdict(list)
    for s in samples:by[s["window"]].append(s)
    names=("source","family","source_family","source_action",
           "regime","family_regime","source_regime",
           "survival_route","survival_family_route","survival_regime_route")
    banks={k:defaultdict(list) for k in names};globals_=[]
    for w in yrs:
      ww=by[w]
      # Jeffreys-style 0.5/0.5 stabilization before hierarchical shrinkage.
      gp=(sum(float(s["y"])>0.0 for s in ww)+.5)/(len(ww)+1.0);globals_.append(gp)
      loc={k:defaultdict(list) for k in banks}
      for s in ww:
        z=1.0 if float(s["y"])>0.0 else 0.0
        src=s["source"];fam=s["family"];act=s["action"];reg=_market_regime_key(s)
        loc["source"][src].append(z);loc["family"][fam].append(z)
        loc["source_family"][str((src,fam))].append(z)
        loc["source_action"][str((src,act))].append(z)
        loc["regime"][reg].append(z)
        loc["family_regime"][str((fam,reg))].append(z)
        loc["source_regime"][str((src,reg))].append(z)
        if src=="SURVIVAL":
          rt=_sf_key(s)
          loc["survival_route"][rt].append(z)
          loc["survival_family_route"][str((fam,rt))].append(z)
          loc["survival_regime_route"][str((reg,rt))].append(z)
      for name,d in loc.items():
        for k,v in d.items():
          # posterior-like shrink to year-global; no test-year outcome involved
          banks[name][k].append((sum(v)+float(shrink)*gp)/(len(v)+float(shrink)))
    fb=_q25_safe(globals_,.5)
    return {"fallback":fb,**{name:{k:_q25_safe(v,fb) for k,v in d.items()} for name,d in banks.items()}}

def _pred_struct_prior(pr,s):
    fb=float(pr.get("fallback",.5));src=s.get("source","NONE");fam=s.get("family","NONE");act=s.get("action","NONE")
    reg=_market_regime_key(s)
    vals=[
      pr.get("source",{}).get(src),
      pr.get("family",{}).get(fam),
      pr.get("source_family",{}).get(str((src,fam))),
      pr.get("source_action",{}).get(str((src,act))),
      pr.get("regime",{}).get(reg),
      pr.get("family_regime",{}).get(str((fam,reg))),
      pr.get("source_regime",{}).get(str((src,reg))),
      pr.get("survival_route",{}).get(_sf_key(s)) if src=="SURVIVAL" else None,
      pr.get("survival_family_route",{}).get(str((fam,_sf_key(s)))) if src=="SURVIVAL" else None,
      pr.get("survival_regime_route",{}).get(str((reg,_sf_key(s)))) if src=="SURVIVAL" else None
    ]
    z=[float(x) for x in vals if x is not None]
    if not z:return fb
    # Robust harmonic mean penalizes a weak regime-specific component more than
    # an arithmetic average while remaining bounded and monotone.
    eps=1e-6
    hm=len(z)/sum(1.0/max(eps,min(1.0,x)) for x in z)
    return .65*hm+.35*(sum(z)/len(z))

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

def _predict_structural_bank(models,reps):
    """Predict many structural heads with exact booster-output reuse."""
    if not models:return {}
    first=next(iter(models.values()))
    prior_vals=[_pred_struct_prior(first["prior"],e["s"]) for e in reps]
    booster_cache={}
    out={}
    for key,md in models.items():
        wk=id(md["win"]);ak=id(md["aux"])
        if wk not in booster_cache:
            booster_cache[wk]=[max(0.0,min(1.0,_boost_pred(md["win"],e["s"].get("admission_x",e["s"]["x"]))[0]))
                               for e in reps]
        if ak not in booster_cache:
            booster_cache[ak]=[max(0.0,min(1.0,_boost_pred(md["aux"],e["s"].get("admission_x",e["s"]["x"]))[0]))
                               for e in reps]
        pw=booster_cache[wk];pa=booster_cache[ak]
        out[key]=[(pw[i],pa[i],prior_vals[i]) for i in range(len(reps))]
    return out

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
      model_cache={};fold_models={}
      for si,spec in enumerate(specs):
        md=_fit_structural_head(tr_adm,spec,fit_ctx,model_cache)
        if md is None:raise SystemExit("V74 structural head fit failure "+str(spec["id"]))
        fold_models[str(si)]=md
      fold_pred=_predict_structural_bank(fold_models,va_reps)
      for si in range(len(specs)):
        bank_chunks[si].extend(fold_pred[str(si)])
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
    predicted=_predict_structural_bank(heads,full_reps)
    full_bank=[]
    for mid in range(len(specs)):
      if str(mid) in predicted:full_bank.append(predicted[str(mid)])
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
    predicted=_predict_structural_bank(heads,reps)
    bank=[]
    for mid in range(len(specs)):
      bank.append(predicted.get(str(mid),[(.5,.5,.5)]*len(reps)))
    scores=_struct_scores(bank,model["config"]);out=[]
    for i,e in enumerate(reps):
      q=dict(e);q["score"]=scores[i];q["pred"]=dict(e["pred"],structural_admission_score=scores[i])
      out.append(q)
    return out


# ---------------------------------------------------------------------------
# V74 Harmonic Survival State-Space Alpha V1
# ---------------------------------------------------------------------------
# Root-cause rearchitecture.  Harmonic completion remains the setup identity;
# capital admission is learned only from the empirically feasible SURVIVAL lane.
# EARLY/LATE/FAILURE remain in telemetry as shadow mechanisms and are never
# blanket-blacklisted from future research.  All inputs are completed-bar causal.

_SURVIVAL_CORE_FEATURES=(0,1,2,3,4,6,7,8,9,10,11,12,13,14,15,16,19,21,23,24,25,26,27,28,29,30,
                         32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52)
_SURVIVAL_STATE_FEATURES=(5,6,7,12,13,14,15,16,17,18,19,20,21,24,25,26,27,28,29,30,31,32,33,34,
                          35,36,37,38,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,
                          64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79)

def _sf_key(s):
    b=str(s.get("base",""))
    return b[len("SURVIVAL_"):] if b.startswith("SURVIVAL_") else str(s.get("route","")).split("|")[-1]

def _sf_route_coordinates(key):
    parts=str(key).split("_")
    try:r=float(parts[0][1:])/100.0
    except:r=.50
    try:f=float(parts[1][1:])/1000.0
    except:f=.50
    try:rr=float(parts[2][2:])/10.0
    except:rr=2.30
    c1=1.0 if str(key).endswith("_C1") else 0.0
    # Continuous Fibonacci coordinates replace the former 80-way one-hot
    # representation inside the primary Alpha model.  Smooth polynomial/Fourier
    # terms preserve neighbourhood structure: F382 is closer to F500 than F786.
    return [r,f,rr,c1,r*f,r*r,f*f,abs(f-.618),abs(f-.500),
            math.sin(math.pi*f),math.cos(math.pi*f),rr-2.30,c1*f,c1*r]

_REGIME_PROTOTYPES=(
    (.15,.20,.05,.35), # calm/range
    (.30,.50,.10,.45), # active/range
    (.75,.55,.05,.75), # directional trend
    (.55,.62,.95,.50), # transition
    (.65,.90,.70,.35), # shock/high vol
)

def _norm_prob(v):
    s=sum(max(0.0,float(x)) for x in v)
    if s<=1e-18:return [1.0/len(v)]*len(v)
    return [max(0.0,float(x))/s for x in v]

def _regime_emission(state):
    z=list(state or [])
    def g(i,d=.0):
        try:return float(z[i])
        except:return d
    # All four coordinates are completed-bar observables from V74RouteStateFeatures.
    obs=(g(16,.5),g(19,.5),g(21,0.0),g(35,.5))
    sig=.30
    raw=[math.exp(-sum((obs[j]-p[j])**2 for j in range(4))/(2.0*sig*sig))
         for p in _REGIME_PROTOTYPES]
    return _norm_prob(raw)

def _regime_forward(maturity,entry):
    """Two-observation forward-only latent-state filter; never future-smoothed."""
    p0=_regime_emission(maturity)
    trans_obs=0.0
    try:trans_obs=float((maturity or [])[21])
    except:pass
    stay=.80-.20*max(0.0,min(1.0,trans_obs))
    k=len(p0);pred=[]
    for j in range(k):
        v=0.0
        for i in range(k):
            tij=stay if i==j else (1.0-stay)/(k-1)
            v+=p0[i]*tij
        pred.append(v)
    e1=_regime_emission(entry)
    p1=_norm_prob([pred[i]*e1[i] for i in range(k)])
    def ent(p):
        return -sum(x*math.log(max(x,1e-15)) for x in p)/math.log(len(p))
    change=sum(abs(p1[i]-p0[i]) for i in range(k))/2.0
    return p0+p1+[ent(p0),ent(p1),change,max(p1)]

def _mat_inverse(a):
    n=len(a);m=[list(map(float,a[i]))+[1.0 if i==j else 0.0 for j in range(n)] for i in range(n)]
    for col in range(n):
        piv=max(range(col,n),key=lambda r:abs(m[r][col]))
        if abs(m[piv][col])<1e-12:return None
        m[col],m[piv]=m[piv],m[col]
        d=m[col][col];m[col]=[x/d for x in m[col]]
        for r in range(n):
            if r==col:continue
            q=m[r][col]
            if abs(q)>1e-18:m[r]=[m[r][j]-q*m[col][j] for j in range(2*n)]
    return [row[n:] for row in m]

def _fit_family_manifold(samples):
    """Training-only 5D Fibonacci residual covariance with shrinkage/ridge."""
    by=defaultdict(list);allr=[]
    for s in samples:
        r=list(_precision_vector(s["row"])[:5]);by[s["family"]].append(r);allr.append(r)
    def fit(v):
        if not v:return [[1.0 if i==j else 0.0 for j in range(5)] for i in range(5)]
        n=len(v);cov=[[sum(x[i]*x[j] for x in v)/n for j in range(5)] for i in range(5)]
        lam=.30
        for i in range(5):
            for j in range(5):
                if i!=j:cov[i][j]*=(1.0-lam)
            cov[i][i]=max(1e-5,cov[i][i]+1e-4)
        inv=_mat_inverse(cov)
        return inv or [[1.0 if i==j else 0.0 for j in range(5)] for i in range(5)]
    glob=fit(allr)
    return {"global":glob,"family":{fam:fit(v if len(v)>=24 else allr) for fam,v in by.items()}}

def _manifold_features(s,manifold):
    r=list(_precision_vector(s["row"])[:5])
    inv=manifold.get("family",{}).get(s["family"],manifold["global"])
    q=[sum(inv[i][j]*r[j] for j in range(5)) for i in range(5)]
    d=math.sqrt(max(0.0,sum(r[i]*q[i] for i in range(5))))
    # bounded normal coordinates + Mahalanobis distance
    return [math.tanh(d/3.0)]+[math.tanh(v) for v in q]

def _survival_vector(s,manifold):
    row=s["row"];base=list(row.get("features",[]))
    core=[float(base[i]) if i<len(base) else 0.0 for i in _SURVIVAL_CORE_FEATURES]
    hp=list(_precision_vector(row))
    sf=_sf_key(s);route=_sf_route_coordinates(sf)
    a=row.get("survival_fresh_maturity_state",{}).get(sf)
    e=row.get("survival_fresh_entry_state",{}).get(sf)
    aa=list(a) if a is not None and len(a)==SEQUENTIAL_STATE_FEATURE_COUNT else [0.0]*SEQUENTIAL_STATE_FEATURE_COUNT
    ee=list(e) if e is not None and len(e)==SEQUENTIAL_STATE_FEATURE_COUNT else [0.0]*SEQUENTIAL_STATE_FEATURE_COUNT
    entry=[float(ee[i]) for i in _SURVIVAL_STATE_FEATURES]
    delta=[float(ee[i])-float(aa[i]) for i in _SURVIVAL_STATE_FEATURES]
    q=row.get("survival_fresh_morphology",{}).get(sf)
    morph=[float(x) for x in q] if q is not None and len(q)==SURVIVAL_MORPH_FEATURE_COUNT else [0.0]*SURVIVAL_MORPH_FEATURE_COUNT
    pv=row.get("survival_fresh_path_v2",{}).get(sf)
    path_v2=[float(x) for x in pv] if pv is not None and len(pv)==SURVIVAL_PATH_V2_FEATURE_COUNT else [0.0]*SURVIVAL_PATH_V2_FEATURE_COUNT
    path_v2_present=1.0 if pv is not None and len(pv)==SURVIVAL_PATH_V2_FEATURE_COUNT else 0.0
    rb=row.get("survival_fresh_reaction_bar",{}).get(sf,-1)
    pb=row.get("survival_fresh_pullback_bar",{}).get(sf,-1)
    tb=row.get("survival_fresh_trigger_bar",{}).get(sf,-1)
    eb=row.get("survival_fresh_entry_bar",{}).get(sf,-1)
    def ts(v):return max(-1.0,min(6.0,float(v)/10.0)) if v is not None else -1.0
    timing=[ts(eb),ts(rb),ts(pb),ts(tb)]
    regime=_regime_forward(aa,ee)
    manifold_x=_manifold_features(s,manifold)
    parts={
      "core":core,"harmonic":hp,"route":route,"morphology":morph,
      "path_v2":path_v2+[path_v2_present],
      "timing":timing,"entry_state":entry,"state_delta":delta,
      "regime":regime,"manifold":manifold_x
    }
    x=[];layout={};p=0
    for name in ("core","harmonic","route","morphology","path_v2","timing","entry_state","state_delta","regime","manifold"):
        z=parts[name];layout[name]=(p,p+len(z));x.extend(z);p+=len(z)
    rid=max(range(len(_REGIME_PROTOTYPES)),key=lambda i:regime[len(_REGIME_PROTOTYPES)+i])
    return x,layout,rid

def _prepare_survival(samples,manifold):
    out=[];layout=None
    for s in samples:
        x,ly,rid=_survival_vector(s,manifold);q=dict(s);q["x"]=x;q["regime_id"]=rid
        out.append(q);layout=ly
    return out,layout or {}

def _survival_specs():
    # Group-preserving architecture alternatives.  No univariate pre-screening:
    # interaction-only signals survive into the tree learner.
    group_sets=(
      ("core","harmonic","route","morphology","path_v2","timing","entry_state","state_delta","regime","manifold"),
      ("harmonic","route","morphology","path_v2","timing","entry_state","state_delta","regime","manifold"),
      ("core","harmonic","route","morphology","path_v2","regime","manifold"),
      ("harmonic","route","morphology","path_v2","entry_state","state_delta","regime","manifold"),
    )
    out=[];sid=0
    for groups in group_sets:
      for depth,rounds,minleaf,lr in ((2,10,34,.060),(3,12,28,.055)):
        out.append({"id":sid,"groups":list(groups),"depth":depth,"rounds":rounds,
                    "min_leaf":minleaf,"lr":lr});sid+=1
    return out

def _idx_for_spec(layout,spec):
    z=[]
    for name in spec["groups"]:
        a,b=layout[name];z.extend(range(a,b))
    return z

_SURVIVAL_CONTEXT_PARITY_DONE=False

def _event_balanced_weights(samples,eligible=None):
    """Each (year,event,decision-bar) cluster has total weight 1.

    eligible optionally supplies row indices for a conditional P/W/L head; the
    cluster is renormalized inside that head so route multiplicity cannot make an
    event statistically louder merely because more lattice actions share it.
    """
    ids=list(range(len(samples))) if eligible is None else list(eligible)
    by=defaultdict(list)
    for i in ids:
      s=samples[i];by[(s["window"],event_identity(s["setup"]),int(s["bar"]))].append(i)
    out={i:1.0/max(1,len(v)) for v in by.values() for i in v}
    return [out.get(i,0.0) for i in range(len(samples))]

def _build_survival_fit_context(samples,manifold):
    """Immutable fold context shared by every SURVIVAL architecture spec.

    Feature vectors, P/W/L targets, deterministic fit views, hierarchical prior
    and root feature orders depend on the fold, not on depth/rounds/spec. Build
    them once and reuse exactly; architecture search space remains unchanged.
    """
    ss,layout=_prepare_survival(samples,manifold)
    if len(ss)<500:return None
    X=[s["x"] for s in ss]
    yp=[1.0 if float(s["y"])>0 else 0.0 for s in ss]
    win=[i for i,s in enumerate(ss) if float(s["y"])>0]
    loss=[i for i,s in enumerate(ss) if float(s["y"])<=0]
    if len(win)<80 or len(loss)<80:return None
    wp0=_event_balanced_weights(ss)
    ww0=_event_balanced_weights(ss,win);wl0=_event_balanced_weights(ss,loss)
    Xp,tp=_fit_view(X,[yp,wp0],5200);ypf,wp=tp
    Xw=[X[i] for i in win];yw=[float(ss[i]["y"]) for i in win];ww=[ww0[i] for i in win]
    Xl=[X[i] for i in loss];yl=[max(0.0,-float(ss[i]["y"])) for i in loss];wl=[wl0[i] for i in loss]
    Xw,tw=_fit_view(Xw,[yw,ww],5200);yw,ww=tw
    Xl,tl=_fit_view(Xl,[yl,wl],5200);yl,wl=tl
    dim=len(Xp[0]) if Xp else 0
    specs=_survival_specs()
    use=sorted(set(j for spec in specs for j in _idx_for_spec(layout,spec)))
    if dim<=0 or any(len(x)!=dim for x in Xp+Xw+Xl) or any(j<0 or j>=dim for j in use):
        raise SystemExit("V74 survival fit-context dimension contract failure")
    return {"ss":ss,"layout":layout,"Xp":Xp,"yp":ypf,"wp":wp,"Xw":Xw,"yw":yw,"ww":ww,
            "Xl":Xl,"yl":yl,"wl":wl,"orders":_root_orders(Xp,use),
            "ow":_root_orders(Xw,use),"ol":_root_orders(Xl,use),
            "prior":_fit_struct_prior(ss),"wins":len(win),"losses":len(loss),
            "dim":dim,"use":use}

def _assert_survival_context_parity(samples,manifold,ctx):
    """One exact input/order probe proves context reuse cannot alter training."""
    global _SURVIVAL_CONTEXT_PARITY_DONE
    if _SURVIVAL_CONTEXT_PARITY_DONE:return
    ref,layout=_prepare_survival(samples,manifold)
    if layout!=ctx["layout"] or len(ref)!=len(ctx["ss"]):
        raise SystemExit("V74 survival context parity failure: layout/count")
    for a,b in zip(ref,ctx["ss"]):
        if (a["window"],a["setup"],a["route"],a["bar"],a["y"]) != (b["window"],b["setup"],b["route"],b["bar"],b["y"]) or tuple(a["x"])!=tuple(b["x"]):
            raise SystemExit("V74 survival context parity failure: sample")
    spec=_survival_specs()[0];idx=_idx_for_spec(layout,spec)
    direct=_root_orders(ctx["Xp"],idx)
    if any(direct[j]!=ctx["orders"][j] for j in idx):
        raise SystemExit("V74 survival context parity failure: root orders")
    _SURVIVAL_CONTEXT_PARITY_DONE=True
    print("[V74-SURVIVAL-CONTEXT-PARITY] pass=true",flush=True)

def _fit_survival_distribution(samples,spec,manifold,fit_ctx=None):
    ctx=fit_ctx or _build_survival_fit_context(samples,manifold)
    if ctx is None:return None
    layout=ctx["layout"];idx=_idx_for_spec(layout,spec)
    kw={"rounds":spec["rounds"],"lr":spec["lr"],"max_rows":10**9,
        "max_depth":spec["depth"],"min_leaf":spec["min_leaf"]}
    # R8 precision-first two-pass probability fit.  Pass 1 discovers the
    # training-only false-positive frontier.  Pass 2 upweights hard negatives
    # (and, more mildly, missed positives) so the learned ordering targets
    # Top-K winner purity rather than average classification accuracy.  Nested
    # expanding OOF below is the only place architecture/threshold is selected.
    pm0=_boost_train(ctx["Xp"],ctx["yp"],idx,root_orders=ctx["orders"],weights=ctx["wp"],**kw)
    hard_w=[]
    for xx,yy,ww0 in zip(ctx["Xp"],ctx["yp"],ctx["wp"]):
        pp,_=_boost_pred(pm0,xx);pp=max(.001,min(.999,float(pp)))
        difficulty=pp if float(yy)<.5 else .35*(1.0-pp)
        hard_w.append(float(ww0)*(1.0+2.75*difficulty))
    pm=_boost_train(ctx["Xp"],ctx["yp"],idx,root_orders=ctx["orders"],weights=hard_w,**kw)
    wm=_boost_train(ctx["Xw"],ctx["yw"],idx,root_orders=ctx["ow"],weights=ctx["ww"],**kw)
    lm=_boost_train(ctx["Xl"],ctx["yl"],idx,root_orders=ctx["ol"],weights=ctx["wl"],**kw)
    return {"type":"R8_SURVIVAL_COUNTERFACTUAL_PWL_DISTRIBUTION","spec":spec,"layout":layout,"idx":idx,
            "p":pm,"p_stage1":pm0,"w":wm,"l":lm,"manifold":manifold,
            "precision_hard_negative_refit":True,
            "prior":ctx["prior"],"n":len(ctx["ss"]),
            "wins":ctx["wins"],"losses":ctx["losses"]}

def _prepare_survival_inference(samples,manifold,prior):
    """Prepare identical inference vectors/prior once for a topology bank."""
    out=[]
    for s in samples:
        if s.get("source")!="SURVIVAL":continue
        x,_,rid=_survival_vector(s,manifold)
        pv=_pred_struct_prior(prior,dict(s,x=x))
        out.append({"s":s,"x":x,"regime_id":rid,"prior":pv})
    return out

def _pred_survival_distribution_prepared(model,s,x,rid,prior):
    p,sp=_boost_pred(model["p"],x);w,sw=_boost_pred(model["w"],x);l,sl=_boost_pred(model["l"],x)
    p=max(.001,min(.999,p));p=.82*p+.18*float(prior)
    w=max(.05,float(w));l=max(.05,float(l))
    support=max(8,min(sp or 8,sw or 8,sl or 8))
    se=math.sqrt(max(.02,p*(1.0-p))/support)
    plcb=max(0.0,p-Z*se)
    er=p*w-(1.0-p)*l
    pf=(p*w)/max(1e-9,(1.0-p)*l)
    score=plcb+.035*math.tanh(er/2.0)+.015*math.tanh(math.log(max(1e-6,pf)))
    return {"win":p,"win_lcb":plcb,"expected_win_r":w,"expected_loss_r":l,
            "mean":er,"pf":pf,"support":support,"regime_id":rid,"admission_score":score}

def _pred_survival_distribution(model,s):
    x,_,rid=_survival_vector(s,model["manifold"])
    prior=_pred_struct_prior(model["prior"],dict(s,x=x))
    return _pred_survival_distribution_prepared(model,s,x,rid,prior)

def _survival_decisions(samples,model,prepared=None):
    """Causal event-time route choice plus WAIT-aware stopping state.

    Route multiplicity is collapsed first.  Then each event is traversed in
    completed-bar order.  The score at bar t may use only predictions observed
    at bars <=t: no later route, price, outcome or future best score is visible.
    Persistence and draw-up encode whether the latent reversal belief is
    strengthening enough to justify consuming the single capital slot now.
    """
    pp=prepared if prepared is not None else _prepare_survival_inference(samples,model["manifold"],model["prior"])
    by=defaultdict(list)
    for z in pp:
        s=z["s"];by[(s["window"],event_identity(s["setup"]),s["bar"])].append(z)
    raw=[]
    for ev in by.values():
        cand=[]
        for z in ev:
            s=z["s"];p=_pred_survival_distribution_prepared(
                model,s,z["x"],z["regime_id"],z["prior"])
            cand.append((p["admission_score"],p["win_lcb"],p["win"],p["mean"],s["route"],p,s))
        cand.sort(reverse=True,key=lambda z:(z[0],z[1],z[2],z[3],z[4]))
        if not cand:continue
        _,_,_,_,_,p,s=cand[0];q=dict(s);q["regime_id"]=p["regime_id"]
        raw.append({"score":p["admission_score"],"route_rank":p["win_lcb"],"pred":p,"s":q})

    events=defaultdict(list)
    for e in raw:events[(e["s"]["window"],event_identity(e["s"]["setup"]))].append(e)
    out=[]
    for ev in events.values():
        ev.sort(key=lambda e:(int(e["s"]["bar"]),e["s"]["route"]))
        hist=[];last_bar=None
        for e in ev:
            base=float(e["score"]);pred=e["pred"];bar=int(e["s"]["bar"])
            prior_best=max(hist) if hist else base
            drawup=base-prior_best
            # One-sided causal persistence: reward a belief that is not merely a
            # single-bar spike.  Same-bar alternatives were already collapsed.
            persist=0.0
            if hist:
                persist=sum(1.0 for z in hist[-2:] if base>=z-.015)/min(2,len(hist))
            age_gap=0.0 if last_bar is None else min(1.0,max(0,bar-last_bar)/10.0)
            uncertainty=max(0.0,float(pred["win"])-float(pred["win_lcb"]))
            continuation=max(0.0,prior_best-base)
            # Fixed ex-ante stopping utility; coefficients are architectural,
            # not searched on burned outcomes.
            stop_score=(base
                        +.025*math.tanh(drawup/.05)
                        +.018*persist
                        -.030*math.tanh(continuation/.05)
                        -.020*math.tanh(uncertainty/.10)
                        -.006*age_gap)
            q=dict(e);q["score"]=stop_score
            q["pred"]=dict(pred,raw_admission_score=base,stopping_score=stop_score,
                           causal_persistence=persist,causal_drawup=drawup,
                           continuation_penalty=continuation,uncertainty=uncertainty)
            out.append(q)
            hist.append(base);last_bar=bar
    return out

def _stopping_feature_vector(e,route_model):
    s=e["s"];p=e["pred"];x=s.get("x",[])
    layout=route_model.get("layout",{})
    use=[]
    for g in ("path_v2","timing","regime","manifold"):
      a,b=layout.get(g,(0,0));use.extend(range(a,b))
    z=[float(x[j]) for j in use if 0<=j<len(x)]
    z.extend([
      max(0.0,min(1.0,float(p.get("win",0.0)))),
      max(0.0,min(1.0,float(p.get("win_lcb",0.0)))),
      math.tanh(float(p.get("mean",0.0))/2.0),
      math.tanh(math.log(max(1e-6,float(p.get("pf",1.0))))/3.0),
      min(1.0,float(p.get("support",0.0))/100.0),
      min(1.0,max(0.0,float(s.get("bar",0)))/180.0)
    ])
    return [1.0]+z

def _continuation_targets_from_decisions(decisions):
    """Best later payoff of the causally selected route, training labels only."""
    y=[0.0]*len(decisions);by=defaultdict(list)
    for i,e in enumerate(decisions):
      s=e["s"];by[(s["window"],event_identity(s["setup"]))].append((int(s["bar"]),i))
    for vv in by.values():
      vv.sort();future=0.0
      for bar,i in reversed(vv):
        y[i]=max(0.0,future)
        future=max(future,float(decisions[i]["s"]["y"]))
    return y

def _fit_stopping_model(samples,route_model,prepared=None):
    dec=_survival_decisions(samples,route_model,prepared)
    if len(dec)<250:return {"valid":False}
    X=[_stopping_feature_vector(e,route_model) for e in dec]
    y=_continuation_targets_from_decisions(dec)
    d=len(X[0]);lam=3.0
    a=[[0.0]*d for _ in range(d)];b=[0.0]*d
    for x,t in zip(X,y):
      for i in range(d):
        b[i]+=x[i]*t
        xi=x[i]
        for j in range(i,d):a[i][j]+=xi*x[j]
    for i in range(d):
      for j in range(i):a[i][j]=a[j][i]
      if i>0:a[i][i]+=lam
    inv=_mat_inverse(a)
    if inv is None:return {"valid":False}
    beta=[sum(inv[i][j]*b[j] for j in range(d)) for i in range(d)]
    resid=[y[k]-sum(beta[j]*X[k][j] for j in range(d)) for k in range(len(y))]
    sigma=statistics.pstdev(resid) if len(resid)>1 else 10.0
    return {"valid":True,"beta":beta,"sigma":max(.05,float(sigma)),"dim":d,
            "train_decisions":len(dec),"target_mean":sum(y)/len(y)}

def _predict_continuation(stop_model,e,route_model):
    if not stop_model or not stop_model.get("valid"):return 0.0
    x=_stopping_feature_vector(e,route_model)
    if len(x)!=int(stop_model["dim"]):raise SystemExit("V74 stopping feature dimension drift")
    return max(0.0,sum(float(stop_model["beta"][j])*x[j] for j in range(len(x))))

def _survival_stopping_decisions(samples,route_model,stop_model,prepared=None):
    dec=_survival_decisions(samples,route_model,prepared)
    for e in dec:
      co=_predict_continuation(stop_model,e,route_model)
      enter=float(e["pred"].get("mean",0.0))
      adv=enter-co
      e["pred"]["continuation"]=co;e["pred"]["stop_advantage"]=adv
      e["stop_advantage"]=adv
    return dec

def _compact_tournament_decision(e):
    """Minimal lossless decision payload for inner-OOF architecture selection."""
    s=e["s"];p=e["pred"]
    cs={k:s[k] for k in ("window","setup","family","action","source","base","route","bar","bars","y")}
    cs["row"]={}
    return {"score":float(e["score"]),"route_rank":float(e.get("route_rank",-999.0)),
            "stop_advantage":float(e.get("stop_advantage",-999.0)),
            "pred":{"regime_id":int(p.get("regime_id",0)),
                    "continuation":float(p.get("continuation",0.0)),
                    "stop_advantage":float(p.get("stop_advantage",-999.0))},"s":cs}

def _compute_shared_inner_survival_year(vw):
    """One causal inner year; safe to compute once and reuse by later outer folds."""
    vy=int(vw[1:])
    tr=[s for s in _ALL_SURVIVAL_SAMPLES if int(s["window"][1:])<vy]
    va=[s for s in _ALL_SURVIVAL_SAMPLES if s["window"]==vw]
    manifold=_fit_family_manifold(tr)
    ctx=_build_survival_fit_context(tr,manifold)
    if ctx is None:raise SystemExit("V74 shared inner survival context failure "+vw)
    _assert_survival_context_parity(tr,manifold,ctx)
    prepared=_prepare_survival_inference(va,manifold,ctx["prior"])
    banks=[]
    for spec in _survival_specs():
        md=_fit_survival_distribution(tr,spec,manifold,ctx)
        if md is None:raise SystemExit("V74 shared inner survival fit failure "+vw+" spec="+str(spec["id"]))
        sm=_fit_stopping_model(tr,md)
        if not sm.get("valid"):raise SystemExit("V74 shared inner stopping fit failure "+vw+" spec="+str(spec["id"]))
        banks.append([_compact_tournament_decision(e) for e in _survival_stopping_decisions(va,md,sm,prepared)])
    meta={"validation_year":vw,"training_years":sorted({s["window"] for s in tr}),
          "train_survival_actions":len(tr),"validation_survival_actions":len(va)}
    return vw,{"banks":banks,"meta":meta}

def _precision_rank(tm):
    if not tm:return (-999.0,)*7
    ms=list(tm.values())
    return (min(float(m["win_rate"])-MIN_WR for m in ms),
            min(float(m["lcb_r"]) for m in ms),
            min(float(m["mean_r"])-MIN_MEAN for m in ms),
            min(float(m["pf_r"])-MIN_PF for m in ms),
            min(float(m["average_rr"])-MIN_AVG_RR for m in ms),
            min(float(m["n"])/MIN_N-1.0 for m in ms),
            statistics.median(float(m["win_rate"]) for m in ms))

def _precision_threshold(decisions,years,target):
    adv=[float(e.get("stop_advantage",-999.0)) for e in decisions]
    margins=sorted(set([-math.inf]+[qtile(adv,q) for q in (0.10,0.25,0.40,0.55,0.70)]))
    best=None
    for margin in margins:
      by=defaultdict(lambda:defaultdict(lambda:-math.inf));scores=[]
      for e in decisions:
        if float(e.get("stop_advantage",-999.0))+1e-12<margin:continue
        w=e["s"]["window"];eid=event_identity(e["s"]["setup"]);z=float(e["score"])
        by[w][eid]=max(by[w][eid],z);scores.append(z)
      limits={};feasible=True
      for w in years:
        vals=sorted(by[w].values(),reverse=True);k=min(int(target),len(vals))
        if k<MIN_N:feasible=False;break
        limits[w]=vals[k-1]
      if not feasible or not scores:continue
      upper=min(limits.values())
      base=[z for z in scores if z<=upper+1e-12]
      cand=sorted(set([upper]+[qtile(base,q) for q in [i/50.0 for i in range(51)]]),reverse=True)
      for th in cand:
        tm={w:metric_selected(simulate(decisions,th,w,margin))[0] for w in years}
        if any(m["n"]<target for m in tm.values()):continue
        rank=_precision_rank(tm);z=(rank,margin,th,tm,limits,by)
        if best is None or z[:3]>best[:3]:best=z
    if best is None:return None
    return {"rank":best[0],"stop_margin":best[1],"threshold":best[2],
            "metrics":best[3],"limits":best[4],
            "supply":{w:len(best[5][w]) for w in years}}

def _conditional_mi_bits(decisions):
    """OOF conditional information in score about win, conditioning on family/regime."""
    if len(decisions)<100:return 0.0
    scores=[float(e["score"]) for e in decisions]
    cuts=sorted(set(qtile(scores,q) for q in (.2,.4,.6,.8)))
    groups=defaultdict(list)
    for e in decisions:
        b=bisect.bisect_right(cuts,float(e["score"]))
        y=1 if float(e["s"]["y"])>0 else 0
        groups[(e["s"]["family"],int(e["pred"].get("regime_id",0)))].append((b,y))
    total=sum(len(v) for v in groups.values());out=0.0
    for v in groups.values():
        n=len(v)
        if n<20:continue
        cb=Counter(b for b,_ in v);cy=Counter(y for _,y in v);cby=Counter(v)
        mi=0.0
        for (b,y),nn in cby.items():
            p=nn/n;den=(cb[b]/n)*(cy[y]/n)
            if p>0 and den>0:mi+=p*math.log(p/den,2)
        out+=(n/total)*mi
    return out

def _fit_survival_state_space_tournament(samples,years):
    specs=_survival_specs()
    eligible=[years[i] for i in range(2,len(years))]
    val_years=eligible[-min(3,len(eligible)):]
    if len(val_years)<2:raise SystemExit("V74 survival state-space insufficient inner years")
    banks=[[] for _ in specs];meta=[]
    shared=globals().get("_INNER_SURVIVAL_OOF_CACHE",{})
    for vw in val_years:
        vy=int(vw[1:]);tr=[s for s in samples if int(s["window"][1:])<vy];va=[s for s in samples if s["window"]==vw]
        expected={"validation_year":vw,"training_years":sorted({s["window"] for s in tr}),
                  "train_survival_actions":len(tr),"validation_survival_actions":len(va)}
        cached=shared.get(vw)
        if cached is not None:
            if cached.get("meta")!=expected or len(cached.get("banks",[]))!=len(specs):
                raise SystemExit("V74 shared inner cache semantic mismatch "+vw)
            for si in range(len(specs)):banks[si].extend(cached["banks"][si])
            meta.append(expected);continue
        manifold=_fit_family_manifold(tr)
        ctx=_build_survival_fit_context(tr,manifold)
        if ctx is None:raise SystemExit("V74 survival fit context failure "+vw)
        _assert_survival_context_parity(tr,manifold,ctx)
        prepared=_prepare_survival_inference(va,manifold,ctx["prior"])
        for si,spec in enumerate(specs):
            md=_fit_survival_distribution(tr,spec,manifold,ctx)
            if md is None:raise SystemExit("V74 survival distribution fit failure "+str(spec["id"]))
            banks[si].extend(_survival_decisions(va,md,prepared))
        meta.append(expected)
    candidates=[]
    for si,spec in enumerate(specs):
        dec=banks[si];cmi=_conditional_mi_bits(dec)
        for target in (250,275,300):
            z=_precision_threshold(dec,val_years,target)
            if z is None:continue
            rank=(z["rank"][0],cmi)+z["rank"][1:]
            candidates.append((rank,si,target,z,cmi))
    if not candidates:raise SystemExit("V74 survival state-space no coverage-feasible candidate")
    candidates.sort(key=lambda z:z[0],reverse=True)
    rank,si,target,z,cmi=candidates[0];chosen=specs[si]
    info_viable=bool(cmi>1e-4)
    print("[V74-SURVIVAL-INFO] conditional_mi_bits="+str(cmi)+" viable="+str(info_viable).lower(),flush=True)
    print("[V74-SURVIVAL-SELECT] "+json.dumps({"spec":chosen,"coverage_target":target,
          "rank":list(rank),"conditional_mi_bits":cmi},sort_keys=True),flush=True)

    full_manifold=_fit_family_manifold(samples)
    final_ctx=_build_survival_fit_context(samples,full_manifold)
    final=_fit_survival_distribution(samples,chosen,full_manifold,final_ctx)
    if final is None:raise SystemExit("V74 survival final distribution fit failure")
    stop_model=_fit_stopping_model(samples,final)
    if not stop_model.get("valid"):raise SystemExit("V74 survival final stopping fit failure")
    full_prepared=_prepare_survival_inference(samples,full_manifold,final_ctx["prior"])
    full_dec=_survival_stopping_decisions(samples,final,stop_model,full_prepared)
    oof_scores=[float(e["score"]) for e in banks[si]]
    full_scores=[float(e["score"]) for e in full_dec]
    om=med(oof_scores,0.0);fm=med(full_scores,0.0)
    oq1,oq3=qtile(oof_scores,.25),qtile(oof_scores,.75);fq1,fq3=qtile(full_scores,.25),qtile(full_scores,.75)
    scale=max(.25,min(4.0,(fq3-fq1)/max(1e-9,oq3-oq1)))
    transferred=fm+(float(z["threshold"])-om)*scale
    return {"model":final,"stopping_model":stop_model,"threshold":transferred,
            "stop_margin":z["stop_margin"],"oof_threshold":z["threshold"],
            "training_metrics":z["metrics"],"training_rank":list(rank),
            "training_limits":z["limits"],"training_supply":z["supply"],
            "coverage_target":target,"inner_oof_years":val_years,"nested_meta":meta,
            "conditional_mi_bits":cmi,"information_gate":info_viable,
            "threshold_transfer":{"oof_median":om,"full_fit_median":fm,"oof_iqr":oq3-oq1,
                                  "full_fit_iqr":fq3-fq1,"scale":scale,
                                  "rule":"OUTCOME_FREE_SCORE_DISTRIBUTION_AFFINE_TRANSFER"}}


# ---------------------------------------------------------------------------
# V74-R4 Unified Causal Mixture-of-Experts Optimal-Stopping Reconstruction
# R4.1: honest OOF stacked lane-action meta policy.  Route choice happens inside
# each lane first; EARLY/LATE/SURVIVAL/FAILURE remain separate candidates until
# the event-level meta policy chooses an action.  No burned/test outcome enters
# a runtime feature.
# ---------------------------------------------------------------------------

def _r4_regime_id(s):
    k=_market_regime_key(s)
    return sum((i+1)*ord(ch) for i,ch in enumerate(k))%997

def _r4_wilson_lcb(p,n):
    n=max(1.0,float(n));p=max(0.0,min(1.0,float(p)));z=Z
    den=1.0+z*z/n
    center=p+z*z/(2.0*n)
    rad=z*math.sqrt(max(0.0,p*(1.0-p)/n+z*z/(4.0*n*n)))
    return max(0.0,(center-rad)/den)

def _fit_r4_calibrator(route_decisions,bundle):
    """Training-only hierarchical calibration of the ENTER head.

    Calibration is learned only from prior-year route decisions.  Runtime sees
    the raw causal ENTER probability plus source/family/regime identity.  The
    hierarchy shrinks small cells toward the raw-probability-bin base rate.
    """
    reps=admission_lane_context(route_decisions)
    rows=[];glob=[0,0];bins=defaultdict(lambda:[0,0])
    for e in reps:
        z=pred_admission(bundle,e);p=max(0.0,min(.999999,float(z["enter"])))
        b=min(9,int(p*10.0));win=1 if float(e["s"]["y"])>0 else 0
        rid=int(e["s"].get("regime_id",_r4_regime_id(e["s"])))
        rows.append((e,p,b,win,rid));glob[0]+=win;glob[1]+=1
        bins[b][0]+=win;bins[b][1]+=1
    gp=(glob[0]+.5)/(glob[1]+1.0) if glob[1] else .5
    base={}
    for b,(w,n) in bins.items():
        pp=(w+18.0*gp+.5)/(n+19.0)
        base[b]={"p":pp,"n":n+18.0}
    banks={
      "source":defaultdict(lambda:[0,0]),
      "family":defaultdict(lambda:[0,0]),
      "source_family":defaultdict(lambda:[0,0]),
      "regime":defaultdict(lambda:[0,0])
    }
    for e,p,b,win,rid in rows:
        s=e["s"];src=s.get("source","NONE");fam=s.get("family","NONE")
        keys={"source":str((src,b)),"family":str((fam,b)),
              "source_family":str((src,fam,b)),"regime":str((rid,b))}
        for name,k in keys.items():
            banks[name][k][0]+=win;banks[name][k][1]+=1
    shrink=42.0;cells={name:{} for name in banks}
    for name,bank in banks.items():
        for k,(w,n) in bank.items():
            try:b=int(k.rsplit(",",1)[-1].replace(")","").strip())
            except Exception:b=0
            bp=float(base.get(b,{"p":gp})["p"])
            pp=(w+shrink*bp+.5)/(n+shrink+1.0)
            cells[name][k]={"p":pp,"n":n+shrink}
    return {"global_p":gp,"global_n":glob[1],"base":base,"cells":cells,
            "shrink":shrink,"n":glob[1]}

def _pred_r4_calibrator(cal,bundle,e):
    z=pred_admission(bundle,e);p=max(0.0,min(.999999,float(z["enter"])))
    b=min(9,int(p*10.0));s=e["s"];src=s.get("source","NONE");fam=s.get("family","NONE")
    rid=int(s.get("regime_id",_r4_regime_id(s)))
    bb=cal.get("base",{}).get(b,{"p":cal.get("global_p",.5),"n":max(1,cal.get("global_n",1))})
    vals=[float(bb["p"])];ns=[float(bb.get("n",1))]
    keys={"source":str((src,b)),"family":str((fam,b)),
          "source_family":str((src,fam,b)),"regime":str((rid,b))}
    for name,k in keys.items():
        q=cal.get("cells",{}).get(name,{}).get(k)
        if q is not None:vals.append(float(q["p"]));ns.append(float(q.get("n",1)))
    eps=1e-6
    hm=len(vals)/sum(1.0/max(eps,min(1.0,v)) for v in vals)
    pp=.60*hm+.40*(sum(vals)/len(vals))
    en=max(1.0,min(ns))
    return {"raw":z,"p":pp,"lcb":_r4_wilson_lcb(pp,en),"effective_n":en}

def _r4_event_year_weights(samples):
    """Every harmonic event has unit mass inside its year; every year equal mass."""
    return _event_year_balanced_weights(samples)

def _r4_direct_causal_state(s):
    """Existing approved causal state for the R4 meta selector.

    R4.1 accidentally compressed the second layer almost entirely to first-layer
    predictions.  That destroys information even when the underlying HCOG and
    Path-V3 telemetry are causal.  Re-admit the existing event features,
    canonical harmonic-precision vector and SURVIVAL Path V3 here.  This is not
    Path V4 and creates no new telemetry.  Non-SURVIVAL lanes receive an explicit
    zero Path-V3 vector so the meta feature dimension is identical across lanes.
    """
    r=s.get("row") or {}
    base=[]
    raw=list(r.get("features",[]))
    for i in range(len(FEATURE_NAMES)):
        try:
            v=float(raw[i]);base.append(v if math.isfinite(v) else 0.0)
        except Exception:
            base.append(0.0)
    try:
        hp=[float(z) for z in _precision_vector(r)]
    except Exception:
        hp=[0.0]*len(_precision_vector({}))
    cp=[0.0]*R7_COMMON_PATH_FEATURE_COUNT
    if s.get("source")!="SURVIVAL":
        sx=list(s.get("x",[]))
        if len(sx)>=R7_COMMON_PATH_FEATURE_COUNT:
            try:
                z=[float(v) for v in sx[-R7_COMMON_PATH_FEATURE_COUNT:]]
                if all(math.isfinite(v) for v in z):cp=z
            except Exception:
                pass
    pv=[0.0]*SURVIVAL_PATH_V2_FEATURE_COUNT
    if s.get("source")=="SURVIVAL":
        sf=str(s.get("route","")).split("|",1)[1] if "|" in str(s.get("route","")) else ""
        q=r.get("survival_fresh_path_v2",{}).get(sf)
        if q is not None and len(q)==SURVIVAL_PATH_V2_FEATURE_COUNT:
            try:
                z=[float(v) for v in q]
                if all(math.isfinite(v) for v in z):pv=z
            except Exception:
                pass
    fam=[1.0 if s.get("family")==ff else 0.0 for ff in FAMILIES]
    return base+hp+cp+pv+fam

def _r4_stage_samples(route_decisions,prior):
    """R4.3 causal trajectory state for unified-lane optimal stopping.

    One route per lane is retained at each completed decision bar.  The static
    R4.2 state is augmented only with summaries of *earlier* decision bars from
    the same harmonic event.  Same-bar candidates are frozen together before
    history is advanced, so source iteration order cannot leak contemporaneous
    alternatives into a fake temporal sequence.
    """
    by_bar=defaultdict(list)
    for e in route_decisions:
        s=e["s"];by_bar[(s["window"],event_identity(s["setup"]),int(s["bar"]))].append(e)

    raw=[]
    for vv in by_bar.values():
        lane={}
        for e in vv:
            src=e["s"].get("source","NONE")
            if src not in lane or float(e.get("score",-999.0))>float(lane[src].get("score",-999.0)):
                lane[src]=e
        vals=sorted([float(e.get("score",-999.0)) for e in lane.values()],reverse=True)
        if vals:
            mx=max(vals);ex=[math.exp(max(-40.0,min(40.0,(z-mx)/.35))) for z in vals]
            sm=sum(ex);pp=[z/sm for z in ex]
            ent=-sum(q*math.log(max(q,1e-15)) for q in pp)
            ent=ent/math.log(len(pp)) if len(pp)>1 else 0.0
            margin=math.tanh((vals[0]-vals[1]) if len(vals)>1 else 1.0)
        else:
            ent=1.0;margin=0.0

        for e in lane.values():
            s=e["s"];p=e["pred"];src=s.get("source","NONE")
            x=[
              float(p.get("win",.5)),
              math.tanh(float(p.get("mean",0.0))/2.0),
              math.tanh(float(p.get("lcb",0.0))/2.0),
              math.tanh(float(p.get("continuation",0.0))/2.0),
              -math.tanh(float(p.get("regret",0.0))/2.0),
              float(p.get("best_probability",.5)),
              math.tanh(float(p.get("stop_advantage",0.0))/2.0),
              math.tanh(float(s.get("pair_advantage",0.0))),
              math.tanh(2.0*float(s.get("decision_margin",0.0))),
              math.tanh(float(e.get("score",0.0))/2.0),
              math.tanh(float(e.get("route_rank",0.0))/2.0),
              min(1.0,max(0.0,float(p.get("expected_hold_bars",60.0))/180.0)),
              float(_pred_struct_prior(prior,s)),
              float(ent),float(margin),
              min(1.0,len(lane)/max(1.0,float(len(SOURCES)))),
              min(1.0,max(0.0,float(s.get("bar",0)))/180.0),
              1.0 if s.get("action")=="CONTINUATION" else 0.0
            ]
            x.extend([1.0 if src==q else 0.0 for q in SOURCES])
            x.extend(_r4_direct_causal_state(s))
            for qsrc in SOURCES:
                z=lane.get(qsrc)
                if z is None:
                    x.extend([0.0]*8);continue
                zp=z["pred"]
                x.extend([
                  1.0,float(zp.get("win",.5)),
                  math.tanh(float(zp.get("mean",0.0))/2.0),
                  math.tanh(float(zp.get("lcb",0.0))/2.0),
                  float(zp.get("best_probability",.5)),
                  -math.tanh(float(zp.get("regret",0.0))/2.0),
                  math.tanh(float(zp.get("stop_advantage",0.0))/2.0),
                  math.tanh(float(z.get("score",0.0))/2.0)
                ])
            raw.append({"window":s["window"],"setup":s["setup"],"family":s["family"],
                        "action":s["action"],"source":src,"base":s["base"],"route":s["route"],
                        "bar":s["bar"],"bars":s["bars"],"x":x,"y":float(s["y"]),"row":s["row"],
                        "regime_id":_r4_regime_id(s),
                        "_lane_score":float(e.get("score",0.0)),
                        "_lane_win":float(p.get("win",.5)),
                        "_lane_mean":float(p.get("mean",0.0)),
                        "_lane_lcb":float(p.get("lcb",0.0)),
                        "_lane_stop":float(p.get("stop_advantage",0.0))})

    events=defaultdict(list)
    for s in raw:
        events[(s["window"],event_identity(s["setup"]))].append(s)
    out=[]
    for vv in events.values():
        bars=defaultdict(list)
        for s in vv:bars[int(s["bar"])].append(s)
        hist_best=[];last_bar=None
        last_by_src={};count_by_src=Counter()
        running_best_max=-math.inf;running_best_min=math.inf
        for bar in sorted(bars):
            cur=bars[bar]
            prev_best=hist_best[-1] if hist_best else 0.0
            prev_prev=hist_best[-2] if len(hist_best)>=2 else prev_best
            slope=prev_best-prev_prev if hist_best else 0.0
            gap=0.0 if last_bar is None else min(1.0,max(0.0,bar-last_bar)/20.0)
            hcount=min(1.0,len(hist_best)/8.0)
            rbmax=prev_best if running_best_max==-math.inf else running_best_max
            rbmin=prev_best if running_best_min==math.inf else running_best_min
            for s in cur:
                src=s["source"];prev=last_by_src.get(src)
                hist=[
                  hcount,gap,
                  math.tanh(prev_best/2.0),
                  math.tanh(slope/1.0),
                  math.tanh(rbmax/2.0),
                  math.tanh(rbmin/2.0),
                  min(1.0,count_by_src[src]/6.0)
                ]
                # Last observed state of every lane.  These values are from a
                # strictly earlier completed bar, never the current same-bar set.
                for qsrc in SOURCES:
                    z=last_by_src.get(qsrc)
                    if z is None:
                        hist.extend([0.0]*6)
                    else:
                        hist.extend([
                          1.0,
                          math.tanh(float(z["_lane_score"])/2.0),
                          float(z["_lane_win"]),
                          math.tanh(float(z["_lane_mean"])/2.0),
                          math.tanh(float(z["_lane_lcb"])/2.0),
                          math.tanh(float(z["_lane_stop"])/2.0)
                        ])
                if prev is None:
                    hist.extend([0.0]*6)
                else:
                    hist.extend([
                      1.0,
                      math.tanh((float(s["_lane_score"])-float(prev["_lane_score"]))/1.0),
                      float(s["_lane_win"])-float(prev["_lane_win"]),
                      math.tanh((float(s["_lane_mean"])-float(prev["_lane_mean"]))/1.0),
                      math.tanh((float(s["_lane_lcb"])-float(prev["_lane_lcb"]))/1.0),
                      math.tanh((float(s["_lane_stop"])-float(prev["_lane_stop"]))/1.0)
                    ])
                q=dict(s);q["x"]=list(s["x"])+hist
                for k in ("_lane_score","_lane_win","_lane_mean","_lane_lcb","_lane_stop"):q.pop(k,None)
                out.append(q)

            # Advance history only after every candidate at this bar was encoded.
            best=max(float(s["_lane_score"]) for s in cur)
            hist_best.append(best)
            running_best_max=max(running_best_max,best)
            running_best_min=min(running_best_min,best)
            for s in cur:
                last_by_src[s["source"]]=s
                count_by_src[s["source"]]+=1
            last_bar=bar
    return out

def _r4_fit_value_balanced(samples,idx):
    X=[s["x"] for s in samples]
    ym=[float(s["y"]) for s in samples];yw=[1.0 if s["y"]>0 else 0.0 for s in samples]
    yc=training_continuation_targets(samples);yr,yb=event_regret_targets(samples)
    yh=[max(1.0,min(180.0,float(s.get("bars",1) or 1)))/180.0 for s in samples]
    w=_r4_event_year_weights(samples)
    if len(X)>9000:
        step=max(1,math.ceil(len(X)/9000));ids=list(range(0,len(X),step))
        Xf=[X[i] for i in ids];targets=[[z[i] for i in ids] for z in (ym,yw,yc,yr,yb,yh)];wf=[w[i] for i in ids]
    else:
        Xf=X;targets=[ym,yw,yc,yr,yb,yh];wf=w
    ymf,ywf,ycf,yrf,ybf,yhf=targets;orders=_root_orders(Xf,idx)
    kw={"rounds":max(8,TREE_ROUNDS),"lr":.070,"max_rows":10**9,"root_orders":orders,
        "max_depth":2,"min_leaf":34,"weights":wf}
    mm=_boost_train(Xf,ymf,idx,**kw);wm=_boost_train(Xf,ywf,idx,**kw)
    cm=_boost_train(Xf,ycf,idx,**kw);rm=_boost_train(Xf,yrf,idx,**kw)
    bm=_boost_train(Xf,ybf,idx,**kw)
    hm=_boost_train(Xf,yhf,idx,rounds=max(6,TREE_ROUNDS-2),lr=.070,max_rows=10**9,
                    root_orders=orders,max_depth=2,min_leaf=34,weights=wf)
    pm=[_boost_pred(mm,x)[0] for x in X];pw=[max(0.0,min(1.0,_boost_pred(wm,x)[0])) for x in X]
    return {"idx":idx,"mean":mm,"win":wm,"continuation":cm,"regret":rm,"best":bm,"hold":hm,
            "residuals":_residual_cells(samples,pm,pw)}

def _r4_fit_pair_balanced(samples,idx):
    X=[];yw=[];yd=[];event_keys=[]
    for key,ev in grouped_events(samples).items():
        if len(ev)<2:continue
        a=sorted(ev,key=lambda z:(z["source"],z["base"],z["route"]));n=len(a)
        for i in range(n):
            for j in range(i+1,n):
                delta=float(a[i]["y"])-float(a[j]["y"])
                if abs(delta)<1e-12:continue
                d=[a[i]["x"][q]-a[j]["x"][q] for q in idx]
                X.append(d);yw.append(1.0 if delta>0 else 0.0);yd.append(max(-4.0,min(4.0,delta)));event_keys.append((key[0],key[1]))
                X.append([-z for z in d]);yw.append(0.0 if delta>0 else 1.0);yd.append(max(-4.0,min(4.0,-delta)));event_keys.append((key[0],key[1]))
    if len(X)<200:return {"valid":False,"idx":idx,"n":len(X)}
    by=defaultdict(list)
    for i,k in enumerate(event_keys):by[k].append(i)
    year_events=defaultdict(list)
    for (w,eid),ids in by.items():year_events[w].append(ids)
    weights=[0.0]*len(X)
    for w,events in year_events.items():
        ew=1.0/max(1,len(events))
        for ids in events:
            q=ew/max(1,len(ids))
            for i in ids:weights[i]=q
    sw=sum(weights);scale=(len(weights)/sw) if sw>1e-18 else 1.0
    weights=[z*scale for z in weights]
    use=list(range(len(idx)));orders=_root_orders(X,use)
    return {"valid":True,"idx":idx,"n":len(X),
            "win":_boost_train(X,yw,use,rounds=max(8,PAIR_ROUNDS),lr=.075,max_rows=10**9,
                               root_orders=orders,max_depth=2,min_leaf=28,weights=weights),
            "delta":_boost_train(X,yd,use,rounds=max(8,PAIR_ROUNDS),lr=.075,max_rows=10**9,
                                 root_orders=orders,max_depth=2,min_leaf=28,weights=weights)}

def _r4_meta_feature_idx(stage_samples):
    """Training-only union of temporally stable admission objectives.

    Winner probability alone is too lossy for the V74 hard gate.  Select a
    bounded union of features that transfer in sign for win, strong-win and
    clipped Expected-R, then fill from the generic nonlinear stability ranking.
    """
    p=len(stage_samples[0]["x"]) if stage_samples else 0
    yw=[1.0 if float(s["y"])>0.0 else 0.0 for s in stage_samples]
    ys=[1.0 if float(s["y"])>=1.0 else 0.0 for s in stage_samples]
    yr=[(max(-1.0,min(2.5,float(s["y"])))+1.0)/3.5 for s in stage_samples]
    banks=[
      stable_idx_target(stage_samples,yw,min(24,p)),
      stable_idx_target(stage_samples,ys,min(24,p)),
      stable_idx_target(stage_samples,yr,min(24,p)),
      stable_idx(stage_samples,min(36,p))
    ]
    out=[]
    for bank in banks:
        for j in bank:
            if j not in out:out.append(j)
            if len(out)>=56:return out
    return out or list(range(min(32,p)))


def _fit_r4_meta_policy(stage_samples,years):
    if len(stage_samples)<700:raise SystemExit("V74-R6 insufficient OOF stage samples")
    p=len(stage_samples[0]["x"]);idx=_r4_meta_feature_idx(stage_samples)
    if len(idx)<6:idx=list(range(min(24,p)))
    vm=_r4_fit_value_balanced(stage_samples,idx)
    tr_route=meta_lane_decisions(stage_samples,vm)
    admission=fit_admission_bundle(tr_route,years)
    precision=fit_source_precision_bundle(tr_route,years)
    common_cal=_fit_r6_common_calibrator(tr_route,precision,years)
    r8=fit_r8_local_matcher(stage_samples,years)
    return {"type":"R8_LOCAL_MATCHED_COUNTERFACTUAL__R7_CAUSAL_TRAJECTORY_POLICY",
            "value":vm,"pair":None,
            "admission_bundle":admission,
            "source_precision_bundle":precision,
            "common_calibrator":common_cal,
            "r8_matcher":r8,
            "score_mode":"R8_MATCHED_UTILITY",
            "fit_years":list(years),"selected_features":list(idx),
            "lane_preserving_until_post_admission":True,
            "mode_specific_post_admission_arbitration":True,
            "forward_oof_common_scale_calibration":True,
            "local_counterfactual_matching":True,
            "source_native_matched_cells":True}


def _apply_r4_meta_policy(model,stage_samples,preserve_lanes=False,score_mode=None):
    route=meta_lane_decisions(stage_samples,model["value"])
    scored=[]
    for e in admission_lane_context(route):
        z=pred_admission(model["admission_bundle"],e)
        cc=_pred_r6_common_calibrator(model["common_calibrator"],
                                      model["source_precision_bundle"],e)
        r8=_pred_r8_local_matcher(model["r8_matcher"],e)
        p=e["pred"];comp=max(float(z["defer"]),float(z["reject"]))
        stop01=.5+.5*math.tanh(float(z["advantage_lcb"])/1.25)
        common=float(cc["utility"])
        bank={
          "R6_COMMON_UTILITY":common,
          "R6_WIN_LCB":float(cc["win_lcb"]),
          "R6_WIN_PROB":float(cc["win_p"]),
          "R6_MEAN_LCB":float(cc["mean_lcb"]),
          "R6_UTILITY_PLUS_STOP":common+.06*stop01,
          "R8_MATCHED_UTILITY":float(r8["utility"]),
          "R8_MATCHED_WIN_LCB":float(r8["win_lcb"]),
          "R8_MATCHED_MEAN_LCB":float(r8["mean_lcb"])
        }
        q=dict(e);q["score"]=common
        q["stop_advantage"]=float(p.get("stop_advantage",-999.0))
        q["pred"]=dict(p,admission=z,
                       r6_source_precision=cc["ranker"],
                       r6_win_probability=cc["win_p"],
                       r6_win_lcb=cc["win_lcb"],
                       r6_mean_r=cc["mean_r"],
                       r6_mean_lcb=cc["mean_lcb"],
                       r6_common_utility=common,
                       r6_calibration_origin=cc["calibration_origin"],
                       r6_effective_n=cc["effective_n"],
                       r6_fallback_penalty=cc["fallback_penalty"],
                       r8_matched_probability=r8["p"],
                       r8_matched_win_lcb=r8["win_lcb"],
                       r8_matched_mean_r=r8["mean_r"],
                       r8_matched_mean_lcb=r8["mean_lcb"],
                       r8_matched_utility=r8["utility"],
                       r8_matched_support=r8["support"],
                       r8_matched_cells=r8["matched_cells"],
                       r8_matched_dispersion=r8["dispersion"],
                       r8_match_depth=r8["match_depth"],
                       r8_match_origin=r8["origin"],
                       raw_meta_score=common,semantic_scores=bank,
                       score_mode=str(score_mode or model.get("score_mode","R8_MATCHED_UTILITY")),score_orientation=1.0,
                       enter_wait_margin=float(z["enter_lcb"])-comp,
                       regime_id=int(e["s"].get("regime_id",0)))
        scored.append(q)
    if preserve_lanes:return scored
    mode=str(score_mode or model.get("score_mode","R6_COMMON_UTILITY"))
    return _r6_arbitrate(scored,mode)

def _compact_r4_stage(s):
    return {"window":s["window"],"setup":s["setup"],"family":s["family"],
            "action":s["action"],"source":s["source"],"base":s["base"],
            "route":s["route"],"bar":s["bar"],"bars":s["bars"],
            "x":[float(z) for z in s["x"]],"y":float(s["y"]),"row":{},
            "regime_id":int(s.get("regime_id",0))}

def _compute_shared_inner_r4_year(vw):
    """One honest first-layer OOF year, retaining all four lane candidates."""
    vy=int(vw[1:])
    tr=[s for s in _ALL_SAMPLES if int(s["window"][1:])<vy]
    va=[s for s in _ALL_SAMPLES if s["window"]==vw]
    yrs=sorted({s["window"] for s in tr},key=lambda w:int(w[1:]))
    heads,_=fit_mechanism_heads_from_samples(tr)
    tr_route=mechanism_decisions(tr,heads);va_route=mechanism_decisions(va,heads)
    prior=_fit_struct_prior([e["s"] for e in tr_route])
    stage=[_compact_r4_stage(s) for s in _r4_stage_samples(va_route,prior)]
    meta={"validation_year":vw,"training_years":yrs,
          "train_actions":len(tr),"validation_actions":len(va),
          "stage_candidates":len(stage),
          "validation_events":len({event_identity(s["setup"]) for s in stage})}
    return vw,{"stage":stage,"meta":meta}

def _r4_meta_cache_key(years):
    return tuple(str(w) for w in years)

def _fit_r4_meta_policy_cached(stage_samples,years):
    key=_r4_meta_cache_key(years)
    md=globals().get("_R4_META_MODEL_CACHE",{}).get(key)
    if md is not None:return md
    return _fit_r4_meta_policy(stage_samples,years)

def _fit_r4_tournament(samples,years):
    eligible=[years[i] for i in range(2,len(years))]
    val_years=list(eligible)
    if len(val_years)<3:raise SystemExit("V74-R6 insufficient inner OOF years")
    shared=globals().get("_INNER_R4_OOF_CACHE",{});stage=[];meta=[]
    for vw in val_years:
        z=shared.get(vw)
        if z is None:
            _,z=_compute_shared_inner_r4_year(vw)
        if not z.get("stage"):raise SystemExit("V74-R6 empty OOF stage "+vw)
        stage.extend(z["stage"]);meta.append(z["meta"])

    # Honest expanding-forward meta OOF.  Preserve every scored source lane here;
    # each candidate semantic mode performs its own post-admission arbitration.
    cross_lanes=[];meta_cv=[];cross_years=[]
    for hi in range(2,len(val_years)):
        hw=val_years[hi];ty=val_years[:hi]
        tr=[s for s in stage if s["window"] in ty]
        va=[s for s in stage if s["window"]==hw]
        if len(tr)<700 or not va:continue
        md=_fit_r4_meta_policy_cached(tr,ty)
        dd=_apply_r4_meta_policy(md,va,preserve_lanes=True)
        cross_lanes.extend(dd);cross_years.append(hw)
        meta_cv.append({"held_year":hw,"fit_years":list(ty),"train_stage":len(tr),
                        "test_stage":len(va),"scored_lanes":len(dd),
                        "causal_forward_chain":True,
                        "mode_specific_arbitration":True})
    if not cross_lanes or not cross_years:
        raise SystemExit("V74-R6 empty causal forward meta OOF")

    candidates=[]
    for mode in R6_SEMANTIC_SCORE_MODES:
        scored=_r6_arbitrate(cross_lanes,mode)
        cmi=_conditional_mi_bits(scored)
        for target in (250,275,300):
            z=_precision_threshold(scored,cross_years,target)
            if z is None:continue
            rank=tuple(z["rank"])+(cmi,)
            candidates.append((rank,target,z,mode,cmi,scored))
    if not candidates:raise SystemExit("V74-R6 no coverage-feasible common-scale scorer")
    candidates.sort(key=lambda x:x[0],reverse=True)
    rank,target,z,score_mode,cmi,cross=candidates[0]

    final_meta=dict(_fit_r4_meta_policy_cached(stage,val_years))
    final_meta["score_mode"]=score_mode
    fitted_lanes=_apply_r4_meta_policy(final_meta,stage,preserve_lanes=True)
    fitted_dec=_r6_arbitrate(fitted_lanes,score_mode)

    os=[float(e["score"]) for e in cross];fs=[float(e["score"]) for e in fitted_dec]
    om=med(os,0.0);fm=med(fs,0.0)
    oq1,oq3=qtile(os,.25),qtile(os,.75);fq1,fq3=qtile(fs,.25),qtile(fs,.75)
    scale=max(.35,min(2.5,(fq3-fq1)/max(1e-9,oq3-oq1)))
    transferred=fm+(float(z["threshold"])-om)*scale

    oof_stop=float(z.get("stop_margin",-math.inf))
    if math.isfinite(oof_stop):
        oa=[float(e.get("stop_advantage",-999.0)) for e in cross
            if math.isfinite(float(e.get("stop_advantage",-999.0))) and float(e.get("stop_advantage",-999.0))>-900.0]
        fa=[float(e.get("stop_advantage",-999.0)) for e in fitted_dec
            if math.isfinite(float(e.get("stop_advantage",-999.0))) and float(e.get("stop_advantage",-999.0))>-900.0]
        oam=med(oa,0.0);fam=med(fa,0.0)
        oaq1,oaq3=qtile(oa,.25),qtile(oa,.75);faq1,faq3=qtile(fa,.25),qtile(fa,.75)
        stop_scale=max(.35,min(2.5,(faq3-faq1)/max(1e-9,oaq3-oaq1)))
        stop_transferred=fam+(oof_stop-oam)*stop_scale
    else:
        oam=fam=0.0;oaq1=oaq3=faq1=faq3=0.0;stop_scale=1.0
        stop_transferred=-math.inf

    heads,training=fit_mechanism_heads_from_samples(samples)
    route=mechanism_decisions(samples,heads)
    prior=_fit_struct_prior([e["s"] for e in route])
    training_oracle={w:_oracle_top250([s for s in samples if s["window"]==w]) for w in years}
    return {"mechanism_heads":heads,"mechanism_training":training,
            "stage_prior":prior,"meta_policy":final_meta,
            "threshold":transferred,"oof_threshold":z["threshold"],
            "stop_margin":stop_transferred,"oof_stop_margin":oof_stop,
            "training_metrics":z["metrics"],"training_rank":list(rank),
            "training_limits":z["limits"],"training_supply":z["supply"],
            "coverage_target":target,"inner_oof_years":val_years,
            "meta_oof_years":cross_years,
            "nested_meta":meta,"meta_crossfit":meta_cv,
            "conditional_mi_bits":cmi,"score_orientation":1.0,"score_mode":score_mode,
            "training_oracle_admission":training_oracle,
            "threshold_transfer":{"oof_median":om,"full_fit_median":fm,
              "oof_iqr":oq3-oq1,"full_fit_iqr":fq3-fq1,"scale":scale,
              "oof_stop_margin":oof_stop,"transferred_stop_margin":stop_transferred,
              "stop_oof_median":oam,"stop_full_fit_median":fam,
              "stop_oof_iqr":oaq3-oaq1,"stop_full_fit_iqr":faq3-faq1,
              "stop_scale":stop_scale,
              "rule":"OUTCOME_FREE_R6_COMMON_SCALE_AND_STOP_MARGIN_AFFINE_TRANSFER"}}

def fit_policy(train_rows,prebuilt_samples=None):
    """V74-R8 SURVIVAL-native counterfactual admission policy.

    Physical/forensic evidence says winner supply is concentrated in the
    SURVIVAL manifold.  Formal fitting therefore learns capital admission only
    inside SURVIVAL; EARLY/LATE/FAILURE remain complete shadow telemetry and are
    never deleted or family-blacklisted.  All architecture, threshold and
    stopping choices are nested expanding-forward OOF on prior years only.
    """
    samples=list(prebuilt_samples) if prebuilt_samples is not None else make_samples(train_rows)
    survival=[s for s in samples if s.get("source")=="SURVIVAL"]
    if len(survival)<1500:raise SystemExit("V74-R8 insufficient SURVIVAL causal actions")
    yrs=sorted({r["window"] for r in train_rows},key=lambda w:int(w[1:]))
    r8=_fit_survival_state_space_tournament(survival,yrs)
    tm=r8["training_metrics"];worst=min(gate_margin(m) for m in tm.values()) if tm else -999.0
    training_gate=all(gate(m) for m in tm.values()) if tm else False
    training_oracle={w:_oracle_top250([s for s in survival if s["window"]==w]) for w in yrs}
    return {"architecture":"V74_R8_SURVIVAL_NATIVE_COUNTERFACTUAL_ADMISSION_POLICY",
            "survival_model":r8["model"],"stopping_model":r8["stopping_model"],
            "admission_fit_years":yrs,"admission_inner_oof_years":r8["inner_oof_years"],
            "threshold":r8["threshold"],"oof_threshold":r8["oof_threshold"],
            "stop_margin":r8["stop_margin"],
            "training_coverage_limits":r8["training_limits"],"training_supply":r8["training_supply"],
            "training_metrics":tm,"training_worst_gate_margin":worst,
            "training_oracle_admission":training_oracle,
            "training_gate":training_gate,"coverage_target":r8["coverage_target"],
            "admission_sweep":{"rounds":[],"evaluated_candidates":len(_survival_specs()),
              "training_rank":r8["training_rank"],"baseline_rank":None,
              "non_regression_vs_current_training":True,
              "selected_mode":"R8_SURVIVAL_NATIVE_COUNTERFACTUAL__HARD_NEGATIVE_PRECISION__PWL_DISTRIBUTION__CAUSAL_STOPPING",
              "inner_oof_years":r8["inner_oof_years"],"nested_meta":r8["nested_meta"],
              "threshold_transfer":r8["threshold_transfer"],
              "conditional_mi_bits":r8["conditional_mi_bits"],
              "information_gate":r8["information_gate"],
              "score_orientation":1.0}},samples

def apply_policy(policy,test_rows,prebuilt_samples=None):
    samples=list(prebuilt_samples) if prebuilt_samples is not None else make_samples(test_rows)
    survival=[s for s in samples if s.get("source")=="SURVIVAL"]
    model=policy["survival_model"]
    prepared=_prepare_survival_inference(survival,model["manifold"],model["prior"])
    dec=_survival_stopping_decisions(survival,model,policy["stopping_model"],prepared)
    sel=simulate(dec,policy["threshold"],stop_margin=policy.get("stop_margin",-math.inf))
    # Return the full action surface for oracle diagnostics, while deployed
    # decisions are strictly SURVIVAL-native.
    return sel,samples,dec

def _diag_metrics(samples):
    rr=[]
    for s in samples:
      q=dict(s.get("row",{}));q["r"]=float(s["y"]);q["bars"]=max(1,int(s.get("bars",1) or 1));rr.append(q)
    return metrics(rr)

def _component_rank_diagnostic(decisions):
    """Burned/post-hoc diagnostic only: isolate causal score components.

    Each component is frozen by prior-year training.  For a component we first
    retain that component's highest-scored completed-bar decision per event,
    then evaluate its Top250 event ranking.  Outcomes are read only after ranking
    and are never fed back into training, thresholding or deployment.
    """
    def g(e,name):
        p=e.get("pred",{});a=p.get("admission",{});ct=p.get("contrastive_winner",{})
        table={
          "DEPLOYED_SCORE":float(e.get("score",-999.0)),
          "RAW_META_SCORE":float(p.get("raw_meta_score",-999.0)),
          "LANE_WIN":float(p.get("win",0.0)),
          "LANE_MEAN":float(p.get("mean",-999.0)),
          "LANE_LCB":float(p.get("lcb",-999.0)),
          "BEST_PROBABILITY":float(p.get("best_probability",0.0)),
          "STOP_ADVANTAGE":float(e.get("stop_advantage",p.get("stop_advantage",-999.0))),
          "ENTER_RAW":float(a.get("enter",0.0)),
          "ENTER_LCB":float(a.get("enter_lcb",-999.0)),
          "ENTER_ADVANTAGE_LCB":float(a.get("advantage_lcb",-999.0)),
          "CALIBRATED_ENTER":float(p.get("r4_calibrated_enter",0.0)),
          "CALIBRATED_LCB":float(p.get("r4_calibrated_lcb",-999.0)),
          "CONTRASTIVE":float(ct.get("score",0.0)),
          "CONTRASTIVE_MEDIAN":float(ct.get("median",0.0)),
          "YEAR_Q25":float(p.get("year_expert_q25",0.0)),
          "YEAR_MIN":float(p.get("year_expert_min",0.0)),
          "NEG_YEAR_DISPERSION":-float(p.get("year_expert_dispersion",999.0))
        }
        return table[name]
    names=("DEPLOYED_SCORE","RAW_META_SCORE","LANE_WIN","LANE_MEAN","LANE_LCB",
           "BEST_PROBABILITY","STOP_ADVANTAGE","ENTER_RAW","ENTER_LCB",
           "ENTER_ADVANTAGE_LCB","CALIBRATED_ENTER","CALIBRATED_LCB",
           "CONTRASTIVE","CONTRASTIVE_MEDIAN","YEAR_Q25","YEAR_MIN","NEG_YEAR_DISPERSION")
    out={}
    for name in names:
        by=defaultdict(list)
        for e in decisions:
            s=e["s"];by[(s["window"],event_identity(s["setup"]))].append(e)
        reps=[]
        for vv in by.values():
            e=max(vv,key=lambda z:(g(z,name),float(z.get("score",-999.0)),z["s"]["route"]))
            reps.append((g(e,name),e["s"]))
        reps.sort(key=lambda z:(z[0],z[1]["route"]),reverse=True)
        top=[s for _,s in reps[:MIN_N]]
        m=_diag_metrics(top)
        vals=[z for z,_ in reps]
        wins=[1.0 if float(s["y"])>0.0 else 0.0 for _,s in reps]
        # A simple rank-biserial-style separation diagnostic; positive means
        # winners receive higher causal component scores on average.
        wp=[vals[i] for i in range(len(vals)) if wins[i]>0]
        lp=[vals[i] for i in range(len(vals)) if wins[i]<=0]
        sep=(statistics.mean(wp)-statistics.mean(lp)) if wp and lp else 0.0
        out[name]={"top250":m,"pass":gate(m),"available_events":len(reps),
                   "winner_score_minus_loser_score":sep}
    best=max(out.items(),key=lambda kv:(kv[1]["top250"]["win_rate"],
                                       kv[1]["top250"]["mean_r"],
                                       kv[1]["top250"]["pf_r"])) if out else (None,None)
    return {"type":"DIAGNOSTIC_BURNED_COMPONENT_RANKING_ONLY__NEVER_TRAINED",
            "components":out,"best_component":best[0]}

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

# Fail before any expensive tournament work if a diagnostic dependency was
# accidentally removed by a future refactor.
for _required_fn in ("_diag_metrics","_oracle_top250","fit_mechanism_heads_from_samples",
                     "fit_admission_bundle","fit_contrastive_winner_ranker",
                     "fit_source_precision_bundle","_fit_r6_common_calibrator","_r6_arbitrate",
                     "meta_lane_decisions","admission_lane_context",
                     "_fit_r4_meta_policy","_apply_r4_meta_policy","_fit_r4_tournament"):
    if not callable(globals().get(_required_fn)):
        raise SystemExit("V74 evaluator preflight missing callable "+_required_fn)
_required_modes=("R6_COMMON_UTILITY","R6_WIN_LCB","R6_WIN_PROB","R6_MEAN_LCB","R6_UTILITY_PLUS_STOP","R8_MATCHED_UTILITY","R8_MATCHED_WIN_LCB","R8_MATCHED_MEAN_LCB")
if tuple(globals().get("R6_SEMANTIC_SCORE_MODES",()))!=_required_modes:
    raise SystemExit("V74 evaluator preflight invalid R6 semantic score mode contract")

checks=telemetry_guard()
summary={"version":"HarmonyBot V74 One-Shot Family-Native Causal Action Selector",
 "architecture":"V74_R8_SURVIVAL_NATIVE_COUNTERFACTUAL_ADMISSION__HARD_NEGATIVE_PRECISION__CAUSAL_STOPPING",
 "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,
         "min_win_rate":MIN_WR,"min_average_rr":MIN_AVG_RR,"lcb95_gt":0.0},
 "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
 "policy":{"actions":"EARLY_OR_LATE_COMPLETED_BAR_ENTRY_ACTION__RAW_F00_EARLY__PREENTRY_CONFIRMATION_F20_F30_LATE",
           "harmonic_completion":"DIRECTION_TIME_D_EVENT_IDENTITY__MULTI_GEOMETRY_IS_CONFLUENCE_NOT_SUPPLY",
           "reaction_state":"CAUSAL_FEATURE_NOT_HARD_FILTER","physical_route_contract":"EVENT_NATIVE_CANONICAL_EVENT_FULL_COMPLETED_BAR_ENTRY_TIMING__EARLY_F00_M05_M10_M15__LATE_PREENTRY_F20_F30__SURVIVAL_FRESH__NETRR_GE230","v75_management_variants_excluded":True,"all_entry_maturity_stages_completed_bar_only":True,
           "route_choice":"SURVIVAL_NATIVE_ROUTE_SELECTION__EARLY_LATE_FAILURE_SHADOW_ONLY",
           "optimal_stopping":"SURVIVAL_NATIVE_ENTER_DEFER_REJECT__PWL_DISTRIBUTION__CAUSAL_CONTINUATION_VALUE",
           "admission":"SURVIVAL_ONLY_PRIMARY_CAPITAL_ADMISSION__ROUTE_FAMILY_REGIME_COUNTERFACTUAL_PRIOR__HARD_NEGATIVE_PRECISION_REFIT",
           "training_coverage_target_per_year":TRAIN_COVERAGE,
           "family_hierarchy":"12_FAMILY_CANONICAL_IDENTITY__SURVIVAL_PRIMARY__OTHER_LANES_SHADOW__NO_FAMILY_BLACKLIST",
           "no_trigger_posttrigger_lock_future_state":True,
           "canonical_family_blanket_blacklist":False,"grid":False,
           "v75_profit_capture_used":False},
 "folds":{},"validation_used":False,"fresh_used":False,"telemetry_contract_checks":checks}
models={"architecture":summary["architecture"],"folds":{}}

def evaluate_burned_fold(test):
    ft=time.perf_counter();test_year=int(test[1:])
    tw=[w for w in ALL if int(w[1:])<test_year]
    # Preserve the original global row/sample order exactly: deterministic
    # training subsampling depends on sequence order even when membership matches.
    tr=[r for r in rows if r["window"] in tw];te=[r for r in rows if r["window"]==test]
    tr_samples=[s for s in _ALL_SAMPLES if s["window"] in tw]
    te_samples=[s for s in _ALL_SAMPLES if s["window"]==test]
    policy,_=fit_policy(tr,tr_samples)
    sel,test_samples,dec=apply_policy(policy,te,te_samples);m,mr=metric_selected(sel)
    two_axis=two_axis_oracle_diagnostic(test_samples,dec,sel)
    score_threshold_oracle=score_threshold_oracle_diagnostic(dec)
    routes=Counter(r.get("sequential_key","NONE") for r in mr)
    fams=Counter(r["family"] for r in mr);acts=Counter(r["action"] for r in mr)
    srcs=Counter(x.split("|",1)[0] for x in routes.elements())
    ps=gate(m)
    fold={**m,"pass":ps,"training_windows":tw,
      "entry_threshold":policy["threshold"],"stopping_margin":policy.get("stop_margin",-math.inf),
      "training_coverage_target":TRAIN_COVERAGE,
      "training_gate":policy.get("training_gate"),"training_worst_gate_margin":policy.get("training_worst_gate_margin"),
      "training_supply":policy["training_supply"],"training_year_metrics":policy["training_metrics"],
      "training_oracle_admission":policy.get("training_oracle_admission",{}),
      "admission_sweep":policy.get("admission_sweep",{}),
      "test_legal_actions":len(test_samples),"test_decision_events":len(dec),
      "two_axis_oracle":two_axis,
      "score_threshold_oracle":score_threshold_oracle,
      "component_rank_diagnostic":_component_rank_diagnostic(dec),
      "selected_route_counts":dict(routes),"selected_family_counts":dict(fams),
      "selected_action_counts":dict(acts),"selected_source_counts":dict(srcs),
      "runtime_seconds":round(time.perf_counter()-ft,3)}
    return test,fold,policy

t0=time.perf_counter()
# Build causal action samples once in the parent. Fork workers then share these
# pages read-only; no fold rebuilds route vectors or harmonic precision features.
_ALL_SAMPLES=make_samples(rows)
_ALL_SURVIVAL_SAMPLES=[s for s in _ALL_SAMPLES if s.get("source")=="SURVIVAL"]
# Fail closed on any ordering/content drift introduced by prebuilding. A direct
# single-window rebuild must be byte-for-byte numerically equivalent and ordered.
_probe_window="Y2020" if "Y2020" in ALL else ALL[0]
_probe_rows=[r for r in rows if r["window"]==_probe_window]
_probe_direct=make_samples(_probe_rows)
_probe_cached=[s for s in _ALL_SAMPLES if s["window"]==_probe_window]
def _sample_parity_key(s):
    return (s["window"],s["setup"],s["family"],s["action"],s["source"],s["base"],
            s["route"],int(s["bar"]),int(s["bars"]),float(s["y"]),tuple(float(x) for x in s["x"]))
if len(_probe_direct)!=len(_probe_cached) or any(
        _sample_parity_key(a)!=_sample_parity_key(b)
        for a,b in zip(_probe_direct,_probe_cached)):
    raise SystemExit("V74 prebuild sample parity failure")
print("[V74-PREBUILD-PARITY] pass=true window="+_probe_window+
      " n="+str(len(_probe_cached)),flush=True)
print("[V74-PREBUILD] rows="+str(len(rows))+" samples="+str(len(_ALL_SAMPLES))+
      " precision_cache="+str(len(_HARMONIC_PRECISION_CACHE)),flush=True)

# R8 consumes the same expanding-window SURVIVAL inner years across the
# three burned folds.  Compute them once and share read-only between folds.
_inner_needed=sorted(set(
    vw for test in BURNED
    for vw in (lambda yrs:(yrs[2:])[-min(3,len(yrs[2:])):])(
        sorted([w for w in ALL if int(w[1:])<int(test[1:])],key=lambda w:int(w[1:])))
))
_t_inner=time.perf_counter();_INNER_SURVIVAL_OOF_CACHE={}
if os.environ.get("V74_DISABLE_SHARED_INNER_CACHE","0")!="1" and _inner_needed:
    try:
        _ctx=mp.get_context("fork")
        _workers=min(len(_inner_needed),max(1,int(os.cpu_count() or 1)))
        if _workers>1:
            with _ctx.Pool(processes=_workers) as _pool:
                _inner_results=_pool.map(_compute_shared_inner_survival_year,_inner_needed)
        else:
            _inner_results=[_compute_shared_inner_survival_year(w) for w in _inner_needed]
        _INNER_SURVIVAL_OOF_CACHE=dict(_inner_results)
    except OSError as ex:
        print("[V74-R8-SURVIVAL-INNER-CACHE-FALLBACK] infrastructure="+repr(ex),flush=True)
        _INNER_SURVIVAL_OOF_CACHE={}
_inner_cache_seconds=round(time.perf_counter()-_t_inner,3)
print("[V74-R8-SURVIVAL-INNER-CACHE] years="+str(_inner_needed)+" built="+
      str(sorted(_INNER_SURVIVAL_OOF_CACHE))+" seconds="+str(_inner_cache_seconds),flush=True)
_R4_META_MODEL_CACHE={}
_meta_cache_seconds=0.0

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
    except OSError as ex:
        # Only runner/fork infrastructure failures may fall back. Programming,
        # model, data-contract and parity errors must fail immediately instead
        # of silently paying for a second full sequential tournament.
        print("[V74-PARALLEL-FALLBACK] infrastructure="+repr(ex),flush=True)
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
champ="V74_R8_SURVIVAL_NATIVE_COUNTERFACTUAL_ADMISSION" if alpha else None
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
summary["performance_engine"]={"immutable_sample_prebuild":True,
 "shared_unique_inner_oof_years":sorted(globals().get("_INNER_SURVIVAL_OOF_CACHE",{})),
 "survival_inner_oof_reuse":True,"prepared_inference_reuse":True,
 "inner_cache_build_seconds":globals().get("_inner_cache_seconds"),
 "meta_prefix_cache":False,"meta_prefix_parallel":False,
 "parity_fail_closed":True}
summary["root_cause_rearchitecture"]="V74_R8_SURVIVAL_NATIVE_COUNTERFACTUAL_ADMISSION"
summary["component_rank_diagnostic_version"]="EVENT_TOP250_COMPONENT_RANK_V1"
summary["event_identity_weighting_contract"]="YEAR_EQUAL__INDEPENDENT_EVENT_EQUAL__ROUTE_MULTIPLICITY_NEUTRAL__EARLY_ALIAS_DEDUP"
summary["survival_primary_alpha"]=True
summary["generic_early_late_failure_shadow_only"]=True
summary["all_causal_lanes_active"]=False
summary["lane_preserving_until_post_admission"]=False
summary["cross_source_pair_ranker_removed_at_meta"]=True
summary["strict_source_native_admission"]=True
summary["global_runtime_admission_fallback"]=False
summary["r6_source_native_precision_retrieval"]=True
summary["r6_forward_oof_common_scale_calibration"]=True
summary["r6_mode_specific_post_admission_arbitration"]=True
summary["r6_hierarchical_source_shrinkage"]=True
summary["r7_common_causal_trajectory_all_sources"]=True
summary["r7_common_path_direct_meta_input"]=True
summary["r7_common_path_fail_closed_completeness"]=True
summary["r7_future_information_used"]=False
summary["r7_causal_reaction_state_telemetry"]="ROUTE_STATE_V4_80D__SURVIVAL_PATH_V4_48D__COMPLETED_M1_ONLY__NO_FUTURE_TELEMETRY"
summary["r6_causal_trajectory_representation"]="SUPERSEDED_BY_R7_ROUTE_STATE_V4_AND_SURVIVAL_PATH_V4"
summary["source_head_missing_feature_policy"]="EVENT_YEAR_BALANCED_SOURCE_PRIOR__NEVER_GLOBAL_RUNTIME_HEAD"
summary["fast_replay_supersession_contract"]="R7_GENERATION__STALE_HEAD_AUTO_TERMINATE__35M_HARD_TIMEOUT"
summary["r7_evidence_generation"]="R7_CAUSAL_REACTION_STATE_TELEMETRY__EXACT_2016_2023_RAPID_REGENERATION"
summary["r8_survival_counterfactual_primary"]=True
summary["r8_hard_negative_precision_refit"]=True
summary["r8_route_family_regime_hierarchical_prior"]=True
summary["r8_other_lanes_shadow_only"]=True
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
