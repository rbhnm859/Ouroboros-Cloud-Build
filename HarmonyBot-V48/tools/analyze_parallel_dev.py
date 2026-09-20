#!/usr/bin/env python3
import json,pathlib,sys,collections,statistics
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V48/merged")
out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "HarmonyBot-V48/final"); out.mkdir(parents=True,exist_ok=True)
fams=["V46_SCALE_CONTROL","STRUCTURAL_GEOMETRY_REPAIR","FAMILY_NATIVE_EXECUTION","FULL_V48_FAMILY_PORTFOLIO"]
control="V46_SCALE_CONTROL"
V46={"baskets":39,"frequency":26.0,"net":1721.72,"pf":2.1833,"expectancy":44.15,"win_rate":0.5128,"max_dd_pct":4.56}
V36={"baskets":77,"frequency":51.333333333333336,"net":648.58,"pf":1.2124297856312334,"expectancy":8.423116883116883,"win_rate":0.42857142857142855,"max_dd_pct":8.768267223382058}
COMM={"baskets":90,"frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":0.50,"max_dd_pct":6.0}
DORMANT={"Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","5-0"}

def locate(name):
 xs=list(root.rglob(name))
 if not xs: raise SystemExit("missing "+name)
 return xs[0]
def read(f,w): return json.load(open(locate(f"{f}-{w}.json")))
def pf_of(vals):
 gp=sum(v for v in vals if v>0); gl=abs(sum(v for v in vals if v<0))
 return gp/gl if gl else (999 if gp else 0)
def family(p):
 if p in {"Gartley","Bat","Deep Gartley","Rat"}: return "RETRACEMENT"
 if p in {"Alt Bat","Butterfly","Crab","Deep Crab"}: return "EXTENSION"
 if p in {"Shark","5-0"}: return "TRANSITION"
 if p=="Cypher": return "XC_RETRACE"
 if p=="AB=CD": return "COMPLETION_SYMMETRY"
 return "OTHER"
def agg(f):
 xs=[read(f,w) for w in "ABC"]
 rows=[r for x in xs for r in x.get("basket_outcomes",[])]
 vals=[r["net"] for r in rows]; n=len(rows); gp=sum(v for v in vals if v>0); gl=abs(sum(v for v in vals if v<0))
 setups={r["setup"] for r in rows}
 return {"baskets":n,"unique_setups":len(setups),"duplicate_reentries":n-len(setups),"frequency":n/1.5,
         "net":sum(vals),"pf":gp/gl if gl else (999 if gp else 0),"expectancy":sum(vals)/n if n else 0,
         "win_rate":sum(v>0 for v in vals)/n if n else 0,"max_dd_pct":max(x["max_dd_pct"] for x in xs),
         "all_windows_positive":all(x["net"]>0 for x in xs),"engineering_clean":all(x["engineering_clean"] for x in xs),
         "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 and x["unprotected_survivors"]==0 for x in xs),
         "family_native_pass":sum(x.get("family_native_pass",0) for x in xs),
         "family_grid_envelope_accepted":sum(x.get("family_grid_envelope_accepted",0) for x in xs),
         "family_grid_envelope_rejected":sum(x.get("family_grid_envelope_rejected",0) for x in xs),
         "family_route_rejected":sum(x.get("family_route_rejected",0) for x in xs),
         "family_structural_extension_repairs":sum(x.get("family_structural_extension_repairs",0) for x in xs),
         "windows":{w:read(f,w) for w in "ABC"},"rows":rows}
A={f:agg(f) for f in fams}
c=A[control]
c["baseline_reproduction"]={"pass":c["baskets"]==39 and abs(c["net"]-V46["net"])<=.20 and abs(c["pf"]-V46["pf"])<=.002 and abs(c["expectancy"]-V46["expectancy"])<=.10 and abs(c["win_rate"]-V46["win_rate"])<=.002 and abs(c["max_dd_pct"]-V46["max_dd_pct"])<=.05 and c["duplicate_reentries"]==0 and c["engineering_clean"] and c["risk_clean"]}

control_sets={w:{r["setup"] for r in read(control,w).get("basket_outcomes",[])} for w in "ABC"}
def marginal(f):
 by={}; added=[]
 for w in "ABC":
  rr=[r for r in read(f,w).get("basket_outcomes",[]) if r["setup"] not in control_sets[w]]
  vals=[r["net"] for r in rr]; added.extend(rr)
  by[w]={"trades":len(rr),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals)}
 vals=[r["net"] for r in added]
 z={"trades":len(added),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals),"windows":by,"all_windows_non_negative":all(by[w]["net"]>=0 for w in "ABC")}
 z["pass"]=z["trades"]>0 and z["net"]>0 and z["expectancy"]>0 and z["pf"]>=1.20 and z["all_windows_non_negative"]
 return z

def pattern_economics(rows):
 g=collections.defaultdict(list)
 for r in rows:g[r["pattern"]].append(r["net"])
 return {p:{"trades":len(v),"net":sum(v),"expectancy":sum(v)/len(v),"pf":pf_of(v),"win_rate":sum(x>0 for x in v)/len(v)} for p,v in sorted(g.items())}

def family_economics(rows):
 g=collections.defaultdict(list)
 for r in rows:g[family(r["pattern"])].append(r["net"])
 return {p:{"trades":len(v),"net":sum(v),"expectancy":sum(v)/len(v),"pf":pf_of(v),"win_rate":sum(x>0 for x in v)/len(v)} for p,v in sorted(g.items())}

for f in fams:
 A[f]["marginal_vs_control"]=None if f==control else marginal(f)
 pe=pattern_economics(A[f]["rows"]); fe=family_economics(A[f]["rows"])
 A[f]["pattern_economics"]=pe; A[f]["family_economics"]=fe
 dormant={}
 for p in sorted(DORMANT):
  m=pe.get(p,{"trades":0,"net":0,"expectancy":0,"pf":0,"win_rate":0})
  m=dict(m); m["eligible_sample"]=m["trades"]>=3; m["pass"]=m["trades"]<3 or (m["net"]>0 and m["pf"]>=1.10)
  dormant[p]=m
 A[f]["dormant_pattern_gate"]=dormant
 A[f]["dormant_pattern_gate_pass"]=all(x["pass"] for x in dormant.values())
 A[f]["v36_all_metric_dominance"]=(f!=control and A[f]["baskets"]>V36["baskets"] and A[f]["frequency"]>V36["frequency"] and A[f]["net"]>V36["net"] and A[f]["pf"]>V36["pf"] and A[f]["expectancy"]>V36["expectancy"] and A[f]["win_rate"]>V36["win_rate"] and A[f]["max_dd_pct"]<V36["max_dd_pct"] and A[f]["all_windows_positive"] and A[f]["duplicate_reentries"]==0 and A[f]["engineering_clean"] and A[f]["risk_clean"])
 marg=A[f]["marginal_vs_control"]
 A[f]["commercial_freeze_candidate_gate"]=(c["baseline_reproduction"]["pass"] and f!=control and A[f]["v36_all_metric_dominance"] and A[f]["baskets"]>=COMM["baskets"] and A[f]["frequency"]>=COMM["frequency"] and A[f]["net"]>=COMM["net"] and A[f]["pf"]>=COMM["pf"] and A[f]["expectancy"]>=COMM["expectancy"] and A[f]["win_rate"]>=COMM["win_rate"] and A[f]["max_dd_pct"]<=COMM["max_dd_pct"] and A[f]["all_windows_positive"] and marg is not None and marg["pass"] and A[f]["dormant_pattern_gate_pass"])

# Funnel / rejection attribution.
funnel={}; reject={}
for f in fams:
 fp=collections.defaultdict(collections.Counter); rp=collections.defaultdict(collections.Counter)
 for w in "ABC":
  for e in read(f,w).get("events",[]):
   p=e["pattern"]; reason=e["reason"]; state=e["state"]
   if "PATTERN_DETECTED" in reason: fp[p]["detected"]+=1
   if "PATTERN_VALIDATED" in reason: fp[p]["validated"]+=1
   if "ROUTE_" in reason: fp[p]["routed"]+=1
   if "PRZ_RETEST" in reason: fp[p]["confirming"]+=1
   if "FAMILY_NATIVE_M1_PASS" in reason: fp[p]["family_native_pass"]+=1
   if "CONFIRMATION_PASSED_GRID_PREPLANNED" in reason: fp[p]["armed"]+=1
   if "FIB_GRID_LEG0_FILLED" in reason: fp[p]["executed"]+=1
   if reason.startswith("REJECTED:") or reason.startswith("EXPIRED:") or reason.startswith("INVALIDATED:") or "FAILED" in reason:
    rp[p][reason.split("_")[0] if reason.startswith("LEGACY_CONFIRMATION_FAILED") else reason]+=1
 funnel[f]={p:dict(v) for p,v in sorted(fp.items())}; reject[f]={p:dict(v) for p,v in sorted(rp.items())}
(out/"V48_PATTERN_FUNNEL.json").write_text(json.dumps({"version":"HarmonyBot V48","families":funnel},indent=2))
(out/"V48_PATTERN_REJECTION_ATTRIBUTION.json").write_text(json.dumps({"version":"HarmonyBot V48","families":reject},indent=2))
(out/"V48_PATTERN_FAMILY_ECONOMICS.json").write_text(json.dumps({"version":"HarmonyBot V48","families":{f:{"pattern":A[f]["pattern_economics"],"family":A[f]["family_economics"],"dormant_gate":A[f]["dormant_pattern_gate"]} for f in fams}},indent=2))
(out/"V48_MARGINAL_FREQUENCY_REPORT.json").write_text(json.dumps({"version":"HarmonyBot V48","control":control,"families":{f:A[f]["marginal_vs_control"] for f in fams if f!=control}},indent=2))
(out/"V48_V36_DOMINANCE.json").write_text(json.dumps({"version":"HarmonyBot V48","benchmark":V36,"families":{f:A[f]["v36_all_metric_dominance"] for f in fams}},indent=2))
(out/"V48_COMMERCIAL_FREEZE_GATE.json").write_text(json.dumps({"version":"HarmonyBot V48","minimum":COMM,"families":{f:A[f]["commercial_freeze_candidate_gate"] for f in fams}},indent=2))

eligible=[(A[f]["net"],A[f]["pf"],A[f]["frequency"],-A[f]["max_dd_pct"],f) for f in fams if A[f]["commercial_freeze_candidate_gate"]]
eligible.sort(reverse=True); winner=eligible[0][-1] if eligible else None
for f in fams: A[f].pop("rows",None)
status="COMMERCIAL_FREEZE_CANDIDATE_PASS" if winner else "HOLD_WITH_EVIDENCE"
frontier={"version":"HarmonyBot V48","architecture":"FAMILY_NATIVE_HARMONIC_PORTFOLIO_REFORM","v46_scale_baseline":V46,"v36_benchmark":V36,"commercial_candidate_minimum":COMM,"baseline_reproduction_pass":c["baseline_reproduction"]["pass"],"families":A,"development_candidate":winner,"status":status,"fresh_used":False,"next_stage":"CAPITAL_COMPATIBILITY" if winner else "STOP_DEV_HOLD"}
(out/"V48_PERFORMANCE_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
(out/"V48_FINAL_COMMERCIAL_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V48","decision":status,"candidate":winner,"fresh_used":False},indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps(frontier,indent=2))
