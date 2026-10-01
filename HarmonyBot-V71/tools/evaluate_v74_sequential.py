#!/usr/bin/env python3
"""
V74 barbell survival evaluator.

Run #55 froze A-L negative evidence, Run #60 froze the 1.25R/1.50R cardinality
ceiling, Run #63 established early-entry supply, Run #64 showed barbell exits
still inherited over-tight entry stops, and Run #65 proved a second shadow proof
creates another N<250/year ceiling. This evaluator tests only the preregistered
micro-positive-arm +0.05R/+0.10R/+0.15R single-basket runner routes. Every route and score
threshold is selected from training windows only. Validation/Fresh are never loaded here.
"""
import json,math,pathlib,statistics,sys,time
from v74_model_lib import load_rows,metrics,SEQUENTIAL_KEYS,SEQUENTIAL_STATE_FEATURE_COUNT

BASE_KEYS=[]
for _k in SEQUENTIAL_KEYS:
    _b=_k.rsplit("_F",1)[0]
    if _b not in BASE_KEYS:BASE_KEYS.append(_b)
EVAL_KEYS=[_b+"_F"+_f for _b in BASE_KEYS for _f in ("00","10","20","30")]

root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
RESEARCH=[f"Y{y}" for y in range(2016,2021)]
BURNED=["Y2021","Y2022","Y2023"];ALL=RESEARCH+BURNED
MIN_N=250;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_RR=2.30
ABCD_TRAIN_MIN_N=300;ABCD_TRAIN_MIN_PF=1.20;Z=1.645
rows=load_rows(root,ALL)
if not rows:raise SystemExit("no V74 tournament rows")
if sum(len(r.get("sequential_entry_state",{})) for r in rows)==0:
    raise SystemExit("V74 telemetry schema mismatch: zero per-route sequential entry-state vectors")

def quantile(vals,q):
    if not vals:return math.inf
    xs=sorted(float(x) for x in vals);p=(len(xs)-1)*q;lo=int(math.floor(p));hi=int(math.ceil(p))
    return xs[lo] if lo==hi else xs[lo]*(hi-p)+xs[hi]*(p-lo)

def gate_metrics(m):
    return bool(m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and
                m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0)

def route_meta(key):
    level="025" if "_R025_" in key else "050"
    mode="D" if "_D_" in key else "H"
    return level,level+mode

def with_outcome(r,key):
    base=key.rsplit("_F",1)[0];frac=key.rsplit("_F",1)[1]
    source_key=key
    if frac in ("00","10"):
        k20=base+"_F20";k30=base+"_F30"
        y20=r.get("sequential",{}).get(k20);y30=r.get("sequential",{}).get(k30)
        rr=r.get("sequential_rr",{}).get(k20);source_key=k20
        if y20 is None or y30 is None:return None
        d=float(y30)-float(y20);v=float(y20)-(2.0 if frac=="00" else 1.0)*d
    else:
        v=r.get("sequential",{}).get(key);rr=r.get("sequential_rr",{}).get(key)
    level,_=route_meta(key)
    state=r.get("sequential_state",{}).get(level)
    # F00/F10 share the exact causal decision time and runner path of the logged
    # F20/F30 pair; only the crystallized fraction changes, so their payoff is an
    # exact linear counterfactual rather than a new future-dependent action.
    entry_state=r.get("sequential_entry_state",{}).get(source_key)
    if v is None or rr is None or state is None or entry_state is None:return None
    if len(state)!=SEQUENTIAL_STATE_FEATURE_COUNT or len(entry_state)!=SEQUENTIAL_STATE_FEATURE_COUNT:return None
    try:v=float(v);rr=float(rr)
    except Exception:return None
    if not math.isfinite(v) or not math.isfinite(rr) or rr+1e-9<MIN_RR:return None
    q=dict(r);q["native_r"]=r["r"];q["r"]=v;q["sequential_key"]=key
    q["sequential_planned_rr"]=rr;q["sequential_level"]=level
    q["sequential_state_vector"]=list(state);q["sequential_entry_state_vector"]=list(entry_state)
    return q

def seq_rows(xs,key):
    z=[]
    for r in xs:
        q=with_outcome(r,key)
        if q is not None:z.append(q)
    return z

def hvec(r):
    cached=r.get("_hvec")
    if cached is not None:return cached
    s=r.get("sequential_state_vector");e=r.get("sequential_entry_state_vector")
    if s is None or e is None or len(s)!=SEQUENTIAL_STATE_FEATURE_COUNT or len(e)!=SEQUENTIAL_STATE_FEATURE_COUNT:return None
    f=list(r.get("features",[]))
    delta=[float(e[j])-float(s[j]) for j in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    return f+list(s)+list(e)+delta

def stat_target(xs,win_field=None):
    if not xs:return {"n":0,"mean":0.0,"win":0.0,"sigma":10.0}
    v=[float(r["r"]) for r in xs];n=len(v);sd=statistics.stdev(v) if n>1 else 10.0
    if win_field is None:
        win=sum(x>0 for x in v)/n
    else:
        win=sum(float(r.get(win_field,r["r"]))>0 for r in xs)/n
    return {"n":n,"mean":sum(v)/n,"win":win,"sigma":max(.05,sd)}

def stat(xs):
    return stat_target(xs,None)

def stable_feature_frontier(anchor_rows,train_windows,top_k=24):
    pairs=[(r,hvec(r)) for r in anchor_rows];pairs=[z for z in pairs if z[1] is not None]
    if not pairs:return {"indices":[],"weights":[],"diagnostics":[]}
    q=[z[0] for z in pairs];vec=[z[1] for z in pairs];p=len(vec[0])
    meds=[statistics.median(v[j] for v in vec) for j in range(p)]
    gs=max(.05,stat(q)["sigma"]);diag=[]
    ids_by_year={w:[] for w in train_windows}
    for i,r in enumerate(q):
        if r["window"] in ids_by_year:ids_by_year[r["window"]].append(i)
    for j in range(p):
        yr=[];min_side=10**9
        for w in train_windows:
            ids=ids_by_year[w]
            lo=[q[i] for i in ids if vec[i][j]<meds[j]];hi=[q[i] for i in ids if vec[i][j]>=meds[j]]
            if len(lo)<24 or len(hi)<24:continue
            a=stat(lo);b=stat(hi);min_side=min(min_side,len(lo),len(hi))
            eff=(b["mean"]-a["mean"])/gs+1.25*(b["win"]-a["win"])
            if abs(eff)>1e-12:yr.append(eff)
        if len(yr)<4:
            diag.append((0.0,j,0.0,0.0,len(yr)));continue
        medeff=statistics.median(yr);cons=abs(sum(1 if x>0 else -1 for x in yr))/len(yr)
        floor=min(abs(x) for x in yr);support=min(1.0,math.sqrt(max(1,min_side)/120.0))
        score=(.60*abs(medeff)+.40*floor)*cons*support
        diag.append((score,j,medeff,cons,len(yr)))
    diag.sort(key=lambda z:(z[0],-z[1]),reverse=True)
    keep=[z for z in diag if z[0]>0][:top_k]
    if len(keep)<8:
        keep=[z for z in diag[:min(top_k,len(diag))] if z[0]>=0]
    raw=[max(1e-6,z[0]) for z in keep];sw=sum(raw) or 1.0
    return {"indices":[z[1] for z in keep],"weights":[x/sw for x in raw],
            "diagnostics":[{"index":z[1],"score":z[0],"median_effect":z[2],"sign_consistency":z[3],"supported_years":z[4]} for z in keep]}

def train_labeled(q,key,win_field=None,feature_frontier=None):
    pairs=[(r,hvec(r)) for r in q];pairs=[z for z in pairs if z[1] is not None]
    q=[z[0] for z in pairs];vec=[z[1] for z in pairs]
    if not q:return {"key":key,"medians":[],"global":stat_target([],win_field),"family_action":{},"bins":[],"feature_indices":[],"feature_weights":[],"win_target":win_field or "r"}
    p=len(vec[0])
    idx=list(feature_frontier.get("indices",[])) if feature_frontier else list(range(p))
    if not idx:idx=list(range(p))
    weights=list(feature_frontier.get("weights",[])) if feature_frontier else [1.0/len(idx)]*len(idx)
    if len(weights)!=len(idx):weights=[1.0/len(idx)]*len(idx)
    med=[statistics.median(v[j] for v in vec) for j in idx]
    glob=stat_target(q,win_field);fa={}
    for fam in sorted({r["family"] for r in q}):
        for action in ("REVERSAL","CONTINUATION"):
            z=[r for r in q if r["family"]==fam and r["action"]==action]
            if z:fa[fam+"|"+action]=stat_target(z,win_field)
    bins=[]
    for pos,j in enumerate(idx):
        lo=[r for r,v in zip(q,vec) if v[j]<med[pos]]
        hi=[r for r,v in zip(q,vec) if v[j]>=med[pos]]
        bins.append({"lo":stat_target(lo,win_field),"hi":stat_target(hi,win_field)})
    return {"key":key,"medians":med,"global":glob,"family_action":fa,"bins":bins,
            "feature_indices":idx,"feature_weights":weights,"win_target":win_field or "r"}

def train(xs,key):
    return train_labeled(seq_rows(xs,key),key)

def action_baselines(xs):
    d={}
    for r in xs:
        vals=[]
        for key in EVAL_KEYS:
            q=with_outcome(r,key)
            if q is not None:vals.append(float(q["r"]))
        if vals:d[(r["window"],r["setup"])]=statistics.median(vals)
    return d

def train_advantage(xs,key,baselines):
    q=[]
    for r in seq_rows(xs,key):
        b=baselines.get((r["window"],r["setup"]))
        if b is None:continue
        z=dict(r);z["route_actual_r"]=float(r["r"]);z["r"]=float(r["r"])-float(b);q.append(z)
    return train_labeled(q,key,"route_actual_r")

def score(model,r):
    v=hvec(r);g=model.get("global",{})
    if v is None or not model.get("medians") or int(g.get("n",0))<80:
        return {"score":-999.0,"mean":0.0,"win":0.0,"lcb":-999.0,"support":0}
    gm=float(g.get("mean",0.0));gw=float(g.get("win",0.0));gs=float(g.get("sigma",10.0))
    fa=model.get("family_action",{}).get(r["family"]+"|"+r["action"],{"n":0,"mean":gm,"win":gw})
    fn=int(fa.get("n",0));fw=fn/(fn+80.0)
    pm=gm+fw*(float(fa.get("mean",gm))-gm);pw=gw+fw*(float(fa.get("win",gw))-gw)
    ms=[];ws=[];supp=[];idx=model.get("feature_indices") or list(range(len(v)))
    fwts=model.get("feature_weights") or ([1.0/len(idx)]*len(idx) if idx else [])
    for pos,j in enumerate(idx):
        x=v[j];b=model["bins"][pos]["hi" if x>=model["medians"][pos] else "lo"];n=int(b.get("n",0));sh=n/(n+60.0)
        ms.append(pm+sh*(float(b.get("mean",gm))-gm));ws.append(pw+sh*(float(b.get("win",gw))-gw));supp.append(n)
    sw=sum(fwts) or 1.0
    wm=sum(w*x for w,x in zip(fwts,ms))/sw if ms else pm
    ww=sum(w*x for w,x in zip(fwts,ws))/sw if ws else pw
    mean=(pm+wm)/2.0;win=max(0.0,min(1.0,(pw+ww)/2.0))
    support=max(1,min([fn if fn>0 else int(g.get("n",1))]+supp));lcb=mean-Z*gs/math.sqrt(support)
    return {"score":lcb+.75*win,"mean":mean,"win":win,"lcb":lcb,"support":support}

def scored_rows(xs,key,model):
    z=[]
    for r in seq_rows(xs,key):
        q=dict(r);q["_hz"]=score(model,r);z.append(q)
    return z

def apply(scored,threshold,abcd_allowed=True):
    z=[]
    for r in scored:
        if r["family"]=="ABCD" and not abcd_allowed:continue
        h=r["_hz"]
        if h["score"]+1e-12<threshold:continue
        q=dict(r);q.pop("_hz",None);q["seq_pred_mean"]=h["mean"];q["seq_pred_win"]=h["win"]
        q["seq_pred_lcb"]=h["lcb"];q["seq_support"]=h["support"];q["seq_score"]=h["score"];z.append(q)
    return z

def gate_margin(m):
    if m["n"]<=0:return -999.0
    vals=[m["n"]/MIN_N,m["mean_r"]/MIN_MEAN,m["pf_r"]/MIN_PF,
          m["win_rate"]/MIN_WR,m["average_rr"]/MIN_RR]
    # LCB is a veto, then a smooth robustness reward. This never changes the hard gate.
    lcb_margin=1.0+m["lcb_r"]/.25
    vals.append(lcb_margin)
    return min(vals)

def choose(train_rows,train_windows,q):
    candidates=[]
    for key in EVAL_KEYS:
        model=train(train_rows,key);sr=scored_rows(train_rows,key,model)
        vals=[r["_hz"]["score"] for r in sr if math.isfinite(r["_hz"]["score"]) and r["_hz"]["score"]>-900]
        if not vals:continue
        th=quantile(vals,q);sel=apply(sr,th,True);agg=metrics(sel);yearly=[]
        for w in train_windows:
            ym=metrics([r for r in sel if r["window"]==w])
            if ym["n"]>=180:yearly.append(ym)
        if agg["n"]<1000 or len(yearly)<len(train_windows):continue
        margins=[gate_margin(z) for z in yearly]
        robust=min(margins)+.25*statistics.median(margins)
        wl=min(z["lcb_r"] for z in yearly);wm=min(z["mean_r"] for z in yearly)
        ww=min(z["win_rate"] for z in yearly);wr=min(z["average_rr"] for z in yearly)
        candidates.append((robust,wl,wm,ww,wr,agg["n"],key,model,th,agg))
    candidates.sort(key=lambda z:(z[0],z[1],z[2],z[3],z[4],z[5],z[6]),reverse=True)
    return candidates[0] if candidates else None

summary={
 "version":"HarmonyBot V74 Candidate",
 "architecture":"CAUSAL_MICRO_ARM_CLOSE_ONLY_RUNNER",
 "legacy_negative_evidence":[
  {"source_run_id":36863429034,"run":55,"result":"A-L_FAIL"},
  {"source_run_id":36870479524,"run":60,"result":"1P25_1P50_RAW_N_LT_250"},
  {"source_run_id":36873141009,"run":63,"result":"EARLY_FIRST_PASSAGE_SUPPLY_OK_BUT_WR_MEAN_PF_RR_JOINT_FAIL"},
  {"source_run_id":36876206286,"run":64,"result":"BARBELL_IMPROVED_2022_BUT_2023_FAIL__PLANNED_RR_TOO_HIGH"},
  {"source_run_id":36877930018,"run":65,"result":"SECOND_SHADOW_MICRO_STOP_N_CEILING"},
  {"source_run_id":36879436103,"run":66,"result":"3_TO_4R_NORMALIZED_EARLY_COMMIT_FAIL"},
  {"source_run_id":36880885164,"run":67,"result":"PARTIAL_CRYSTALLIZATION_FAIL"},
  {"source_run_id":36909189452,"run":68,"result":"NORMALIZED_SECOND_SHADOW_ORACLE_TOP250_STILL_FAILS_MEAN_AND_WR"},
  {"source_run_id":36910430560,"run":69,"result":"INTRABAR_LADDER_IMPROVES_2023_SIGN_BUT_ORACLE_BEST_ROUTE_PER_SETUP_TOP250_MEAN_0P779_LT_0P90"},
  {"source_run_id":36912836008,"run":72,"result":"ACTION_ENVELOPE_FEASIBLE_BUT_ENTRY_STATE_ARBITRATION_OOF_FAIL"},
  {"source_run_id":36915977056,"run":74,"result":"MICRO_ARM_INTRABAR_BE_FAILS_RIGHT_TAIL__OOF_WR_AND_MEAN_BELOW_GATE"}],
 "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
 "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,
         "min_win_rate":MIN_WR,"min_average_rr":MIN_RR,"lcb95_gt":0.0},
 "policy":{
   "capital":"LATER_COMPLETED_M1_HOLD_AFTER_ORIGINAL_0P25_OR_0P50_FIRST_PASSAGE",
   "entry_risk_geometry":"CANONICAL_TARGET_BACKSOLVES_INITIAL_STOP_AT_3P5R_OR_4P0R_BOUNDED_BY_STRUCTURAL_INVALIDATION",
   "post_entry_barbell":"MICRO_FIRST_PASSAGE_PLUS_LATER_COMPLETED_HOLD_CRYSTALLIZES_F00_F10_F20_F30__RUNNER_KEEPS_STRUCTURAL_STOP_AND_CANONICAL_TARGET__EXIT_ONLY_ON_LATER_COMPLETED_CLOSE_BELOW_ENTRY",
   "candidates":EVAL_KEYS,"adverse_cut":"COMPLETED_CLOSE_ONLY_BEFORE_POSITIVE_ARM",
   "same_bar":"STRUCTURAL_STOP_THEN_TARGET_THEN_CLOSE_ONLY_FRONTIER_THEN_ADVERSE_CLOSE_THEN_NEW_ARM",
   "no_stop_widening":True,"partial_exit":"SINGLE_BASKET_ONLY","grid":False,"minimum_route_net_rr":MIN_RR,
   "selection":"TRAINING_ONLY_HIERARCHICAL_PARTIAL_POOLING_PLUS_ROBUST_GATE_MARGIN"},
 "models":{},"validation_used":False,"fresh_used":False}
models_blob={"architecture":"V74_CAUSAL_FAMILY_NATIVE_COUNTERFACTUAL_ACTION_RANKER","shared_folds":{},"models":{}}
passers=[]
# Fixed, preregistered burned-calibration candidates. These vary only training-only
# retention and the relative-vs-absolute action-value blend; no Validation/Fresh.
VARIANTS=[
 ("CG_ACTUALWIN_AUTO_STABLE",None,0.65)
]
_eval_t0=time.perf_counter()

def route_year_stability(tr,key,train_windows):
    q=seq_rows(tr,key);out={}
    for w in train_windows:out[w]=stat([r for r in q if r["window"]==w])
    valid=[z for z in out.values() if z["n"]>=120]
    return {"years":out,
            "mean_floor":min((z["mean"] for z in valid),default=-999.0),
            "win_floor":min((z["win"] for z in valid),default=0.0),
            "positive_years":sum(z["mean"]>0 for z in valid),
            "supported_years":len(valid)}

def family_action_route_stability(tr,key,train_windows):
    q=seq_rows(tr,key);res={}
    for fam in sorted({r["family"] for r in q}):
        for action in ("REVERSAL","CONTINUATION"):
            cell=[r for r in q if r["family"]==fam and r["action"]==action]
            if not cell:continue
            overall=stat(cell);ys={}
            for w in train_windows:
                z=[r for r in cell if r["window"]==w]
                if z:ys[w]=stat(z)
            supported=[z for z in ys.values() if z["n"]>=20]
            # Shrink family/action evidence toward route parent instead of ever
            # blacklisting a canonical family (especially AB=CD).
            res[fam+"|"+action]={"overall":overall,"years":ys,
                "mean_floor":min((z["mean"] for z in supported),default=overall["mean"]),
                "win_floor":min((z["win"] for z in supported),default=overall["win"]),
                "supported_years":len(supported)}
    return res

def opportunity_ranked(rows_,raw_models,adv_models,route_stability,fam_stability,adv_weight):
    by_setup={}
    for key in EVAL_KEYS:
        rm=raw_models[key];am=adv_models[key];rst=route_stability[key];fst=fam_stability[key]
        for r in seq_rows(rows_,key):
            raw=score(rm,r);adv=score(am,r)
            if min(raw["support"],adv["support"])<20:continue
            if raw["score"]<=-900 or adv["score"]<=-900:continue
            cell=fst.get(r["family"]+"|"+r["action"])
            if cell:
                cn=int(cell["overall"]["n"]);sh=cn/(cn+80.0)
                fam_mean=sh*float(cell["mean_floor"])
                fam_win=sh*float(cell["win_floor"])
            else:fam_mean=fam_win=0.0
            year_penalty=min(0.0,float(rst["mean_floor"]))
            raw_u=float(raw["lcb"])+0.55*float(raw["mean"])+0.65*float(raw["win"])
            adv_u=float(adv["lcb"])+0.70*float(adv["mean"])+0.55*float(adv["win"])
            utility=adv_weight*adv_u+(1.0-adv_weight)*raw_u+0.15*fam_mean+0.10*fam_win+0.35*year_penalty
            q=dict(r);q["_raw"]=raw;q["_adv"]=adv;q["_route_utility"]=utility
            by_setup.setdefault((r["window"],r["setup"]),[]).append(q)
    winners=[]
    for _,cand in by_setup.items():
        cand.sort(key=lambda r:(r["_route_utility"],r["_adv"]["lcb"],r["_raw"]["lcb"],r["sequential_key"]),reverse=True)
        if not cand:continue
        best=cand[0];second=cand[1]["_route_utility"] if len(cand)>1 else -999.0
        q=dict(best);raw=q.pop("_raw");adv=q.pop("_adv")
        q["route_utility"]=q.pop("_route_utility");q["route_margin"]=q["route_utility"]-second
        q["raw_pred_mean"]=raw["mean"];q["raw_pred_win"]=raw["win"];q["raw_pred_lcb"]=raw["lcb"]
        q["adv_pred_mean"]=adv["mean"];q["adv_pred_win"]=adv["win"];q["adv_pred_lcb"]=adv["lcb"]
        q["route_support"]=min(raw["support"],adv["support"]);winners.append(q)
    return winners

def select_ranked(ranked,threshold):
    return [r for r in ranked if r["route_utility"]+1e-12>=threshold]

def assert_ranked_integrity(ranked,allowed_windows):
    seen=set()
    for r in ranked:
        ident=(r["window"],r["setup"])
        if ident in seen:raise SystemExit("V74 ranked duplicate setup identity: "+repr(ident))
        seen.add(ident)
        if r["window"] not in allowed_windows:raise SystemExit("V74 ranked window leakage: "+str(r["window"]))
        if r["sequential_key"] not in EVAL_KEYS:raise SystemExit("V74 illegal ranked route: "+str(r["sequential_key"]))
        if not math.isfinite(float(r["route_utility"])):raise SystemExit("V74 non-finite route utility")
        if float(r["route_margin"]) < -1e-12:raise SystemExit("V74 negative route winner margin")

def build_route_cache(xs):
    # Exact-semantics optimization: materialize each legal route once per fold/split.
    # No outcome, threshold, model or ordering rule changes.
    cache={key:[] for key in EVAL_KEYS}
    for r in xs:
        for key in EVAL_KEYS:
            q=with_outcome(r,key)
            if q is None:continue
            v=hvec(q)
            if v is None:continue
            q["_hvec"]=v
            cache[key].append(q)
    return cache

def action_baselines_cached(cache):
    by_setup={}
    for key in EVAL_KEYS:
        for r in cache[key]:
            by_setup.setdefault((r["window"],r["setup"]),[]).append(float(r["r"]))
    return {k:statistics.median(v) for k,v in by_setup.items() if v}

def train_advantage_cached(q,key,baselines,feature_frontier=None):
    z=[]
    for r in q:
        b=baselines.get((r["window"],r["setup"]))
        if b is None:continue
        x=dict(r);x["route_actual_r"]=float(r["r"]);x["r"]=float(r["r"])-float(b);z.append(x)
    return train_labeled(z,key,"route_actual_r",feature_frontier)

def _stat_arrays(targets,wins):
    n=len(targets)
    if n==0:return {"n":0,"mean":0.0,"win":0.0,"sigma":10.0}
    sd=statistics.stdev(targets) if n>1 else 10.0
    return {"n":n,"mean":sum(targets)/n,"win":sum(x>0 for x in wins)/n,"sigma":max(.05,sd)}

def _training_design(q,feature_frontier):
    rows=[];vec=[]
    for r in q:
        v=hvec(r)
        if v is not None:rows.append(r);vec.append(v)
    if not rows:return {"rows":[],"indices":[],"weights":[],"medians":[],"family_action":{},"bins":[]}
    p=len(vec[0]);idx=list(feature_frontier.get("indices",[])) if feature_frontier else list(range(p))
    if not idx:idx=list(range(p))
    weights=list(feature_frontier.get("weights",[])) if feature_frontier else [1.0/len(idx)]*len(idx)
    if len(weights)!=len(idx):weights=[1.0/len(idx)]*len(idx)
    med=[statistics.median(v[j] for v in vec) for j in idx]
    fa={}
    for i,r in enumerate(rows):fa.setdefault(r["family"]+"|"+r["action"],[]).append(i)
    bins=[]
    for pos,j in enumerate(idx):
        lo=[];hi=[];m=med[pos]
        for i,v in enumerate(vec):(hi if v[j]>=m else lo).append(i)
        bins.append((lo,hi))
    return {"rows":rows,"indices":idx,"weights":weights,"medians":med,"family_action":fa,"bins":bins}

def _model_from_design(design,key,targets,wins,win_target):
    rows=design["rows"];n=len(rows)
    if n==0:return {"key":key,"medians":[],"global":_stat_arrays([],[]),"family_action":{},"bins":[],"feature_indices":[],"feature_weights":[],"win_target":win_target}
    all_ids=range(n)
    def S(ids):
        ids=list(ids)
        return _stat_arrays([targets[i] for i in ids],[wins[i] for i in ids])
    glob=S(all_ids)
    fa={k:S(ids) for k,ids in design["family_action"].items()}
    bins=[{"lo":S(lo),"hi":S(hi)} for lo,hi in design["bins"]]
    return {"key":key,"medians":design["medians"],"global":glob,"family_action":fa,"bins":bins,
            "feature_indices":design["indices"],"feature_weights":design["weights"],"win_target":win_target}

def train_raw_adv_paired_cached(q,key,baselines,feature_frontier):
    design=_training_design(q,feature_frontier);rows=design["rows"]
    raw=[float(r["r"]) for r in rows];adv=[]
    for r,v in zip(rows,raw):
        b=baselines.get((r["window"],r["setup"]))
        if b is None:raise SystemExit("V74 paired-training baseline missing")
        adv.append(v-float(b))
    return (_model_from_design(design,key,raw,raw,"r"),
            _model_from_design(design,key,adv,raw,"route_actual_r"))

def score_pair(raw_model,adv_model,r):
    v=hvec(r)
    if v is None:return score(raw_model,r),score(adv_model,r)
    if (raw_model.get("feature_indices")!=adv_model.get("feature_indices") or
        raw_model.get("medians")!=adv_model.get("medians")):
        return score(raw_model,r),score(adv_model,r)
    idx=raw_model.get("feature_indices") or list(range(len(v)))
    def init(model):
        g=model.get("global",{})
        if not model.get("medians") or int(g.get("n",0))<80:return None
        gm=float(g.get("mean",0.0));gw=float(g.get("win",0.0));gs=float(g.get("sigma",10.0))
        fa=model.get("family_action",{}).get(r["family"]+"|"+r["action"],{"n":0,"mean":gm,"win":gw})
        fn=int(fa.get("n",0));fw=fn/(fn+80.0)
        pm=gm+fw*(float(fa.get("mean",gm))-gm);pw=gw+fw*(float(fa.get("win",gw))-gw)
        return [g,gm,gw,gs,fn,pm,pw,[],[],[]]
    a=init(raw_model);b=init(adv_model)
    if a is None or b is None:return score(raw_model,r),score(adv_model,r)
    for pos,j in enumerate(idx):
        side="hi" if v[j]>=raw_model["medians"][pos] else "lo"
        for model,z in ((raw_model,a),(adv_model,b)):
            g,gm,gw,gs,fn,pm,pw,ms,ws,supp=z
            cell=model["bins"][pos][side];n=int(cell.get("n",0));sh=n/(n+60.0)
            ms.append(pm+sh*(float(cell.get("mean",gm))-gm))
            ws.append(pw+sh*(float(cell.get("win",gw))-gw));supp.append(n)
    out=[]
    for model,z in ((raw_model,a),(adv_model,b)):
        g,gm,gw,gs,fn,pm,pw,ms,ws,supp=z
        fwts=model.get("feature_weights") or ([1.0/len(idx)]*len(idx) if idx else [])
        sw=sum(fwts) or 1.0;wm=sum(w*x for w,x in zip(fwts,ms))/sw if ms else pm
        ww=sum(w*x for w,x in zip(fwts,ws))/sw if ws else pw
        mean=(pm+wm)/2.0;win=max(0.0,min(1.0,(pw+ww)/2.0))
        support=max(1,min([fn if fn>0 else int(g.get("n",1))]+supp));lcb=mean-Z*gs/math.sqrt(support)
        out.append({"score":lcb+.75*win,"mean":mean,"win":win,"lcb":lcb,"support":support})
    return out[0],out[1]

def route_year_stability_cached(q,train_windows):
    buckets={w:[] for w in train_windows}
    for r in q:
        if r["window"] in buckets:buckets[r["window"]].append(r)
    out={w:stat(buckets[w]) for w in train_windows}
    valid=[z for z in out.values() if z["n"]>=120]
    return {"years":out,
            "mean_floor":min((z["mean"] for z in valid),default=-999.0),
            "win_floor":min((z["win"] for z in valid),default=0.0),
            "positive_years":sum(z["mean"]>0 for z in valid),
            "supported_years":len(valid)}

def family_action_route_stability_cached(q,train_windows):
    cells={}
    for r in q:
        k=r["family"]+"|"+r["action"]
        c=cells.setdefault(k,{"all":[],"years":{w:[] for w in train_windows}})
        c["all"].append(r)
        if r["window"] in c["years"]:c["years"][r["window"]].append(r)
    res={}
    for k,c in cells.items():
        overall=stat(c["all"]);ys={w:stat(v) for w,v in c["years"].items() if v}
        supported=[z for z in ys.values() if z["n"]>=20]
        res[k]={"overall":overall,"years":ys,
                "mean_floor":min((z["mean"] for z in supported),default=overall["mean"]),
                "win_floor":min((z["win"] for z in supported),default=overall["win"]),
                "supported_years":len(supported)}
    return res

def build_scored_cache(cache,raw_models,adv_models):
    out={}
    for key in EVAL_KEYS:
        rm=raw_models[key];am=adv_models[key];z=[]
        for r in cache[key]:
            raw,adv=score_pair(rm,am,r)
            r["_raw_score"]=raw;r["_adv_score"]=adv;z.append(r)
        out[key]=z
    return out

def route_stability_prior(rst):
    sy=max(1,int(rst.get("supported_years",0)))
    pos=float(rst.get("positive_years",0))/sy
    return float(rst.get("mean_floor",-999.0))+0.75*float(rst.get("win_floor",0.0))+0.10*pos

def opportunity_ranked_cached(scored_cache,route_stability,fam_stability,adv_weight):
    by_setup={}
    for key in EVAL_KEYS:
        rst=route_stability[key];fst=fam_stability[key];prior=route_stability_prior(rst)
        for r in scored_cache[key]:
            raw=r["_raw_score"];adv=r["_adv_score"]
            if min(raw["support"],adv["support"])<20:continue
            if raw["score"]<=-900 or adv["score"]<=-900:continue
            cell=fst.get(r["family"]+"|"+r["action"])
            if cell:
                cn=int(cell["overall"]["n"]);sh=cn/(cn+80.0)
                fam_mean=sh*float(cell["mean_floor"]);fam_win=sh*float(cell["win_floor"])
            else:fam_mean=fam_win=0.0
            # Route arbitration and capital admission are different decisions.
            # Advantage mean/lcb choose among counterfactual actions; its win target is
            # ACTUAL route R>0 (never "advantage > median"). Stable route priors prevent
            # high-dimensional local noise from overwhelming cross-year evidence.
            choice_local=float(adv["lcb"])+0.85*float(adv["mean"])
            choice=0.60*prior+0.40*choice_local+0.08*fam_mean+0.04*fam_win
            actual_win=min(float(raw["win"]),float(adv["win"]))
            quality=float(raw["lcb"])+0.80*float(raw["mean"])+1.20*actual_win+0.15*max(0.0,float(adv["mean"]))
            q=dict(r);q["_raw"]=raw;q["_adv"]=adv;q["_choice_score"]=choice;q["_selection_score"]=quality
            q.pop("_raw_score",None);q.pop("_adv_score",None)
            by_setup.setdefault((r["window"],r["setup"]),[]).append(q)
    winners=[]
    for _,cand in by_setup.items():
        cand.sort(key=lambda r:(r["_choice_score"],r["_adv"]["lcb"],r["_raw"]["win"],r["sequential_key"]),reverse=True)
        if not cand:continue
        best=cand[0];second=cand[1]["_choice_score"] if len(cand)>1 else -999.0
        q=dict(best);raw=q.pop("_raw");adv=q.pop("_adv")
        q["route_utility"]=q.pop("_choice_score");q["selection_score"]=q.pop("_selection_score")
        q["route_margin"]=q["route_utility"]-second
        q["raw_pred_mean"]=raw["mean"];q["raw_pred_win"]=raw["win"];q["raw_pred_lcb"]=raw["lcb"]
        q["adv_pred_mean"]=adv["mean"];q["adv_pred_actual_win"]=adv["win"];q["adv_pred_lcb"]=adv["lcb"]
        q["route_support"]=min(raw["support"],adv["support"]);winners.append(q)
    return winners

def select_ranked(ranked,threshold):
    return [r for r in ranked if r.get("selection_score",-999.0)+1e-12>=threshold]

def optimize_training_threshold(ranked,train_windows):
    vals=[r["selection_score"] for r in ranked if math.isfinite(r.get("selection_score",-999.0))]
    if not vals:return {"q":None,"threshold":math.inf,"selected":[],"yearly":[],"objective":-999.0}
    best=None
    # Training-only scan. Test-year scores/results are never read here.
    for qi in range(0,29):
        q=qi*.025
        th=quantile(vals,q)
        sel=select_ranked(ranked,th)
        yearly=[metrics([r for r in sel if r["window"]==w]) for w in train_windows]
        if not all(m["n"]>=MIN_N for m in yearly):continue
        margins=[gate_margin(m) for m in yearly]
        obj=min(margins)+0.20*statistics.median(margins)
        tie=(obj,min(m["lcb_r"] for m in yearly),min(m["mean_r"] for m in yearly),
             min(m["win_rate"] for m in yearly),-len(sel))
        if best is None or tie>best[0]:
            best=(tie,{"q":q,"threshold":th,"selected":sel,"yearly":yearly,"objective":obj})
    return best[1] if best else {"q":None,"threshold":math.inf,"selected":[],"yearly":[],"objective":-999.0}

def assert_ranked_integrity(ranked,allowed_windows):
    seen=set()
    for r in ranked:
        ident=(r["window"],r["setup"])
        if ident in seen:raise SystemExit("V74 ranked duplicate setup identity: "+repr(ident))
        seen.add(ident)
        if r["window"] not in allowed_windows:raise SystemExit("V74 ranked window leakage: "+str(r["window"]))
        if r["sequential_key"] not in EVAL_KEYS:raise SystemExit("V74 illegal ranked route: "+str(r["sequential_key"]))
        if not math.isfinite(float(r["route_utility"])):raise SystemExit("V74 non-finite route choice utility")
        if not math.isfinite(float(r["selection_score"])):raise SystemExit("V74 non-finite setup selection score")
        if float(r["route_margin"]) < -1e-12:raise SystemExit("V74 negative route winner margin")

fold_results={name:{} for name,_,_ in VARIANTS}
fold_policies={name:{} for name,_,_ in VARIANTS}
for test in BURNED:
    fold_t0=time.perf_counter()
    train_windows=RESEARCH+[w for w in BURNED if w!=test]
    tr=[r for r in rows if r["window"] in train_windows];te=[r for r in rows if r["window"]==test]
    print(f"[V74-EVAL] fold={test} phase=route-cache train_rows={len(tr)} test_rows={len(te)}",flush=True)
    tr_cache=build_route_cache(tr);te_cache=build_route_cache(te)
    print(f"[V74-EVAL] fold={test} phase=baselines elapsed={time.perf_counter()-fold_t0:.3f}",flush=True)
    baselines=action_baselines_cached(tr_cache)
    pre_stability={key:route_year_stability_cached(tr_cache[key],train_windows) for key in EVAL_KEYS}
    def _anchor_score(key):
        z=pre_stability[key];sy=max(1,int(z.get("supported_years",0)))
        return (float(z.get("mean_floor",-999.0))+.75*float(z.get("win_floor",0.0))+
                .10*float(z.get("positive_years",0))/sy, z.get("positive_years",0), key)
    anchor_keys=sorted(EVAL_KEYS,key=_anchor_score,reverse=True)[:3]
    anchor_rows=[r for key in anchor_keys for r in tr_cache[key]]
    feature_frontier=stable_feature_frontier(anchor_rows,train_windows,24)
    if len(feature_frontier["indices"])<8:raise SystemExit("V74 stable feature frontier under-supported")
    print(f"[V74-EVAL] fold={test} phase=feature-frontier anchors={anchor_keys} indices={feature_frontier['indices']} elapsed={time.perf_counter()-fold_t0:.3f}",flush=True)
    raw_models={};adv_models={}
    for key in EVAL_KEYS:
        raw_models[key],adv_models[key]=train_raw_adv_paired_cached(tr_cache[key],key,baselines,feature_frontier)
    print(f"[V74-EVAL] fold={test} phase=paired-models elapsed={time.perf_counter()-fold_t0:.3f}",flush=True)
    route_stability=pre_stability
    fam_stability={key:family_action_route_stability_cached(tr_cache[key],train_windows) for key in EVAL_KEYS}
    models_blob["shared_folds"][test]={"training_windows":train_windows,
        "raw_route_models":raw_models,"advantage_route_models":adv_models,
        "route_stability":route_stability,"family_action_route_stability":fam_stability,
        "stable_feature_frontier":{"anchor_keys":anchor_keys,**feature_frontier}}
    tr_scored=build_scored_cache(tr_cache,raw_models,adv_models)
    te_scored=build_scored_cache(te_cache,raw_models,adv_models)
    print(f"[V74-EVAL] fold={test} phase=scored-cache elapsed={time.perf_counter()-fold_t0:.3f}",flush=True)
    rank_cache={}
    for _,_,aw in VARIANTS:
        if aw not in rank_cache:
            trr=opportunity_ranked_cached(tr_scored,route_stability,fam_stability,aw)
            ter=opportunity_ranked_cached(te_scored,route_stability,fam_stability,aw)
            assert_ranked_integrity(trr,set(train_windows));assert_ranked_integrity(ter,{test})
            rank_cache[aw]=(trr,ter)
    print(f"[V74-EVAL] fold={test} phase=rank-cache elapsed={time.perf_counter()-fold_t0:.3f}",flush=True)
    for name,q,aw in VARIANTS:
        tr_rank,te_rank=rank_cache[aw]
        opt=optimize_training_threshold(tr_rank,train_windows)
        th=opt["threshold"];train_sel=opt["selected"];yearly=opt["yearly"];chosen_q=opt["q"]
        feasible=bool(chosen_q is not None and len(train_sel)>=MIN_N*len(train_windows) and all(m["n"]>=MIN_N for m in yearly))
        sel=select_ranked(te_rank,th) if feasible else []
        m=metrics(sel);routes={};fams={}
        for r in sel:
            routes[r["sequential_key"]]=routes.get(r["sequential_key"],0)+1
            fams[r["family"]]=fams.get(r["family"],0)+1
        abcd=metrics([r for r in train_sel if r["family"]=="ABCD"])
        m.update({"pass":bool(feasible and gate_metrics(m)),"training_windows":train_windows,
                  "policy":"COUNTERFACTUAL_ROUTE_CHOICE_PLUS_ACTUAL_OUTCOME_CAPITAL_ADMISSION",
                  "selection_quantile":chosen_q,"selection_threshold":th,"advantage_weight":aw,
                  "training_threshold_objective":opt["objective"],
                  "training_feasible":feasible,"training_selected_metrics":metrics(train_sel),
                  "training_year_metrics":dict(zip(train_windows,yearly)),
                  "abcd_training_metrics_descriptive_only":abcd,
                  "canonical_family_blanket_blacklist":False,
                  "selected_route_counts":routes,"selected_family_counts":fams,
                  "median_planned_route_rr":statistics.median([r["sequential_planned_rr"] for r in sel]) if sel else 0.0})
        fold_results[name][test]=m
        fold_policies[name][test]={"policy":"COUNTERFACTUAL_ROUTE_CHOICE_PLUS_ACTUAL_OUTCOME_CAPITAL_ADMISSION",
                                   "selection_quantile":chosen_q,"selection_threshold":th,
                                   "advantage_weight":aw,"fold_ref":test,
                                   "advantage_win_target":"ACTUAL_ROUTE_R_GT_0",
                                   "canonical_family_blanket_blacklist":False}
    print(f"[V74-EVAL] fold={test} phase=complete elapsed={time.perf_counter()-fold_t0:.3f}",flush=True)

for name,q,aw in VARIANTS:
    folds=fold_results[name];policies=fold_policies[name]
    passed=all(folds[w]["pass"] for w in BURNED)
    worst=min(folds[w]["lcb_r"] for w in BURNED)
    avg_hold=statistics.mean(max(.25,folds[w]["median_hold_bars"]/60.0) for w in BURNED)
    champ_score=worst/max(.25,avg_hold)
    summary["models"][name]={"folds":folds,"pass":passed,
                             "champion_score_worst_lcb_per_slot_hour":champ_score}
    models_blob["models"][name]={"type":"CAUSAL_DUAL_HEAD_ACTION_CHOICE_AND_CAPITAL_ADMISSION","folds":policies}
    if passed:passers.append((champ_score,name))

summary["architecture"]="CAUSAL_DUAL_HEAD_ACTION_CHOICE_AND_CAPITAL_ADMISSION"
summary["policy"]["selection"]="DUAL_HEAD__TRAINING_ONLY_CROSS_YEAR_STABLE_FEATURE_FRONTIER_TOP24__ROUTE_CHOICE_USES_RELATIVE_UPLIFT_AND_STABILITY__CAPITAL_ADMISSION_USES_ACTUAL_R_AND_ACTUAL_WIN__TRAINING_ONLY_AUTO_WORST_YEAR_THRESHOLD"
summary["policy"]["route_arbitration"]="PER_SETUP_ALL_LEGAL_ROUTES__RELATIVE_UPLIFT_FOR_CHOICE_ONLY__ADVANTAGE_WIN_TARGET_IS_ACTUAL_R_GT_0__STABLE_TRAINING_PRIOR__NO_TRIGGER_OR_DECISION_FUTURE_STATE__NO_TEST_YEAR_SELECTION"
summary["policy"]["abcd_contract"]="ABCD_NEVER_BLANKET_BLACKLISTED__TRAINING_ONLY_FAMILY_ACTION_SHRINKAGE"
summary["engineering_invariants"]={"unique_setup_winner":True,"legal_route_only":True,
                                   "test_window_excluded_from_training":True,
                                   "counterfactual_baseline_training_only":True,
                                   "advantage_win_is_actual_route_win":True,
                                   "route_choice_separated_from_capital_admission":True,
                                   "training_only_auto_threshold":True,
                                   "training_only_stable_feature_frontier":True,
                                   "stable_feature_top_k":24,
                                   "canonical_family_blanket_blacklist":False,
                                   "deduplicated_model_pack":True,
                                   "fold_route_vector_cache_exact_semantics":True,
                                   "raw_adv_score_reuse_exact_semantics":True,
                                   "raw_adv_shared_feature_partition_exact_semantics":True,
                                   "single_pass_stability_grouping_exact_semantics":True,
                                   "dead_variant_eliminated":True}
summary["evaluator_runtime_seconds"]=round(time.perf_counter()-_eval_t0,6)
passers.sort(key=lambda x:(x[0],x[1]),reverse=True);alpha_champion=passers[0][1] if passers else None
# FAIL-CLOSED: the sequential OOF Alpha and the live V75/embedded execution policy are
# separate contracts. Current downstream policy code still expects legacy final/base models
# and cannot yet reproduce the selected delayed-entry route/fraction semantics exactly.
# Preserve any 3/3 OOF Alpha result as evidence, but do not promote it until runtime parity is frozen.
EXECUTION_SEMANTICS_READY=False
summary["alpha_gate"]=alpha_champion is not None
summary["alpha_champion"]=alpha_champion
summary["execution_semantics_ready"]=EXECUTION_SEMANTICS_READY
summary["v74_gate"]=bool(alpha_champion is not None and EXECUTION_SEMANTICS_READY)
summary["champion"]=alpha_champion if summary["v74_gate"] else None
summary["promotion_blocker"]="SEQUENTIAL_RUNTIME_POLICY_NOT_FROZEN" if alpha_champion else "ALPHA_OOF_GATE_FAIL"
summary["champion_selection"]="HIGHEST_WORST_YEAR_CAUSAL_LCB_PER_SLOT_HOUR_AMONG_3OF3_PASSERS"
summary["gate_semantics"]="EACH_BURNED_YEAR_N_GE_250_MEAN_R_GE_0P90_PF_R_GE_3P30_WR_GE_70PCT_AVG_RR_GE_2P30_LCB95_GT_0__TRAIN_ONLY_ROUTE_THRESHOLD__NO_LOOKAHEAD__RUNTIME_PARITY_REQUIRED_FOR_PROMOTION"
summary["positive_asset"]="CAUSAL_FAMILY_NATIVE_COUNTERFACTUAL_ACTION_RANKER_OOF_ALPHA" if alpha_champion else "NO_MODEL_EARNED_VERSION_PROMOTION"
(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2))
(out/"V74_MODELS.json").write_text(json.dumps(models_blob,separators=(",",":")))
(out/"champion.txt").write_text(summary["champion"] or "")
(out/"alpha_champion.txt").write_text(alpha_champion or "")
(out/"alpha_pass.txt").write_text("true" if alpha_champion else "false")
(out/"pass.txt").write_text("true" if summary["v74_gate"] else "false")
print(json.dumps(summary,indent=2))
