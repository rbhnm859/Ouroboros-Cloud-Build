#!/usr/bin/env python3
import json,pathlib,sys,statistics,collections,datetime
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
DEV=["H2024H2","H2025H1","H2025H2"]; DUR={"H2024H2":.5,"H2025H1":.5,"H2025H2":.5}; START=10000.0
REF={
"H2024H2":{"baskets":65,"net":355.52,"pf":1.1473694682562052},
"H2025H1":{"baskets":70,"net":-121.39,"pf":0.9519022751226315},
"H2025H2":{"baskets":15,"net":-884.85,"pf":0.32696695874406717}}
def find(name):
    xs=list(root.rglob(name))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {name}: {len(xs)}")
    return xs[0]
freeze=json.load(open(find("V71_CALIBRATION_FREEZE.json")))
candidate=freeze.get("candidate")
if not candidate:
    decision={"version":"HarmonyBot V71","decision":"HOLD_WITH_EVIDENCE","candidate":None,
      "stage":"CALIBRATION_HOLD","validation_used":False,"fresh_used":False}
    (out/"V71_FINAL_DEV_DECISION.json").write_text(json.dumps(decision,indent=2))
    (out/"V71_PERFORMANCE_FRONTIER.json").write_text(json.dumps({"calibration":freeze,"dev":None,**decision},indent=2))
    (out/"candidate.txt").write_text("")
    print(json.dumps(decision,indent=2)); raise SystemExit(0)
V=["A_V70_TRUTH_CONTROL",candidate]
R={(v,w):json.load(open(find(f"{v}-{w}.json"))) for v in V for w in DEV}
def pf(rows):
    gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
    return gp/gl if gl else (999 if gp else 0)
def rr(rows):
    w=[r.get("r") for r in rows if isinstance(r.get("r"),(int,float)) and r.get("r")>0]
    l=[r.get("r") for r in rows if isinstance(r.get("r"),(int,float)) and r.get("r")<0]
    cov=(len(w)+len(l))/len(rows) if rows else 0
    return ((statistics.mean(w)/abs(statistics.mean(l))) if w and l else 0),cov
def month(rows):
    m=collections.defaultdict(float)
    for r in rows:
        v=r.get("entry_time")
        if not isinstance(v,(int,float)) or v<=0: continue
        sec=v/1000 if v>1e11 else v
        try: k=datetime.datetime.utcfromtimestamp(sec).strftime("%Y-%m")
        except: continue
        m[k]+=r["net"]
    ks=sorted(m); z=ks[-12:]
    return len(ks),sum(m[k]>0 for k in z),dict(sorted(m.items()))
def agg(v):
    rows=[]
    for w in DEV:
        for r in R[(v,w)].get("basket_outcomes",[]):
            q=dict(r); q["window"]=w; rows.append(q)
    years=sum(DUR.values()); n=len(rows); net=sum(r["net"] for r in rows); rrv,cov=rr(rows); mo,pm,monthly=month(rows)
    return {"baskets":n,"years":years,"frequency":n/years,"net":net,"pf":pf(rows),"expectancy":net/n if n else 0,
      "win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,"max_dd_pct":max(R[(v,w)]["max_dd_pct"] for w in DEV),
      "positive_windows":sum(R[(v,w)]["net"]>0 for w in DEV),
      "engineering_clean":all(R[(v,w)]["engineering_clean"] for w in DEV),
      "risk_clean":all(R[(v,w)]["actual_basket_risk_violations"]==0 and R[(v,w)]["margin_risk_violations"]==0 and R[(v,w)]["stop_widening_violations"]==0 for w in DEV),
      "identity_clean":all(R[(v,w)]["identity_clean"] and abs(R[(v,w)]["canonical_family_coverage"]-1)<=1e-12 for w in DEV),
      "realized_rr":rrv,"realized_rr_coverage":cov,"months_observed":mo,"profitable_months_observed":pm,
      "simple_annualized_return_pct":net/START/years*100,
      "windows":{w:{k:R[(v,w)][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct"]} for w in DEV},
      "_rows":rows,"monthly_net":monthly}
def protected(rows):
    z=[]
    for r in rows:
        f=r.get("family_id"); route=r.get("route"); st=r.get("subtype") or ""
        if f=="Rat" and route in ("TREND_ALIGNED_REVERSAL","EXHAUSTION_REVERSAL"): z.append(r)
        elif f=="Shark" and route=="TREND_ALIGNED_REVERSAL": z.append(r)
        elif f=="Shark" and route=="EXHAUSTION_REVERSAL" and st=="Shark": z.append(r)
    return {"baskets":len(z),"net":sum(r["net"] for r in z),"pf":pf(z)}
def key(r): return (r.get("window",""),r.get("canonical_setup",""),r.get("family_id",""),r.get("route",""))
def clean(z): return z["engineering_clean"] and z["risk_clean"] and z["identity_clean"]
A=agg(V[0]); C=agg(candidate); am={key(r):r for r in A["_rows"]}; cm={key(r):r for r in C["_rows"]}
added=[r for k,r in cm.items() if k not in am]; removed=[r for k,r in am.items() if k not in cm]
marg={"delta_baskets":C["baskets"]-A["baskets"],"delta_net":C["net"]-A["net"],"delta_pf":C["pf"]-A["pf"],
 "delta_expectancy":C["expectancy"]-A["expectancy"],"positive_delta_windows":sum(R[(candidate,w)]["net"]>R[(V[0],w)]["net"] for w in DEV),
 "added_count":len(added),"added_net":sum(r["net"] for r in added),"added_pf":pf(added),
 "removed_count":len(removed),"removed_net":sum(r["net"] for r in removed),"removed_pf":pf(removed)}
ctrl={w:(R[(V[0],w)]["baskets"]==REF[w]["baskets"] and abs(R[(V[0],w)]["net"]-REF[w]["net"])<=.02 and abs(R[(V[0],w)]["pf"]-REF[w]["pf"])<=1e-9) for w in DEV}
bp=protected(A["_rows"]); cp=protected(C["_rows"]); protected_no_harm=cp["net"]+.05>=bp["net"] and cp["pf"]+.0005>=bp["pf"]
gate=all(ctrl.values()) and clean(C) and marg["delta_net"]>0 and marg["delta_pf"]>0 and marg["delta_expectancy"]>0 and marg["positive_delta_windows"]>=2 and C["positive_windows"]==3 and C["frequency"]>38.6667 and C["net"]>2101.66 and C["pf"]>2.1096878432 and C["expectancy"]>36.2355 and C["win_rate"]>=.534483 and C["max_dd_pct"]<=4.49784 and protected_no_harm
decision="BREAKTHROUGH_PASS" if gate else "HOLD_WITH_EVIDENCE"
for z in (A,C): z.pop("_rows",None)
front={"version":"HarmonyBot V71","stage":"CALIBRATION_FROZEN_OBSERVED_DEV_STRESS",
 "calibration":freeze,"candidate":candidate,"control_dev":A,"candidate_dev":C,"marginal_vs_control":marg,
 "control_reproduction":ctrl,"protected_control":bp,"protected_candidate":cp,"protected_no_harm":protected_no_harm,
 "breakthrough_gate":gate,"decision":decision,"validation_used":False,"fresh_used":False,
 "governance":{"dev_reuse_iteration":6,"dev_role":"OBSERVED_STRESS_CONFIRMATION_NOT_PRISTINE_OOS",
   "candidate_selected_before_this_dev_run":True,"candidate_selection_source":"BURNED_2021_2023_ONLY",
   "validation_locked":True,"fresh_locked":True,"no_minor_version_promotion":True},
 "risk_policy":{"default_pct":1.0,"hard_ceiling_pct":5.0,"adaptive_not_fixed":True,"alpha_risk_attribution_separated":True},"v51_promotion_floor":{"frequency":38.6667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784},"final_v80_targets":{"return_pct":100,"pf":2.5,"max_dd_pct":10,"win_rate":.65,"frequency":200,"realized_rr":2.0,"profitable_months_12":10,"net_pct_initial":100}}
(out/"V71_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V71_FINAL_DEV_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V71","decision":decision,"candidate":candidate,"validation_used":False,"fresh_used":False},indent=2))
(out/"candidate.txt").write_text(candidate if gate else "")
print(json.dumps(front,indent=2))
