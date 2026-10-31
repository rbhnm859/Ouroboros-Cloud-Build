#!/usr/bin/env python3
import json,pathlib,sys,collections,re
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["V46_SCALE_CONTROL","FAMILY_COMPLETION_ONLY","GRID_SEMANTIC_V2","FULL_V50_COMMERCIAL"]
BASE={"baskets":39,"frequency":26.0,"net":1721.72,"pf":2.1833,"expectancy":44.15,"win_rate":.5128,"max_dd_pct":4.56}
V36={"baskets":77,"frequency":51.3333333333,"net":648.58,"pf":1.2124297856,"expectancy":8.4231,"win_rate":.42857,"max_dd_pct":8.7683}
COMM={"baskets":90,"frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
def find(n):
 xs=list(root.rglob(n))
 if not xs: raise SystemExit("missing "+n)
 return xs[0]
def rd(f,w): return json.load(open(find(f"{f}-{w}.json")))
def pf(v):
 gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))
 return gp/gl if gl else (999 if gp else 0)
def agg(f):
 xs=[rd(f,w) for w in "ABC"]; rows=[r for x in xs for r in x.get("basket_outcomes",[])]
 v=[r["net"] for r in rows]; setups={r["setup"] for r in rows}; n=len(rows)
 pipes={}
 for x in xs:
  for p,row in x.get("pattern_pipeline",{}).items():
   q=pipes.setdefault(p,{k:0 for k in row})
   for k,z in row.items(): q[k]+=z
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len(setups),"net":sum(v),"pf":pf(v),
  "expectancy":sum(v)/n if n else 0,"win_rate":sum(x>0 for x in v)/n if n else 0,
  "max_dd_pct":max(x["max_dd_pct"] for x in xs),"all_windows_positive":all(x["net"]>0 for x in xs),
  "engineering_clean":all(x["engineering_clean"] for x in xs),
  "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
  "windows":{w:rd(f,w) for w in "ABC"},"rows":rows,"pipeline":pipes}
A={f:agg(f) for f in F}; c=A["V46_SCALE_CONTROL"]
c["baseline_reproduction_pass"]=c["baskets"]==39 and abs(c["net"]-BASE["net"])<=.10 and abs(c["pf"]-BASE["pf"])<=.002

base_sets={w:{r["setup"] for r in rd("V46_SCALE_CONTROL",w).get("basket_outcomes",[])} for w in "ABC"}
for f in F[1:]:
 by={}; rr=[]
 for w in "ABC":
  q=[r for r in rd(f,w).get("basket_outcomes",[]) if r["setup"] not in base_sets[w]]; rr+=q
  v=[r["net"] for r in q]; by[w]={"trades":len(q),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v) if v else 0}
 v=[r["net"] for r in rr]
 A[f]["marginal"]={"trades":len(rr),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v) if v else 0,"windows":by}
 A[f]["marginal"]["pass"]=len(rr)>0 and sum(v)>0 and (sum(v)/len(v) if v else 0)>0 and pf(v)>=1.20 and all(by[w]["net"]>=0 for w in "ABC")

gridrej={f:collections.Counter() for f in F}
familytel={f:collections.defaultdict(lambda:{"pass":0,"windowReject":0}) for f in F}
for f in F:
 for w in "ABC":
  for lp in root.rglob(f"V50-{f}-{w}-B10000.log"):
   txt=lp.read_text(errors="ignore")
   for m in re.finditer(r"\[V50-GRID-REJECT-SUMMARY\]\s+reason=(\S+)\s+count=(\d+)",txt):
    gridrej[f][m.group(1)]+=int(m.group(2))
   for m in re.finditer(r"\[V50-FAMILY-CONTRACT-SUMMARY\]\s+pattern=(.*?)\s+pass=(\d+)\s+windowReject=(\d+)",txt):
    familytel[f][m.group(1)]["pass"]+=int(m.group(2)); familytel[f][m.group(1)]["windowReject"]+=int(m.group(3))

for f in F:
 z=A[f]; rows=z["rows"]; g=collections.defaultdict(list)
 for r in rows: g[r.get("pattern","?")].append(r["net"])
 z["pattern_economics"]={p:{"trades":len(v),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v),"win_rate":sum(x>0 for x in v)/len(v)} for p,v in g.items()}
 z["grid_reject_reasons"]=dict(gridrej[f]); z["family_contract_telemetry"]={p:dict(v) for p,v in familytel[f].items()}
 z["v36_dominance"]=z["baskets"]>77 and z["frequency"]>V36["frequency"] and z["net"]>V36["net"] and z["pf"]>V36["pf"] and z["expectancy"]>V36["expectancy"] and z["win_rate"]>V36["win_rate"] and z["max_dd_pct"]<V36["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"]
 z["commercial_gate"]=f!="V46_SCALE_CONTROL" and z["baskets"]>=COMM["baskets"] and z["frequency"]>=COMM["frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"] and z.get("marginal",{}).get("pass",False)
 z.pop("rows",None)

eligible=[f for f in F if A[f]["commercial_gate"]]
winner=max(eligible,key=lambda f:(A[f]["net"],A[f]["pf"],A[f]["frequency"])) if eligible else None
front={"version":"HarmonyBot V50","architecture":"PATTERN_NATIVE_STRUCTURAL_GRID_CONTRACT","baseline":BASE,"v36":V36,"commercial_minimum":COMM,
 "baseline_reproduction_pass":c["baseline_reproduction_pass"],"families":A,"development_candidate":winner,
 "status":"COMMERCIAL_FREEZE_CANDIDATE_DEV_PASS" if winner else "HOLD_WITH_EVIDENCE","fresh_used":False,
 "next_stage":"CAPITAL_COMPATIBILITY" if winner else "STOP_DEV_HOLD"}
(out/"V50_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V50_GRID_REJECTION_ATTRIBUTION.json").write_text(json.dumps({f:dict(gridrej[f]) for f in F},indent=2))
(out/"V50_PATTERN_FAMILY_EFFECTIVENESS.json").write_text(json.dumps({f:{"pattern_economics":A[f]["pattern_economics"],"pipeline":A[f]["pipeline"],"family_contract_telemetry":A[f]["family_contract_telemetry"]} for f in F},indent=2))
(out/"V50_ROOT_CAUSE_REPORT.json").write_text(json.dumps({"baseline_reproduced":c["baseline_reproduction_pass"],"completion_only":A["FAMILY_COMPLETION_ONLY"],"grid_semantic_v2":A["GRID_SEMANTIC_V2"],"full_structural_grid":A["FULL_V50_COMMERCIAL"]},indent=2))
(out/"candidate.txt").write_text(winner or "")
(out/"V50_FINAL_COMMERCIAL_DECISION.json").write_text(json.dumps({"decision":"COMMERCIAL_FREEZE_CANDIDATE_DEV_PASS" if winner else "HOLD_WITH_EVIDENCE","stage":"DEV","fresh_used":False},indent=2))
print(json.dumps(front,indent=2))
