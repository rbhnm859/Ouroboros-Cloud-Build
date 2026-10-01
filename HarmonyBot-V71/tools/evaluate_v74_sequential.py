#!/usr/bin/env python3
"""V74 two-stage shadow->capital causal sequential evaluator."""
import json,math,pathlib,statistics,sys
from v74_model_lib import load_rows,metrics,SEQUENTIAL_KEYS
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
RESEARCH=[f"Y{y}" for y in range(2016,2021)];BURNED=["Y2021","Y2022","Y2023"];ALL=RESEARCH+BURNED
MIN_N=250;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_RR=2.30;Z=1.645
ABCD_TRAIN_MIN_N=300;ABCD_TRAIN_MIN_PF=1.20
rows=load_rows(root,ALL)
if not rows:raise SystemExit("no V74 tournament rows")
def quantile(vals,q):
    if not vals:return math.inf
    x=sorted(vals);p=(len(x)-1)*q;a=int(math.floor(p));b=int(math.ceil(p))
    return x[a] if a==b else x[a]*(b-p)+x[b]*(p-a)
def gate(m):return m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0
def with_outcome(r,key):
    v=r.get("sequential",{}).get(key);rr=r.get("sequential_rr",{}).get(key)
    s=r.get("sequential_state",{}).get("025");t=r.get("sequential_trigger_state",{}).get(key);e=r.get("sequential_entry_state",{}).get(key)
    if v is None or rr is None or s is None or t is None or e is None:return None
    if len(s)!=12 or len(t)!=12 or len(e)!=12:return None
    try:v=float(v);rr=float(rr)
    except:return None
    if not math.isfinite(v) or not math.isfinite(rr) or rr+1e-9<MIN_RR:return None
    q=dict(r);q["native_r"]=r["r"];q["r"]=v;q["sequential_key"]=key;q["sequential_planned_rr"]=rr
    q["sequential_state_vector"]=list(s);q["sequential_trigger_state_vector"]=list(t);q["sequential_entry_state_vector"]=list(e)
    return q
def seq_rows(xs,key):
    z=[]
    for r in xs:
        q=with_outcome(r,key)
        if q is not None:z.append(q)
    return z
def hvec(r):
    s=r["sequential_state_vector"];t=r["sequential_trigger_state_vector"];e=r["sequential_entry_state_vector"];f=r.get("features",[])
    pre=[f[j] if j<len(f) else 0.0 for j in (25,26,29,34,35,36,37,38,39)]
    return list(s)+list(t)+list(e)+pre
def stat(xs):
    if not xs:return {"n":0,"mean":0.0,"win":0.0,"sigma":10.0}
    v=[float(r["r"]) for r in xs];n=len(v);sd=statistics.stdev(v) if n>1 else 10.0
    return {"n":n,"mean":sum(v)/n,"win":sum(x>0 for x in v)/n,"sigma":max(.05,sd)}
def train(xs,key):
    q=seq_rows(xs,key);vec=[hvec(r) for r in q]
    if not q:return {"key":key,"medians":[],"global":stat([]),"family_action":{},"bins":[]}
    p=len(vec[0]);med=[statistics.median(v[j] for v in vec) for j in range(p)];g=stat(q);fa={}
    for fam in sorted({r["family"] for r in q}):
        for act in ("REVERSAL","CONTINUATION"):
            z=[r for r in q if r["family"]==fam and r["action"]==act]
            if z:fa[fam+"|"+act]=stat(z)
    bins=[]
    for j in range(p):
        lo=[r for r,v in zip(q,vec) if v[j]<med[j]];hi=[r for r,v in zip(q,vec) if v[j]>=med[j]]
        bins.append({"lo":stat(lo),"hi":stat(hi)})
    return {"key":key,"medians":med,"global":g,"family_action":fa,"bins":bins}
def score(m,r):
    v=hvec(r);g=m.get("global",{})
    if not m.get("medians") or int(g.get("n",0))<80:return {"score":-999.0,"mean":0,"win":0,"lcb":-999,"support":0}
    gm=g["mean"];gw=g["win"];gs=g["sigma"];fa=m["family_action"].get(r["family"]+"|"+r["action"],{"n":0,"mean":gm,"win":gw})
    fn=fa["n"];fw=fn/(fn+80.0);pm=gm+fw*(fa["mean"]-gm);pw=gw+fw*(fa["win"]-gw);ms=[];ws=[];supp=[]
    for j,x in enumerate(v):
        b=m["bins"][j]["hi" if x>=m["medians"][j] else "lo"];n=b["n"];sh=n/(n+60.0)
        ms.append(pm+sh*(b["mean"]-gm));ws.append(pw+sh*(b["win"]-gw));supp.append(n)
    mean=(pm+sum(ms)/len(ms))/2;win=max(0,min(1,(pw+sum(ws)/len(ws))/2));support=max(1,min([fn if fn else g["n"]]+supp));lcb=mean-Z*gs/math.sqrt(support)
    return {"score":lcb+.75*win,"mean":mean,"win":win,"lcb":lcb,"support":support}
def scored(xs,key,m):
    z=[]
    for r in seq_rows(xs,key):
        q=dict(r);q["_hz"]=score(m,r);z.append(q)
    return z
def apply(sr,th,abcd=True):
    z=[]
    for r in sr:
        if r["family"]=="ABCD" and not abcd:continue
        h=r["_hz"]
        if h["score"]+1e-12<th:continue
        q=dict(r);q.pop("_hz",None);q["seq_pred_mean"]=h["mean"];q["seq_pred_win"]=h["win"];q["seq_pred_lcb"]=h["lcb"];q["seq_support"]=h["support"];q["seq_score"]=h["score"];z.append(q)
    return z
def margin(m):
    if not m["n"]:return -999
    return min(m["n"]/MIN_N,m["mean_r"]/MIN_MEAN,m["pf_r"]/MIN_PF,m["win_rate"]/MIN_WR,m["average_rr"]/MIN_RR,1+m["lcb_r"]/.25)
def choose(tr,windows,q):
    cand=[]
    for key in SEQUENTIAL_KEYS:
        model=train(tr,key);sr=scored(tr,key,model);vals=[r["_hz"]["score"] for r in sr if r["_hz"]["score"]>-900]
        if not vals:continue
        th=quantile(vals,q);sel=apply(sr,th,True);agg=metrics(sel);ym=[]
        for w in windows:
            x=metrics([r for r in sel if r["window"]==w])
            if x["n"]>=160:ym.append(x)
        if agg["n"]<850 or len(ym)<len(windows):continue
        mar=[margin(x) for x in ym];robust=min(mar)+.25*statistics.median(mar)
        cand.append((robust,min(x["lcb_r"] for x in ym),min(x["mean_r"] for x in ym),min(x["win_rate"] for x in ym),min(x["average_rr"] for x in ym),agg["n"],key,model,th,agg))
    cand.sort(key=lambda x:(x[0],x[1],x[2],x[3],x[4],x[5],x[6]),reverse=True)
    return cand[0] if cand else None
summary={"version":"HarmonyBot V74 Candidate","architecture":"TWO_STAGE_SHADOW_TO_CAPITAL_CAUSAL_SEQUENCE",
 "legacy_negative_evidence":[{"run":55,"result":"A-L_FAIL"},{"run":60,"result":"1P25_1P50_N_CEILING"},{"run":63,"result":"EARLY_FRONTIER_JOINT_FAIL"},{"run":64,"result":"BARBELL_IMPROVED_PAYOFF_BUT_2023_CONVERSION_FAIL"}],
 "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
 "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,"min_win_rate":MIN_WR,"min_average_rr":MIN_RR,"lcb95_gt":0.0},
 "policy":{"stage_a":"ORIGINAL_0P25R_FIRST_PASSAGE_ZERO_CAPITAL","stage_b":"LATER_COMPLETED_M1_SHADOW_MICRO_ROUTE_ZERO_CAPITAL",
 "stage_c":"SHADOW_FIRST_PASSAGE_0P05_0P10_0P15_ZERO_CAPITAL","stage_d":"STILL_LATER_COMPLETED_M1_PERSISTENCE_ACTUAL_CAPITAL",
 "stage_e":"FULL_CANONICAL_RUNNER_WITH_OPTIONAL_0P25R_TO_0P05R_POSITIVE_FLOOR","same_bar":"CONSERVATIVE","no_stop_widening":True,
 "partial_exit":False,"grid":False,"minimum_route_net_rr":MIN_RR,"selection":"TRAINING_ONLY"},
 "models":{},"validation_used":False,"fresh_used":False}
mb={"architecture":"V74_TWO_STAGE_SHADOW_CAUSAL_HAZARD","models":{}};passers=[]
for name,q in [("V_SHADOW_KEEP100",0.0),("W_SHADOW_KEEP95",.05),("X_SHADOW_KEEP90",.10)]:
    folds={};pol={}
    for test in BURNED:
        windows=RESEARCH+[w for w in BURNED if w!=test];tr=[r for r in rows if r["window"] in windows];te=[r for r in rows if r["window"]==test]
        ch=choose(tr,windows,q)
        if ch is None:
            m=metrics([]);m.update({"pass":False,"training_windows":windows,"route":None,"selection_quantile":q});folds[test]=m;pol[test]={"route":None};continue
        robust,wl,wm,ww,wr,_,key,model,th,_=ch;trs=scored(tr,key,model);train_sel=apply(trs,th,True)
        abcd=metrics([r for r in train_sel if r["family"]=="ABCD"]);abcd_ok=abcd["n"]>=ABCD_TRAIN_MIN_N and abcd["mean_r"]>0 and abcd["pf_r"]>=ABCD_TRAIN_MIN_PF and abcd["lcb_r"]>0
        tes=scored(te,key,model);sel=apply(tes,th,abcd_ok);m=metrics(sel)
        m.update({"pass":gate(m),"training_windows":windows,"route":key,"selection_quantile":q,"selection_threshold":th,
         "training_selected_metrics":metrics(train_sel),"training_robust_gate_margin":robust,"training_worst_year_lcb":wl,
         "training_worst_year_mean":wm,"training_worst_year_win_rate":ww,"training_worst_year_average_rr":wr,
         "abcd_training_metrics":abcd,"abcd_training_capital_eligible":bool(abcd_ok),
         "median_planned_route_rr":statistics.median([r["sequential_planned_rr"] for r in sel]) if sel else 0.0})
        folds[test]=m;pol[test]={"route":key,"selection_quantile":q,"selection_threshold":th,"hazard_model":model,"abcd_capital_eligible":bool(abcd_ok)}
    passed=all(folds[w]["pass"] for w in BURNED);worst=min(folds[w]["lcb_r"] for w in BURNED);avg_hold=statistics.mean(max(.25,folds[w]["median_hold_bars"]/60) for w in BURNED);cs=worst/max(.25,avg_hold)
    summary["models"][name]={"folds":folds,"pass":passed,"champion_score_worst_lcb_per_slot_hour":cs};mb["models"][name]={"type":"TWO_STAGE_SHADOW_CAUSAL_HAZARD","folds":pol}
    if passed:passers.append((cs,name))
passers.sort(reverse=True);champ=passers[0][1] if passers else None
summary["v74_gate"]=champ is not None;summary["champion"]=champ;summary["champion_selection"]="HIGHEST_WORST_YEAR_LCB_PER_SLOT_HOUR_AMONG_3OF3_PASSERS"
summary["gate_semantics"]="UNCHANGED_N250_MEAN0P90_PF3P30_WR70_RR2P30_LCBPOS_TRAIN_ONLY_NO_LOOKAHEAD";summary["positive_asset"]="TWO_STAGE_SHADOW_OOF_CHAMPION" if champ else "NO_MODEL_EARNED_VERSION_PROMOTION"
(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2));(out/"V74_MODELS.json").write_text(json.dumps(mb,separators=(",",":")));(out/"champion.txt").write_text(champ or "");(out/"pass.txt").write_text("true" if champ else "false");print(json.dumps(summary,indent=2))
