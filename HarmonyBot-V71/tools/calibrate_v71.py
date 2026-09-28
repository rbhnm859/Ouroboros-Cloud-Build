#!/usr/bin/env python3
import json,pathlib,sys,statistics
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
V=["A_V70_TRUTH_CONTROL","B_SELECTIVE_BACKFILL_ALPHA","C_BACKFILL_REGIME_GRID","D_ADAPTIVE_RISK_5PCT"]
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
        f=r.get("family_id"); route=r.get("route"); st=r.get("subtype") or ""
        if f=="Rat" and route in ("TREND_ALIGNED_REVERSAL","EXHAUSTION_REVERSAL"): z.append(r)
        elif f=="Shark" and route=="TREND_ALIGNED_REVERSAL": z.append(r)
        elif f=="Shark" and route=="EXHAUSTION_REVERSAL" and st=="Shark": z.append(r)
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
M={"B-A":marginal(V[0],V[1]),"C-B":marginal(V[1],V[2]),"D-C":marginal(V[2],V[3])}
B=control_gate and clean(A[V[1]]) and A[V[1]]["net"]>A[V[0]]["net"] and A[V[1]]["pf"]>A[V[0]]["pf"] and A[V[1]]["expectancy"]>A[V[0]]["expectancy"] and A[V[1]]["frequency"]>=60 and A[V[1]]["max_dd_pct"]<=10 and M["B-A"]["delta_net"]>0 and M["B-A"]["delta_pf"]>0 and M["B-A"]["delta_expectancy"]>0 and M["B-A"]["positive_delta_windows"]>=2 and A[V[1]]["protected_no_harm"]
C=B and clean(A[V[2]]) and A[V[2]]["frequency"]>=A[V[1]]["frequency"]*.90 and A[V[2]]["max_dd_pct"]<=10 and M["C-B"]["delta_net"]>0 and M["C-B"]["delta_pf"]>=0 and M["C-B"]["delta_expectancy"]>=0 and M["C-B"]["positive_delta_windows"]>=2 and A[V[2]]["protected_no_harm"]
D=C and clean(A[V[3]]) and A[V[3]]["net"]>A[V[2]]["net"] and A[V[3]]["expectancy"]>A[V[2]]["expectancy"] and A[V[3]]["pf"]>=A[V[2]]["pf"]-.02 and A[V[3]]["win_rate"]>=A[V[2]]["win_rate"]-.01 and A[V[3]]["frequency"]>=A[V[2]]["frequency"]*.95 and A[V[3]]["max_dd_pct"]<=10 and A[V[3]]["protected_no_harm"]
candidate=V[3] if D else V[2] if C else V[1] if B else None
for v in V: A[v].pop("_rows",None)
freeze={"version":"HarmonyBot V71","stage":"CALIBRATION_ONLY_SELECTION","calibration_windows":CAL,
 "control_reproduction_gate":control_gate,"control_reproduction":control,"variants":A,"marginal":M,
 "gates":{"B_selective_backfill_alpha":B,"C_backfill_regime_grid":C,"D_adaptive_risk_5pct":D},
 "candidate":candidate,"candidate_selection_source":"BURNED_2021_2023_ONLY","risk_attribution_rule":"B/C_ALPHA_AT_1PCT_THEN_D_RISK_OVERLAY_UP_TO_5PCT",
 "dev_seen_previously":True,"dev_used_for_threshold_selection":False,
 "validation_used":False,"fresh_used":False,
 "decision":"CALIBRATION_CANDIDATE_FROZEN" if candidate else "CALIBRATION_HOLD"}
(out/"V71_CALIBRATION_FREEZE.json").write_text(json.dumps(freeze,indent=2))
(out/"candidate.txt").write_text(candidate or "")
(out/"dev_matrix.json").write_text(json.dumps([V[0],candidate] if candidate else [V[0]],separators=(",",":")))
print(json.dumps(freeze,indent=2))
