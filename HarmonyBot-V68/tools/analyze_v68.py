#!/usr/bin/env python3
import json,pathlib,sys,math,statistics
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
V=["A_SUPPLY_CONTROL","B_TRUTH_ONLY","C_EVIDENCE_PRESERVING","D_GRID_CHALLENGER"]
W=["Y2021","Y2022","Y2023","H2024H2","H2025H1","H2025H2"]; DUR={"Y2021":1.0,"Y2022":1.0,"Y2023":1.0,"H2024H2":.5,"H2025H1":.5,"H2025H2":.5}; YEARS=sum(DUR.values())
def find(name):
    xs=list(root.rglob(name))
    if not xs:raise SystemExit("missing "+name)
    return xs[0]
def rd(v,w):return json.load(open(find(f"{v}-{w}.json")))
def pf(rows):
    gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
    return gp/gl if gl else (999 if gp else 0)
def finite(x):return isinstance(x,(int,float)) and math.isfinite(x)
def pctl(xs,p):
    z=sorted(x for x in xs if finite(x))
    return z[max(0,min(len(z)-1,math.ceil(p*len(z))-1))] if z else None
def sig(r):return (r.get("direction",""),int(r.get("entry_time") or 0),int(r.get("close_time") or 0),round(float(r.get("net",0)),2),int(r.get("fragments",0)))
def agg(v):
    wins={w:rd(v,w) for w in W}; rows=[]
    for w in W:
        for r in wins[w].get("basket_outcomes",[]):
            q=dict(r); q["window"]=w; rows.append(q)
    n=len(rows); net=sum(r["net"] for r in rows); rr=[r["r"] for r in rows if finite(r.get("r"))]; wr=[x for x in rr if x>0]
    return {"baskets":n,"years":YEARS,"frequency":n/YEARS,"net":net,"normalized_net_1p5y":net/YEARS*1.5,"pf":pf(rows),
      "expectancy":net/n if n else 0,"win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,
      "max_dd_pct":max((wins[w]["max_dd_pct"] for w in W),default=0),"p95_winner_r":pctl(wr,.95),"max_winner_r":max(wr) if wr else None,
      "all_windows_positive":all(wins[w]["net"]>0 for w in W),"engineering_clean":all(wins[w]["engineering_clean"] for w in W),
      "identity_clean":all(wins[w]["identity_clean"] for w in W if wins[w].get("canonical_identity")),
      "risk_clean":all(wins[w]["actual_basket_risk_violations"]==0 and wins[w]["margin_risk_violations"]==0 and wins[w]["stop_widening_violations"]==0 for w in W),
      "unique_thesis":len({(r["window"],r["canonical_setup"]) for r in rows})==n,
      "canonical_family_coverage":sum(r.get("family_id") not in (None,"","Unknown") for r in rows)/n if n else 0,
      "windows":{w:{k:wins[w][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct","engineering_clean","identity_clean","canonical_family_coverage"]} for w in W},
      "_rows":rows,"_wins":wins}
A={v:agg(v) for v in V}
truth_detail={}; truth_ok=True
for w in W:
    a=rd(V[0],w); b=rd(V[1],w)
    checks={"baskets":a["baskets"]==b["baskets"],"fragments":a["report_history_fragments"]==b["report_history_fragments"],
      "net":abs(a["net"]-b["net"])<=.05,"pf":abs(a["pf"]-b["pf"])<=.0005,"expectancy":abs(a["expectancy"]-b["expectancy"])<=.01,
      "win_rate":abs(a["win_rate"]-b["win_rate"])<=.0001,"max_dd":abs(a["max_dd_pct"]-b["max_dd_pct"])<=.0005,
      "sequence":[sig(x) for x in a["basket_outcomes"]]==[sig(x) for x in b["basket_outcomes"]],
      "b_identity_clean":b["identity_clean"],"b_canonical_coverage":abs(b["canonical_family_coverage"]-1.0)<=1e-12,
      "engineering":a["engineering_clean"] and b["engineering_clean"]}
    ok=all(checks.values()); truth_ok &= ok; truth_detail[w]={"pass":ok,"checks":checks}
def marginal(frm,to):
    x={(r["window"],r["canonical_setup"]):r for r in A[frm]["_rows"]}; y={(r["window"],r["canonical_setup"]):r for r in A[to]["_rows"]}
    added=[r for k,r in y.items() if k not in x]; removed=[r for k,r in x.items() if k not in y]
    common=[(x[k],y[k]) for k in x.keys()&y.keys()]
    return {"from":frm,"to":to,"delta_trades":A[to]["baskets"]-A[frm]["baskets"],"delta_net":A[to]["net"]-A[frm]["net"],
      "delta_pf":A[to]["pf"]-A[frm]["pf"],"delta_expectancy":A[to]["expectancy"]-A[frm]["expectancy"],
      "added_count":len(added),"added_net":sum(r["net"] for r in added),"removed_count":len(removed),"removed_net":sum(r["net"] for r in removed),
      "matched_net_delta":sum(b["net"]-a["net"] for a,b in common)}
M={"C-B":marginal(V[1],V[2]),"D-C":marginal(V[2],V[3])}
COMM={"frequency":60.0,"normalized_net_1p5y":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
V51={"frequency":38.6666666667,"normalized_net_1p5y":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
def commercial(z):return z["frequency"]>=60 and z["normalized_net_1p5y"]>=1800 and z["pf"]>=2 and z["expectancy"]>=20 and z["win_rate"]>=.50 and z["max_dd_pct"]<=6 and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_thesis"] and z["identity_clean"]
def superior(z):return z["frequency"]>V51["frequency"] and z["normalized_net_1p5y"]>V51["normalized_net_1p5y"] and z["pf"]>V51["pf"] and z["expectancy"]>V51["expectancy"] and z["win_rate"]>=V51["win_rate"] and z["max_dd_pct"]<=V51["max_dd_pct"]
c_preserve=(M["C-B"]["removed_count"]==0 and abs(M["C-B"]["delta_net"])<=.05 and A[V[2]]["canonical_family_coverage"]==1.0 and A[V[2]]["identity_clean"])
d_grid=(M["D-C"]["delta_net"]>0 and A[V[3]]["pf"]>=A[V[2]]["pf"] and A[V[3]]["expectancy"]>=A[V[2]]["expectancy"] and A[V[3]]["risk_clean"] and A[V[3]]["identity_clean"] and (A[V[3]]["max_winner_r"] or 0)>=(A[V[2]]["max_winner_r"] or 0))
for v in V:A[v]["commercial_gate"]=commercial(A[v]); A[v]["v51_superiority_gate"]=superior(A[v])
attrib=[]
for v in V:
  for r in A[v]["_rows"]:
    attrib.append({"variant":v,"window":r["window"],"canonical_family_id":r.get("family_id","Unknown"),"pattern_display":r.get("pattern",""),"route":r.get("route",""),
      "setup":r.get("canonical_setup",""),"net":r["net"],"r":r.get("r"),"mfe":r.get("mfe"),"mae":r.get("mae")})
candidate=None
if truth_ok and c_preserve and A[V[2]]["commercial_gate"] and A[V[2]]["v51_superiority_gate"]:candidate=V[2]
if truth_ok and c_preserve and d_grid and A[V[3]]["commercial_gate"] and A[V[3]]["v51_superiority_gate"]:candidate=V[3]
for v in V:A[v].pop("_rows",None);A[v].pop("_wins",None)
front={"version":"HarmonyBot V68","stage":"DEV","duration_years":YEARS,"truth_equivalence_gate":truth_ok,"truth_detail":truth_detail,
 "commercial_minimum":COMM,"v51_superiority":V51,"variants":A,"marginal":M,"evidence_preserving_gate":c_preserve,"grid_promotion_gate":d_grid,
 "development_candidate":candidate,"decision":"DEV_CANDIDATE_PASS" if candidate else "HOLD_WITH_EVIDENCE","fresh_used":False}
(out/"V68_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V68_CANONICAL_FAMILY_ROUTE_ATTRIBUTION.json").write_text(json.dumps(attrib,indent=2))
(out/"V68_TRUTH_EQUIVALENCE.json").write_text(json.dumps({"pass":truth_ok,"windows":truth_detail},indent=2))
(out/"candidate.txt").write_text(candidate or "")
(out/"V68_FINAL_DEV_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V68","decision":front["decision"],"candidate":candidate,"fresh_used":False},indent=2))
print(json.dumps(front,indent=2))
