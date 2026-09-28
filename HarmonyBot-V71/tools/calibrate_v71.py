#!/usr/bin/env python3
import json,pathlib,sys,statistics
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
V=["A_V70_TRUTH_CONTROL","B_STRUCTURAL_REBASE_CONTROL","C_UNIFIED_SCORE_SINGLE","D_UNIFIED_AUCTION_SINGLE","E_UNIFIED_AUCTION_GRID","F_UNIFIED_AUCTION_GRID_RISK5"]
CAL=["Y2021","Y2022","Y2023"]
REF={
"Y2021":{"baskets":164,"net":1561.19,"pf":1.2388820883190013},
"Y2022":{"baskets":144,"net":530.86,"pf":1.0756123581182229},
"Y2023":{"baskets":58,"net":-777.03,"pf":0.713987566117117}}
def find(name):
    xs=list(root.rglob(name))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {name}: {len(xs)}")
    return xs[0]
R={(v,w):json.load(open(find(f"{v}-{w}.json"))) for v in V for w in CAL}
def pf(rows):
    gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
    return gp/gl if gl else (999 if gp else 0)
def agg(v):
    rows=[]
    for w in CAL:
        for r in R[(v,w)].get("basket_outcomes",[]):
            q=dict(r); q["window"]=w; rows.append(q)
    n=len(rows); net=sum(r["net"] for r in rows)
    return {"baskets":n,"net":net,"pf":pf(rows),"expectancy":net/n if n else 0,
      "win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,
      "frequency":n/3.0,
      "max_dd_pct":max(R[(v,w)]["max_dd_pct"] for w in CAL),
      "min_window_net":min(R[(v,w)]["net"] for w in CAL),
      "positive_windows":sum(R[(v,w)]["net"]>0 for w in CAL),
      "engineering_clean":all(R[(v,w)]["engineering_clean"] for w in CAL),
      "risk_clean":all(R[(v,w)]["actual_basket_risk_violations"]==0 and R[(v,w)]["margin_risk_violations"]==0 and R[(v,w)]["stop_widening_violations"]==0 for w in CAL),
      "identity_clean":all(R[(v,w)]["identity_clean"] and abs(R[(v,w)]["canonical_family_coverage"]-1.0)<=1e-12 for w in CAL),
      "windows":{w:{k:R[(v,w)][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct"]} for w in CAL},
      "_rows":rows}
def key(r): return (r.get("window",""),r.get("canonical_setup",""),r.get("family_id",""),r.get("route",""))
def marginal(a,b):
    x=agg(a); y=agg(b); xm={key(r):r for r in x["_rows"]}; ym={key(r):r for r in y["_rows"]}
    added=[r for k,r in ym.items() if k not in xm]; removed=[r for k,r in xm.items() if k not in ym]
    return {"from":a,"to":b,"delta_baskets":y["baskets"]-x["baskets"],"delta_net":y["net"]-x["net"],
      "delta_pf":y["pf"]-x["pf"],"delta_expectancy":y["expectancy"]-x["expectancy"],
      "positive_delta_windows":sum(R[(b,w)]["net"]>R[(a,w)]["net"] for w in CAL),
      "added_count":len(added),"added_net":sum(r["net"] for r in added),"added_pf":pf(added),
      "removed_count":len(removed),"removed_net":sum(r["net"] for r in removed),"removed_pf":pf(removed)}
def protected(rows):
    z=[]
    for r in rows:
        p=r.get("pattern"); route=r.get("route"); st=r.get("subtype") or ""
        if p=="Rat" and st=="Rat" and route=="TREND_ALIGNED_REVERSAL": z.append(r)
        elif p=="Shark" and st=="Shark" and route=="TREND_ALIGNED_REVERSAL": z.append(r)
        elif p=="Gartley" and st=="Gartley" and route=="TREND_ALIGNED_REVERSAL": z.append(r)
        elif p=="5-0" and st=="5-0" and route=="EXHAUSTION_REVERSAL": z.append(r)
        elif p=="AB=CD" and st=="ABCD_EXACT" and route=="EXHAUSTION_REVERSAL": z.append(r)
    return {"baskets":len(z),"net":sum(r["net"] for r in z),"pf":pf(z)}
def clean(z): return z["engineering_clean"] and z["risk_clean"] and z["identity_clean"]
control={}
for w,ref in REF.items():
    x=R[(V[0],w)]
    control[w]=x["baskets"]==ref["baskets"] and abs(x["net"]-ref["net"])<=.02 and abs(x["pf"]-ref["pf"])<=1e-9 and x["engineering_clean"] and x["identity_clean"]
control_gate=all(control.values())
A={v:agg(v) for v in V}
basep=protected(A[V[0]]["_rows"])
for v in V:
    p=protected(A[v]["_rows"]); A[v]["protected"]=p
    A[v]["protected_no_harm"]=p["net"]+.05>=basep["net"] and p["pf"]+.0005>=basep["pf"]
M={"B-A":marginal(V[0],V[1]),"C-B":marginal(V[1],V[2]),"D-C":marginal(V[2],V[3]),"E-D":marginal(V[3],V[4]),"F-E":marginal(V[4],V[5])}
B=clean(A[V[1]])
def beats_floor(z):
    return clean(z) and z["positive_windows"]==3 and z["net"]>2101.66 and z["pf"]>2.1096878432 and z["expectancy"]>36.2355 and z["win_rate"]>=.534483 and z["frequency"]>=60 and z["max_dd_pct"]<=4.49784
C=control_gate and beats_floor(A[V[2]]) and M["C-B"]["delta_net"]>0 and M["C-B"]["delta_pf"]>0 and M["C-B"]["delta_expectancy"]>0 and M["C-B"]["positive_delta_windows"]>=2
D=control_gate and beats_floor(A[V[3]]) and M["D-C"]["delta_net"]>0 and M["D-C"]["delta_pf"]>=0 and M["D-C"]["delta_expectancy"]>=0 and M["D-C"]["positive_delta_windows"]>=2
E=control_gate and beats_floor(A[V[4]]) and M["E-D"]["delta_net"]>0 and M["E-D"]["delta_pf"]>=0 and M["E-D"]["delta_expectancy"]>=0 and M["E-D"]["positive_delta_windows"]>=2 and sum(int(R[(V[4],w)].get("grid_amplified_plans",0)) for w in CAL)>0
F=clean(A[V[5]]) and A[V[5]]["max_dd_pct"]<=10
candidate=V[4] if E else V[3] if D else V[2] if C else None
for v in V: A[v].pop("_rows",None)
freeze={"version":"HarmonyBot V71","stage":"CALIBRATION_ONLY_SELECTION","calibration_windows":CAL,
 "control_reproduction_gate":control_gate,"control_reproduction":control,"variants":A,"marginal":M,
 "gates":{"B_structural_rebase_control_clean":B,"C_unified_score_single":C,"D_unified_auction_single":D,"E_unified_auction_grid":E,"F_unified_risk5_research_only":F},
 "candidate":candidate,"candidate_selection_source":"BURNED_2021_2023_ONLY","risk_attribution_rule":"C_D_E_PROMOTION_ALWAYS_1PCT_F_IS_RESEARCH_ONLY_5PCT_CAPACITY",
 "dev_seen_previously":True,"dev_used_for_threshold_selection":False,
 "validation_used":False,"fresh_used":False,
 "decision":"CALIBRATION_CANDIDATE_FROZEN" if candidate else "CALIBRATION_HOLD"}
(out/"V71_CALIBRATION_FREEZE.json").write_text(json.dumps(freeze,indent=2))
(out/"candidate.txt").write_text(candidate or "")
(out/"dev_matrix.json").write_text(json.dumps([V[0],candidate] if candidate else [V[0]],separators=(",",":")))
print(json.dumps(freeze,indent=2))
