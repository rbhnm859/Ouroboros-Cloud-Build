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
import json,math,pathlib,statistics,sys
from v74_model_lib import load_rows,metrics,SEQUENTIAL_KEYS

root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
RESEARCH=[f"Y{y}" for y in range(2016,2021)]
BURNED=["Y2021","Y2022","Y2023"];ALL=RESEARCH+BURNED
MIN_N=250;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_RR=2.30
ABCD_TRAIN_MIN_N=300;ABCD_TRAIN_MIN_PF=1.20;Z=1.645
rows=load_rows(root,ALL)
if not rows:raise SystemExit("no V74 tournament rows")

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
    v=r.get("sequential",{}).get(key);rr=r.get("sequential_rr",{}).get(key)
    level,entry_key=route_meta(key)
    state=r.get("sequential_state",{}).get(level)
    entry_state=r.get("sequential_entry_state",{}).get(entry_key)
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

def train(xs,key):
    q=seq_rows(xs,key);pairs=[(r,hvec(r)) for r in q];pairs=[z for z in pairs if z[1] is not None]
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
    for key in SEQUENTIAL_KEYS:
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
 "architecture":"CAUSAL_MICRO_POSITIVE_ARM_BARBELL",
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
  {"source_run_id":36912836008,"run":72,"result":"ACTION_ENVELOPE_FEASIBLE_BUT_ENTRY_STATE_ARBITRATION_OOF_FAIL"}],
 "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
 "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,
         "min_win_rate":MIN_WR,"min_average_rr":MIN_RR,"lcb95_gt":0.0},
 "policy":{
   "capital":"LATER_COMPLETED_M1_HOLD_AFTER_ORIGINAL_0P25_OR_0P50_FIRST_PASSAGE",
   "entry_risk_geometry":"CANONICAL_TARGET_BACKSOLVES_INITIAL_STOP_AT_2P4R_2P6R_2P8R_BOUNDED_BY_STRUCTURAL_INVALIDATION",
   "post_entry_barbell":"COMPLETED_BAR_0P25_0P50_0P75_1P00_FIRST_PASSAGE_PLUS_LATER_PERSISTENCE_ARMS_MONOTONE_SOFT_FRONTIER__EXIT_ONLY_ON_LATER_COMPLETED_M1_CLOSE__CANONICAL_TARGET_REMAINS_INTRABAR",
   "candidates":SEQUENTIAL_KEYS,"adverse_cut":"COMPLETED_CLOSE_ONLY_BEFORE_POSITIVE_ARM",
   "same_bar":"STRUCTURAL_STOP_THEN_TARGET_THEN_CLOSE_ONLY_FRONTIER_THEN_ADVERSE_CLOSE_THEN_NEW_ARM",
   "no_stop_widening":True,"partial_exit":False,"grid":False,"minimum_route_net_rr":MIN_RR,
   "selection":"TRAINING_ONLY_HIERARCHICAL_PARTIAL_POOLING_PLUS_ROBUST_GATE_MARGIN"},
 "models":{},"validation_used":False,"fresh_used":False}
models_blob={"architecture":"V74_CAUSAL_MICRO_POSITIVE_ARM_BARBELL","models":{}}
passers=[]

for name,q in [("AQ_MICRO_KEEP100",0.0),("AR_MICRO_KEEP90",.10),("AS_MICRO_KEEP80",.20)]:
    folds={};policies={}
    for test in BURNED:
        train_windows=RESEARCH+[w for w in BURNED if w!=test]
        tr=[r for r in rows if r["window"] in train_windows];te=[r for r in rows if r["window"]==test]
        ch=choose(tr,train_windows,q)
        if ch is None:
            m=metrics([]);m.update({"pass":False,"training_windows":train_windows,"route":None,"selection_quantile":q})
            folds[test]=m;policies[test]={"route":None,"selection_quantile":q};continue
        robust,wl,wm,ww,wr,_,key,model,th,_=ch
        tr_sc=scored_rows(tr,key,model);train_sel=apply(tr_sc,th,True)
        abcd=metrics([r for r in train_sel if r["family"]=="ABCD"])
        abcd_ok=bool(abcd["n"]>=ABCD_TRAIN_MIN_N and abcd["mean_r"]>0 and abcd["pf_r"]>=ABCD_TRAIN_MIN_PF and abcd["lcb_r"]>0)
        te_sc=scored_rows(te,key,model);sel=apply(te_sc,th,abcd_ok);m=metrics(sel)
        m.update({"pass":gate_metrics(m),"training_windows":train_windows,"route":key,
                  "selection_quantile":q,"selection_threshold":th,
                  "training_selected_metrics":metrics(train_sel),"training_robust_gate_margin":robust,
                  "training_worst_year_lcb":wl,"training_worst_year_mean":wm,
                  "training_worst_year_win_rate":ww,"training_worst_year_average_rr":wr,
                  "abcd_training_metrics":abcd,"abcd_training_capital_eligible":abcd_ok,
                  "median_planned_route_rr":statistics.median([r["sequential_planned_rr"] for r in sel]) if sel else 0.0})
        folds[test]=m
        policies[test]={"route":key,"selection_quantile":q,"selection_threshold":th,
                        "hazard_model":model,"abcd_capital_eligible":abcd_ok}
    passed=all(folds[w]["pass"] for w in BURNED)
    worst=min(folds[w]["lcb_r"] for w in BURNED)
    avg_hold=statistics.mean(max(.25,folds[w]["median_hold_bars"]/60.0) for w in BURNED)
    champ_score=worst/max(.25,avg_hold)
    summary["models"][name]={"folds":folds,"pass":passed,
                             "champion_score_worst_lcb_per_slot_hour":champ_score}
    models_blob["models"][name]={"type":"CAUSAL_MICRO_POSITIVE_ARM_BARBELL","folds":policies}
    if passed:passers.append((champ_score,name))

passers.sort(key=lambda x:(x[0],x[1]),reverse=True);champion=passers[0][1] if passers else None
summary["v74_gate"]=champion is not None;summary["champion"]=champion
summary["champion_selection"]="HIGHEST_WORST_YEAR_CAUSAL_LCB_PER_SLOT_HOUR_AMONG_3OF3_PASSERS"
summary["gate_semantics"]="EACH_BURNED_YEAR_N_GE_250_MEAN_R_GE_0P90_PF_R_GE_3P30_WR_GE_70PCT_AVG_RR_GE_2P30_LCB95_GT_0__TRAIN_ONLY_ROUTE_THRESHOLD__NO_LOOKAHEAD"
summary["positive_asset"]="CAUSAL_MICRO_POSITIVE_ARM_OOF_CHAMPION" if champion else "NO_MODEL_EARNED_VERSION_PROMOTION"
(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2))
(out/"V74_MODELS.json").write_text(json.dumps(models_blob,separators=(",",":")))
(out/"champion.txt").write_text(champion or "")
(out/"pass.txt").write_text("true" if champion else "false")
print(json.dumps(summary,indent=2))
