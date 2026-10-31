#!/usr/bin/env python3
import json,pathlib,sys,collections
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["V46_SCALE_CONTROL","V51_MATH_CONTROL","FAMILY_IDENTITY_RECONSTRUCTION","FULL_V52_COMMERCIAL"]
V46={"baskets":39,"frequency":26.0,"net":1721.72,"pf":2.1833,"expectancy":44.15,"win_rate":.5128,"max_dd_pct":4.56}
V51={"baskets":58,"frequency":38.6666666667,"net":2101.66,"pf":2.1097,"expectancy":36.24,"win_rate":.5345,"max_dd_pct":4.50}
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
 truth=collections.defaultdict(lambda:collections.Counter()); pipes={}
 for x in xs:
  for p,stages in x.get("detector_truth",{}).items(): truth[p].update(stages)
  for p,row in x.get("pattern_pipeline",{}).items():
   q=pipes.setdefault(p,{k:0 for k in row})
   for k,z in row.items(): q[k]+=z
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len(setups),"net":sum(v),"pf":pf(v),
 "expectancy":sum(v)/n if n else 0,"win_rate":sum(x>0 for x in v)/n if n else 0,
 "max_dd_pct":max(x["max_dd_pct"] for x in xs),"all_windows_positive":all(x["net"]>0 for x in xs),
 "engineering_clean":all(x["engineering_clean"] for x in xs),
 "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
 "windows":{w:rd(f,w) for w in "ABC"},"rows":rows,"pipeline":pipes,
 "detector_truth":{p:dict(c) for p,c in truth.items()}}
A={f:agg(f) for f in F}
def repro(z,b):
 return z["baskets"]==b["baskets"] and abs(z["net"]-b["net"])<=.20 and abs(z["pf"]-b["pf"])<=.004 and abs(z["max_dd_pct"]-b["max_dd_pct"])<=.10
A["V46_SCALE_CONTROL"]["control_reproduction_pass"]=repro(A["V46_SCALE_CONTROL"],V46)
A["V51_MATH_CONTROL"]["control_reproduction_pass"]=repro(A["V51_MATH_CONTROL"],V51)
controls_ok=A["V46_SCALE_CONTROL"]["control_reproduction_pass"] and A["V51_MATH_CONTROL"]["control_reproduction_pass"]
base_sets={w:{r["setup"] for r in rd("V46_SCALE_CONTROL",w).get("basket_outcomes",[])} for w in "ABC"}
for f in F[1:]:
 by={}; rr=[]
 for w in "ABC":
  q=[r for r in rd(f,w).get("basket_outcomes",[]) if r["setup"] not in base_sets[w]]; rr+=q
  v=[r["net"] for r in q]; by[w]={"trades":len(q),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v) if v else 0}
 v=[r["net"] for r in rr]
 A[f]["marginal"]={"trades":len(rr),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v) if v else 0,"windows":by}
 A[f]["marginal"]["pass"]=len(rr)>0 and sum(v)>0 and (sum(v)/len(v) if v else 0)>0 and pf(v)>=1.20 and all(by[w]["net"]>=0 for w in "ABC")
for f,z in A.items():
 g=collections.defaultdict(list)
 for r in z["rows"]: g[r.get("pattern","?")].append(r["net"])
 z["pattern_economics"]={p:{"trades":len(v),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v),"win_rate":sum(x>0 for x in v)/len(v)} for p,v in g.items()}
 z["family_detected"]={p:row.get("detected",0) for p,row in z["pipeline"].items()}
 z["commercial_gate"]=controls_ok and f in ["FAMILY_IDENTITY_RECONSTRUCTION","FULL_V52_COMMERCIAL"] and z["baskets"]>=COMM["baskets"] and z["frequency"]>=COMM["frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"] and z.get("marginal",{}).get("pass",False)
 z.pop("rows",None)
eligible=[f for f in ["FAMILY_IDENTITY_RECONSTRUCTION","FULL_V52_COMMERCIAL"] if A[f]["commercial_gate"]]
winner=max(eligible,key=lambda f:(A[f]["net"],A[f]["pf"],A[f]["frequency"])) if eligible else None
front={"version":"HarmonyBot V52","architecture":"HARMONIC_FAMILY_IDENTITY_DETECTION_GRAPH_RECONSTRUCTION",
"v46_control":V46,"v51_math_control":V51,"commercial_minimum":COMM,"controls_reproduced":controls_ok,
"families":A,"development_candidate":winner,"status":"COMMERCIAL_FREEZE_CANDIDATE_DEV_PASS" if winner else "HOLD_WITH_EVIDENCE",
"fresh_used":False,"next_stage":"CAPITAL_COMPATIBILITY" if winner else "STOP_DEV_HOLD"}
(out/"V52_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V52_DETECTOR_TRUTH_LEDGER.json").write_text(json.dumps({f:A[f]["detector_truth"] for f in F},indent=2))
(out/"V52_FAMILY_DETECTION_RECOVERY.json").write_text(json.dumps({f:{"family_detected":A[f]["family_detected"],"pattern_economics":A[f]["pattern_economics"],"pipeline":A[f]["pipeline"]} for f in F},indent=2))
(out/"candidate.txt").write_text(winner or "")
(out/"V52_FINAL_COMMERCIAL_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V52","decision":"COMMERCIAL_FREEZE_CANDIDATE_DEV_PASS" if winner else "HOLD_WITH_EVIDENCE","stage":"DEV","fresh_used":False},indent=2))
print(json.dumps(front,indent=2))
