#!/usr/bin/env python3
"""
V74 causal sequential reconstruction evaluator.

Run #55 froze A-L as terminal negative evidence. This evaluator intentionally does
not recompute those exhausted architectures. It evaluates only the current causal
first-passage reaction->reversal reconstruction, with every route/threshold chosen
from training windows only. Validation/Fresh are never loaded here.
"""
import json,math,pathlib,statistics,sys
from v74_model_lib import load_rows,metrics,SEQUENTIAL_KEYS

root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
RESEARCH=[f"Y{y}" for y in range(2016,2021)]
BURNED=["Y2021","Y2022","Y2023"]
ALL=RESEARCH+BURNED
MIN_N=250;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_RR=2.30
ABCD_TRAIN_MIN_N=300;ABCD_TRAIN_MIN_PF=1.20
Z=1.645
rows=load_rows(root,ALL)
if not rows: raise SystemExit("no V74 tournament rows")

def quantile(vals,q):
    if not vals:return math.inf
    xs=sorted(float(x) for x in vals);p=(len(xs)-1)*q
    lo=int(math.floor(p));hi=int(math.ceil(p))
    return xs[lo] if lo==hi else xs[lo]*(hi-p)+xs[hi]*(p-lo)

def gate_metrics(m):
    return bool(m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and
                m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0)

def with_outcome(r,key):
    v=r.get("sequential",{}).get(key);rr=r.get("sequential_rr",{}).get(key)
    level="125" if "S125_" in key else "150"
    state=r.get("sequential_state",{}).get(level)
    if v is None or rr is None or state is None or len(state)!=12:return None
    try:v=float(v);rr=float(rr)
    except Exception:return None
    if not math.isfinite(v) or not math.isfinite(rr) or rr+1e-9<MIN_RR:return None
    q=dict(r);q["native_r"]=r["r"];q["r"]=v;q["sequential_key"]=key
    q["sequential_planned_rr"]=rr;q["sequential_level"]=level;q["sequential_state_vector"]=list(state)
    return q

def seq_rows(xs,key):
    out=[]
    for r in xs:
        q=with_outcome(r,key)
        if q is not None:out.append(q)
    return out

def hvec(r):
    s=r.get("sequential_state_vector")
    if s is None or len(s)!=12:return None
    f=r.get("features",[])
    pre=[f[j] if j<len(f) else 0.0 for j in (25,26,29,34,35,36,37,38,39)]
    return list(s)+pre

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
        lo=[r for r,v in zip(q,vec) if v[j]<med[j]];hi=[r for r,v in zip(q,vec) if v[j]>=med[j]]
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
    out=[]
    for r in seq_rows(xs,key):
        z=score(model,r);q=dict(r);q["_hz"]=z;out.append(q)
    return out

def apply(scored,threshold,abcd_allowed=True):
    out=[]
    for r in scored:
        if r["family"]=="ABCD" and not abcd_allowed:continue
        z=r["_hz"]
        if z["score"]+1e-12<threshold:continue
        q=dict(r);q.pop("_hz",None);q["seq_pred_mean"]=z["mean"];q["seq_pred_win"]=z["win"]
        q["seq_pred_lcb"]=z["lcb"];q["seq_support"]=z["support"];q["seq_score"]=z["score"];out.append(q)
    return out

def choose(train_rows,train_windows,q):
    candidates=[]
    for key in SEQUENTIAL_KEYS:
        model=train(train_rows,key);sr=scored_rows(train_rows,key,model)
        vals=[r["_hz"]["score"] for r in sr if math.isfinite(r["_hz"]["score"]) and r["_hz"]["score"]>-900]
        if not vals:continue
        th=quantile(vals,q);sel=apply(sr,th,True);agg=metrics(sel);yearly=[]
        for w in train_windows:
            ym=metrics([r for r in sel if r["window"]==w])
            if ym["n"]>=120:yearly.append(ym)
        if agg["n"]<700 or len(yearly)<4:continue
        wl=min(z["lcb_r"] for z in yearly);wm=min(z["mean_r"] for z in yearly)
        ww=min(z["win_rate"] for z in yearly);wr=min(z["average_rr"] for z in yearly)
        utility=wl+.20*wm+.35*ww+.08*min(5.0,wr)
        candidates.append((utility,wl,wm,ww,wr,agg["n"],key,model,th,agg))
    candidates.sort(key=lambda z:(z[0],z[1],z[2],z[3],z[4],z[5],z[6]),reverse=True)
    return candidates[0] if candidates else None

summary={
 "version":"HarmonyBot V74 Candidate",
 "architecture":"CAUSAL_FIRST_PASSAGE_REACTION_TO_REVERSAL_RECONSTRUCTION",
 "legacy_negative_evidence":{"frozen":True,"source_run_id":36863429034,"source_run_number":55,
   "reason":"A-L static/protection/re-entry/hybrid/reaction-commit/high-conviction architectures already failed 3/3 OOF; do not recompute completed history."},
 "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
 "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,
         "min_win_rate":MIN_WR,"min_average_rr":MIN_RR,"lcb95_gt":0.0},
 "causal_sequential_policy":{"routes":SEQUENTIAL_KEYS,"observation":"SHADOW_FIRST_PASSAGE_1P25R_OR_1P50R",
   "capital_entry":"LATER_COMPLETED_M1_REACTION_HOLD_ONLY","minimum_route_net_rr":MIN_RR,
   "hazard_state":"FIRST_PASSAGE_TIME_MFE_MAE_BODY_WICKS_RETRACE_REMAINING_R_DIRECTION_EFFICIENCY_PLUS_PREENTRY_REGIME",
   "selection":"TRAINING_ONLY","test_year_never_selects_route_or_threshold":True,
   "same_bar_ambiguity":"ALREADY_ARMED_FLOOR_THEN_STOP_THEN_TARGET","no_stop_widening":True},
 "models":{},"validation_used":False,"fresh_used":False}
models_blob={"architecture":"V74_CAUSAL_FIRST_PASSAGE_SEQUENTIAL_HAZARD","models":{}}
passers=[]

for name,q in [("M_CAUSAL_SEQ_HAZARD_KEEP90",.10),("N_CAUSAL_SEQ_HAZARD_KEEP85",.15),("O_CAUSAL_SEQ_HAZARD_KEEP80",.20)]:
    folds={};policies={}
    for test in BURNED:
        train_windows=RESEARCH+[w for w in BURNED if w!=test]
        tr=[r for r in rows if r["window"] in train_windows];te=[r for r in rows if r["window"]==test]
        ch=choose(tr,train_windows,q)
        if ch is None:
            m=metrics([]);m.update({"pass":False,"training_windows":train_windows,"route":None,"selection_quantile":q,"selection_threshold":None})
            folds[test]=m;policies[test]={"route":None,"selection_quantile":q};continue
        utility,wl,wm,ww,wr,_,key,model,th,_=ch
        tr_sc=scored_rows(tr,key,model);train_sel=apply(tr_sc,th,True)
        abcd=metrics([r for r in train_sel if r["family"]=="ABCD"])
        abcd_ok=bool(abcd["n"]>=ABCD_TRAIN_MIN_N and abcd["mean_r"]>0 and abcd["pf_r"]>=ABCD_TRAIN_MIN_PF and abcd["lcb_r"]>0)
        te_sc=scored_rows(te,key,model);sel=apply(te_sc,th,abcd_ok);m=metrics(sel)
        m.update({"pass":gate_metrics(m),"training_windows":train_windows,"route":key,"selection_quantile":q,
                  "selection_threshold":th,"training_selected_metrics":metrics(train_sel),
                  "training_worst_year_lcb":wl,"training_worst_year_mean":wm,"training_worst_year_win_rate":ww,
                  "training_worst_year_average_rr":wr,"training_route_utility":utility,
                  "abcd_training_metrics":abcd,"abcd_training_capital_eligible":abcd_ok,
                  "median_planned_route_rr":statistics.median([r["sequential_planned_rr"] for r in sel]) if sel else 0.0})
        folds[test]=m;policies[test]={"route":key,"selection_quantile":q,"selection_threshold":th,
                                     "hazard_model":model,"abcd_capital_eligible":abcd_ok}
    passed=all(folds[w]["pass"] for w in BURNED)
    worst=min(folds[w]["lcb_r"] for w in BURNED);avg_hold=statistics.mean(max(.25,folds[w]["median_hold_bars"]/60.0) for w in BURNED)
    champ_score=worst/max(.25,avg_hold)
    summary["models"][name]={"folds":folds,"pass":passed,"champion_score_worst_lcb_per_slot_hour":champ_score}
    models_blob["models"][name]={"type":"CAUSAL_FIRST_PASSAGE_SEQUENTIAL_HAZARD","folds":policies}
    if passed:passers.append((champ_score,name))

passers.sort(key=lambda x:(x[0],x[1]),reverse=True);champion=passers[0][1] if passers else None
summary["v74_gate"]=champion is not None;summary["champion"]=champion
summary["champion_selection"]="HIGHEST_WORST_YEAR_CAUSAL_LCB_PER_EXPECTED_SLOT_HOUR_AMONG_3OF3_PASSERS"
summary["gate_semantics"]="EACH_BURNED_YEAR_N_GE_250_MEAN_R_GE_0P90_PF_R_GE_3P30_WR_GE_70PCT_AVG_RR_GE_2P30_LCB95_GT_0__ALL_ROUTE_AND_HAZARD_THRESHOLDS_TRAIN_ONLY__NO_LOOKAHEAD"
summary["positive_asset"]="CAUSAL_SEQUENTIAL_OOF_CHAMPION" if champion else "NO_MODEL_EARNED_VERSION_PROMOTION"

(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2))
(out/"V74_MODELS.json").write_text(json.dumps(models_blob,separators=(",",":")))
(out/"champion.txt").write_text(champion or "")
(out/"pass.txt").write_text("true" if champion else "false")
print(json.dumps(summary,indent=2))
