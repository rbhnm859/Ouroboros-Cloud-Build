#!/usr/bin/env python3
import json,pathlib,sys,collections,re
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["V46_SCALE_CONTROL","V50_FULL_CONTROL","FAMILY_NATIVE_MATH_GEOMETRY","FULL_V51_COMMERCIAL"]
V46={"baskets":39,"frequency":26.0,"net":1721.72,"pf":2.1833,"expectancy":44.15,"win_rate":.5128,"max_dd_pct":4.56}
V50={"baskets":57,"frequency":38.0,"net":1742.74,"pf":1.8413,"expectancy":30.57,"win_rate":.4912,"max_dd_pct":5.17}
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
 anchors=[a for x in xs for a in x.get("entry_anchor_forensics",[])]
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len(setups),"net":sum(v),"pf":pf(v),
 "expectancy":sum(v)/n if n else 0,"win_rate":sum(x>0 for x in v)/n if n else 0,
 "max_dd_pct":max(x["max_dd_pct"] for x in xs),"all_windows_positive":all(x["net"]>0 for x in xs),
 "engineering_clean":all(x["engineering_clean"] for x in xs),
 "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
 "windows":{w:rd(f,w) for w in "ABC"},"rows":rows,"entry_anchor_forensics":anchors}
A={f:agg(f) for f in F}
def repro(z,b):
 return z["baskets"]==b["baskets"] and abs(z["net"]-b["net"])<=.15 and abs(z["pf"]-b["pf"])<=.003 and abs(z["max_dd_pct"]-b["max_dd_pct"])<=.08
A["V46_SCALE_CONTROL"]["control_reproduction_pass"]=repro(A["V46_SCALE_CONTROL"],V46)
A["V50_FULL_CONTROL"]["control_reproduction_pass"]=repro(A["V50_FULL_CONTROL"],V50)
controls_ok=A["V46_SCALE_CONTROL"]["control_reproduction_pass"] and A["V50_FULL_CONTROL"]["control_reproduction_pass"]
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
 econ={p:{"trades":len(v),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v),"win_rate":sum(x>0 for x in v)/len(v)} for p,v in g.items()}
 promotion={}
 for p,e in econ.items():
  if e["trades"]>=10 and e["net"]>0 and e["pf"]>=1.20 and e["expectancy"]>0: status="LIVE_ELIGIBLE_DEV"
  elif e["trades"]>=5 and (e["net"]<=0 or e["pf"]<1.0): status="DISABLED_EVIDENCE"
  else: status="SHADOW_INSUFFICIENT_OR_UNSTABLE"
  promotion[p]={"status":status,**e}
 z["pattern_economics"]=econ; z["family_promotion"]=promotion
 z["commercial_gate"]=controls_ok and f not in ["V46_SCALE_CONTROL","V50_FULL_CONTROL"] and z["baskets"]>=COMM["baskets"] and z["frequency"]>=COMM["frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"] and z.get("marginal",{}).get("pass",False)
 z.pop("rows",None)
eligible=[f for f in ["FAMILY_NATIVE_MATH_GEOMETRY","FULL_V51_COMMERCIAL"] if A[f]["commercial_gate"]]
winner=max(eligible,key=lambda f:(A[f]["net"],A[f]["pf"],A[f]["frequency"])) if eligible else None
front={"version":"HarmonyBot V51","architecture":"FAMILY_NATIVE_MATHEMATICAL_GEOMETRY_ECONOMIC_CONVERSION",
"v46_control":V46,"v50_control":V50,"commercial_minimum":COMM,"controls_reproduced":controls_ok,
"families":A,"development_candidate":winner,"status":"COMMERCIAL_FREEZE_CANDIDATE_DEV_PASS" if winner else "HOLD_WITH_EVIDENCE",
"fresh_used":False,"next_stage":"CAPITAL_COMPATIBILITY" if winner else "STOP_DEV_HOLD"}
(out/"V51_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V51_PATTERN_FAMILY_PROMOTION.json").write_text(json.dumps({f:A[f]["family_promotion"] for f in F},indent=2))
(out/"V51_ENTRY_ANCHOR_FORENSICS.json").write_text(json.dumps({f:A[f]["entry_anchor_forensics"] for f in F},indent=2))
(out/"candidate.txt").write_text(winner or "")
(out/"V51_FINAL_COMMERCIAL_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V51","decision":"COMMERCIAL_FREEZE_CANDIDATE_DEV_PASS" if winner else "HOLD_WITH_EVIDENCE","stage":"DEV","fresh_used":False},indent=2))
print(json.dumps(front,indent=2))
