#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["V46_SCALE_CONTROL","NATIVE_CONFIRMATION_ONLY","NATIVE_CONFIRMATION_QUEUE","FULL_V49_COMMERCIAL"]
BASE={"baskets":39,"frequency":26.0,"net":1721.72,"pf":2.1833,"expectancy":44.15,"win_rate":.5128,"max_dd_pct":4.56}
V36={"baskets":77,"frequency":51.3333333333,"net":648.58,"pf":1.2124297856,"expectancy":8.4231,"win_rate":.42857,"max_dd_pct":8.7683}
COMM={"baskets":90,"frequency":60,"net":1800,"pf":2.0,"expectancy":20,"win_rate":.50,"max_dd_pct":6.0}
def find(n): return next(root.rglob(n))
def rd(f,w): return json.load(open(find(f"{f}-{w}.json")))
def pf(v):
 gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0)); return gp/gl if gl else (999 if gp else 0)
def agg(f):
 xs=[rd(f,w) for w in "ABC"]; rows=[r for x in xs for r in x.get("basket_outcomes",[])]
 v=[r["net"] for r in rows]; setups={r["setup"] for r in rows}; n=len(rows)
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len(setups),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/n if n else 0,
 "win_rate":sum(x>0 for x in v)/n if n else 0,"max_dd_pct":max(x["max_dd_pct"] for x in xs),
 "all_windows_positive":all(x["net"]>0 for x in xs),"engineering_clean":all(x["engineering_clean"] for x in xs),
 "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
 "windows":{w:rd(f,w) for w in "ABC"},"rows":rows}
A={f:agg(f) for f in F}; c=A["V46_SCALE_CONTROL"]
c["baseline_reproduction_pass"]=c["baskets"]==39 and abs(c["net"]-BASE["net"])<=.10 and abs(c["pf"]-BASE["pf"])<=.002
base_sets={w:{r["setup"] for r in rd("V46_SCALE_CONTROL",w).get("basket_outcomes",[])} for w in "ABC"}
for f in F[1:]:
 by={}; rr=[]
 for w in "ABC":
  q=[r for r in rd(f,w).get("basket_outcomes",[]) if r["setup"] not in base_sets[w]]; rr+=q; v=[r["net"] for r in q]
  by[w]={"trades":len(q),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v) if v else 0}
 v=[r["net"] for r in rr]
 A[f]["marginal"]={"trades":len(rr),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v) if v else 0,"windows":by}
 A[f]["marginal"]["pass"]=len(rr)>0 and sum(v)>0 and pf(v)>=1.20 and all(by[w]["net"]>=0 for w in "ABC")
for f in F:
 z=A[f]; z["v36_dominance"]=z["baskets"]>77 and z["frequency"]>V36["frequency"] and z["net"]>V36["net"] and z["pf"]>V36["pf"] and z["expectancy"]>V36["expectancy"] and z["win_rate"]>V36["win_rate"] and z["max_dd_pct"]<V36["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"]
 z["commercial_gate"]=f!="V46_SCALE_CONTROL" and z["baskets"]>=90 and z["frequency"]>=60 and z["net"]>=1800 and z["pf"]>=2 and z["expectancy"]>=20 and z["win_rate"]>=.50 and z["max_dd_pct"]<=6 and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z.get("marginal",{}).get("pass",False)
 rows=z.pop("rows")
 # family effectiveness: which patterns actually convert to executions and economics
 g={}
 for r in rows:
  p=r.get("pattern","?"); q=g.setdefault(p,[]); q.append(r["net"])
 z["pattern_economics"]={p:{"trades":len(v),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v),"win_rate":sum(x>0 for x in v)/len(v)} for p,v in g.items()}
eligible=[f for f in F if A[f]["commercial_gate"]]
winner=max(eligible,key=lambda f:(A[f]["net"],A[f]["pf"],A[f]["frequency"])) if eligible else None
front={"version":"HarmonyBot V49","architecture":"PATTERN_NATIVE_CONFIRMATION_ARBITRATION","baseline":BASE,"v36":V36,"commercial_minimum":COMM,"baseline_reproduction_pass":c["baseline_reproduction_pass"],"families":A,"development_candidate":winner,"status":"COMMERCIAL_FREEZE_CANDIDATE_DEV_PASS" if winner else "HOLD_WITH_EVIDENCE","fresh_used":False}
(out/"V49_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2)); (out/"candidate.txt").write_text(winner or "")
(out/"V49_PATTERN_CONFIRMATION_EFFECTIVENESS.json").write_text(json.dumps({f:A[f]["pattern_economics"] for f in F},indent=2))
(out/"V49_FINAL_COMMERCIAL_DECISION.json").write_text(json.dumps({"decision":"COMMERCIAL_FREEZE_CANDIDATE_PASS" if winner else "HOLD_WITH_EVIDENCE","stage":"DEV","fresh_used":False},indent=2))
print(json.dumps(front,indent=2))
