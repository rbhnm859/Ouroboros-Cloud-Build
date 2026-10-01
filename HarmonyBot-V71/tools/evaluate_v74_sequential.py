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
from v74_model_lib import load_rows,metrics,SEQUENTIAL_KEYS

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
    if len(state)!=12 or len(entry_state)!=12:return None
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
    s=r.get("sequential_state_vector");e=r.get("sequential_entry_state_vector")
    if s is None or e is None or len(s)!=12 or len(e)!=12:return None
    f=r.get("features",[])
    pre=[f[j] if j<len(f) else 0.0 for j in (25,26,29,34,35,36,37,38,39)]
    return list(s)+list(e)+pre

def stat(xs):
    if not xs:return {"n":0,"mean":0.0,"win":0.0,"sigma":10.0}
    v=[float(r["r"]) for r in xs];n=len(v);sd=statistics.stdev(v) if n>1 else 10.0
    return {"n":n,"mean":sum(v)/n,"win":sum(x>0 for x in v)/n,"sigma":max(.05,sd)}

def train_labeled(q,key):
    pairs=[(r,hvec(r)) for r in q];pairs=[z for z in pairs if z[1] is not None]
    q=[z[0] for z in pairs];vec=[z[1] for z in pairs]
    if not q:return {"key":key,"medians":[],"global":stat([]),"family_action":{},"bins":[]}
    p=len(vec[0]);med=[statistics.median(v[j] for v in vec) for j in range(p)]
    glob=stat(q);fa={}
    for fam in sorted({r["family"] for r in q}):
        for action in ("REVERSAL","CONTINUATION"):
            z=[r for r in q if r["family"]==fam and r["action"]==action]
            if z:fa[fam+"|"+action]=stat(z)
    bins=[]
    for j in range(p):
        lo=[r for r,v in zip(q,vec) if v[j]<med[j]]
        hi=[r for r,v in zip(q,vec) if v[j]>=med[j]]
        bins.append({"lo":stat(lo),"hi":stat(hi)})
    return {"key":key,"medians":med,"global":glob,"family_action":fa,"bins":bins}

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
    return train_labeled(q,key)

def score(model,r):
    v=hvec(r);g=model.get("global",{})
    if v is None or not model.get("medians") or int(g.get("n",0))<80:
        return {"score":-999.0,"mean":0.0,"win":0.0,"lcb":-999.0,"support":0}
    gm=float(g.get("mean",0.0));gw=float(g.get("win",0.0));gs=float(g.get("sigma",10.0))
    fa=model.get("family_action",{}).get(r["family"]+"|"+r["action"],{"n":0,"mean":gm,"win":gw})
    fn=int(fa.get("n",0));fw=fn/(fn+80.0)
    pm=gm+fw*(float(fa.get("mean",gm))-gm);pw=gw+fw*(float(fa.get("win",gw))-gw)
    ms=[];ws=[];supp=[]
    for j,x in enumerate(v):
        b=model["bins"][j]["hi" if x>=model["medians"][j] else "lo"];n=int(b.get("n",0));sh=n/(n+60.0)
        ms.append(pm+sh*(float(b.get("mean",gm))-gm));ws.append(pw+sh*(float(b.get("win",gw))-gw));supp.append(n)
    mean=(pm+sum(ms)/len(ms))/2.0;win=max(0.0,min(1.0,(pw+sum(ws)/len(ws))/2.0))
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
 ("CA_UPLIFT60_KEEP100",0.00,0.60),
 ("CB_UPLIFT60_KEEP97",0.03,0.60),
 ("CC_UPLIFT60_KEEP95",0.05,0.60),
 ("CD_UPLIFT75_KEEP100",0.00,0.75),
 ("CE_UPLIFT75_KEEP97",0.03,0.75),
 ("CF_UPLIFT75_KEEP95",0.05,0.75)
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

fold_results={name:{} for name,_,_ in VARIANTS}
fold_policies={name:{} for name,_,_ in VARIANTS}
for test in BURNED:
    train_windows=RESEARCH+[w for w in BURNED if w!=test]
    tr=[r for r in rows if r["window"] in train_windows];te=[r for r in rows if r["window"]==test]
    baselines=action_baselines(tr)
    raw_models={key:train(tr,key) for key in EVAL_KEYS}
    adv_models={key:train_advantage(tr,key,baselines) for key in EVAL_KEYS}
    route_stability={key:route_year_stability(tr,key,train_windows) for key in EVAL_KEYS}
    fam_stability={key:family_action_route_stability(tr,key,train_windows) for key in EVAL_KEYS}
    models_blob["shared_folds"][test]={"training_windows":train_windows,
        "raw_route_models":raw_models,"advantage_route_models":adv_models,
        "route_stability":route_stability,"family_action_route_stability":fam_stability}
    rank_cache={}
    for _,_,aw in VARIANTS:
        if aw not in rank_cache:
            trr=opportunity_ranked(tr,raw_models,adv_models,route_stability,fam_stability,aw)
            ter=opportunity_ranked(te,raw_models,adv_models,route_stability,fam_stability,aw)
            assert_ranked_integrity(trr,set(train_windows));assert_ranked_integrity(ter,{test})
            rank_cache[aw]=(trr,ter)
    for name,q,aw in VARIANTS:
        tr_rank,te_rank=rank_cache[aw]
        vals=[r["route_utility"] for r in tr_rank if math.isfinite(r["route_utility"])]
        th=quantile(vals,q) if vals else math.inf
        train_sel=select_ranked(tr_rank,th)
        yearly=[metrics([r for r in train_sel if r["window"]==w]) for w in train_windows]
        feasible=bool(len(train_sel)>=MIN_N*len(train_windows) and all(m["n"]>=MIN_N for m in yearly))
        sel=select_ranked(te_rank,th) if feasible else []
        m=metrics(sel);routes={};fams={}
        for r in sel:
            routes[r["sequential_key"]]=routes.get(r["sequential_key"],0)+1
            fams[r["family"]]=fams.get(r["family"],0)+1
        abcd=metrics([r for r in train_sel if r["family"]=="ABCD"])
        m.update({"pass":bool(feasible and gate_metrics(m)),"training_windows":train_windows,
                  "policy":"FAMILY_NATIVE_COUNTERFACTUAL_PER_OPPORTUNITY_ROUTE_WINNER",
                  "selection_quantile":q,"selection_threshold":th,"advantage_weight":aw,
                  "training_feasible":feasible,"training_selected_metrics":metrics(train_sel),
                  "training_year_metrics":dict(zip(train_windows,yearly)),
                  "abcd_training_metrics_descriptive_only":abcd,
                  "canonical_family_blanket_blacklist":False,
                  "selected_route_counts":routes,"selected_family_counts":fams,
                  "median_planned_route_rr":statistics.median([r["sequential_planned_rr"] for r in sel]) if sel else 0.0})
        fold_results[name][test]=m
        fold_policies[name][test]={"policy":"FAMILY_NATIVE_COUNTERFACTUAL_PER_OPPORTUNITY_ROUTE_WINNER",
                                   "selection_quantile":q,"selection_threshold":th,
                                   "advantage_weight":aw,"fold_ref":test,
                                   "canonical_family_blanket_blacklist":False}

for name,q,aw in VARIANTS:
    folds=fold_results[name];policies=fold_policies[name]
    passed=all(folds[w]["pass"] for w in BURNED)
    worst=min(folds[w]["lcb_r"] for w in BURNED)
    avg_hold=statistics.mean(max(.25,folds[w]["median_hold_bars"]/60.0) for w in BURNED)
    champ_score=worst/max(.25,avg_hold)
    summary["models"][name]={"folds":folds,"pass":passed,
                             "champion_score_worst_lcb_per_slot_hour":champ_score}
    models_blob["models"][name]={"type":"CAUSAL_FAMILY_NATIVE_COUNTERFACTUAL_ACTION_RANKER","folds":policies}
    if passed:passers.append((champ_score,name))

summary["architecture"]="CAUSAL_FAMILY_NATIVE_COUNTERFACTUAL_ACTION_RANKER"
summary["policy"]["selection"]="TRAINING_ONLY_COUNTERFACTUAL_UPLIFT_PLUS_ABSOLUTE_ROUTE_VALUE__FAMILY_NATIVE_SHRINKAGE__NO_CANONICAL_FAMILY_BLACKLIST"
summary["policy"]["route_arbitration"]="PER_SETUP_ALL_LEGAL_ROUTES__CENTERED_ACTION_ADVANTAGE_AND_ABSOLUTE_VALUE__NO_TEST_YEAR_SELECTION"
summary["policy"]["abcd_contract"]="ABCD_NEVER_BLANKET_BLACKLISTED__TRAINING_ONLY_FAMILY_ACTION_SHRINKAGE"
summary["engineering_invariants"]={"unique_setup_winner":True,"legal_route_only":True,
                                   "test_window_excluded_from_training":True,
                                   "counterfactual_baseline_training_only":True,
                                   "canonical_family_blanket_blacklist":False,
                                   "deduplicated_model_pack":True}
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
