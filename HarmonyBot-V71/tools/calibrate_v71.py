#!/usr/bin/env python3
import json,pathlib,sys,os,hashlib
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); model_manifest=pathlib.Path(sys.argv[3])
out.mkdir(parents=True,exist_ok=True)
V=["A_V51_PROTECTED_CORE","B_PROTECTED_XFIT_SINGLE","C_PROTECTED_XFIT_GRID"]
W=["Y2021","Y2022","Y2023"]
V51={"frequency":38.6667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
VIOL=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
"gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
def find(n):
 xs=list(root.rglob(n))
 if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {n}: {len(xs)}")
 return xs[0]
R={(v,w):json.load(open(find(f"{v}-{w}.json"))) for v in V for w in W}
REF={w:json.load(open(find(f"V51_REFERENCE-{w}.json"))) for w in W}
model=json.load(open(model_manifest))
def pf(rows):
 gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
 return gp/gl if gl else (999 if gp else 0)
def agg(v):
 xs=[R[(v,w)] for w in W]; rows=[r for x in xs for r in x["basket_outcomes"]]; n=len(rows); net=sum(r["net"] for r in rows)
 return {"baskets":n,"frequency":n/3.0,"net":net,"pf":pf(rows),"expectancy":net/n if n else 0,
  "win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,"max_dd_pct":max(x["max_dd_pct"] for x in xs),
  "positive_windows":sum(x["net"]>0 for x in xs),"engineering_clean":all(x["engineering_clean"] for x in xs),
  "violation_totals":{k:sum(int(x.get(k,0)) for x in xs) for k in VIOL},
  "windows":{w:{k:R[(v,w)][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct"]} for w in W},
  "_rows":rows}
A={v:agg(v) for v in V}
replay={}; replay_evidence={}
for w in W:
 a=R[(V[0],w)]; r=REF[w]
 report_exact=bool(a.get("canonical_report_sha256") and a.get("canonical_report_sha256")==r.get("canonical_report_sha256"))
 pipe_exact=bool(a.get("core_pipeline_sha256") and a.get("core_pipeline_sha256")==r.get("core_pipeline_sha256"))
 data_exact=bool(a.get("data_snapshot_sha256") and a.get("data_snapshot_sha256")==r.get("data_snapshot_sha256"))
 replay[w]=report_exact and pipe_exact and data_exact
 replay_evidence[w]={"canonical_report_exact":report_exact,"core_pipeline_exact":pipe_exact,"data_snapshot_exact":data_exact,
  "a_report_sha256":a.get("canonical_report_sha256"),"reference_report_sha256":r.get("canonical_report_sha256"),
  "a_pipeline_sha256":a.get("core_pipeline_sha256"),"reference_pipeline_sha256":r.get("core_pipeline_sha256"),
  "a_data_snapshot_sha256":a.get("data_snapshot_sha256"),"reference_data_snapshot_sha256":r.get("data_snapshot_sha256")}
replay_gate=all(replay.values())

def sig(rows): return {(r["setup"],r["pattern"],r["route"]) for r in rows}
def fp(x):
 z=x.get("core_execution_fingerprint")
 return (int(z["executed"]),str(z["fnv64"]).upper()) if z and z.get("fnv64") else None
core_sig={w:sig(R[(V[0],w)]["core_basket_outcomes"]) for w in W}
def core_preserved(v):
 for w in W:
  if not R[(V[0],w)].get("data_snapshot_sha256") or R[(V[0],w)].get("data_snapshot_sha256")!=R[(v,w)].get("data_snapshot_sha256"): return False
  a,z=fp(R[(V[0],w)]),fp(R[(v,w)])
  if a is not None and z is not None:
   if a!=z:return False
  elif sig(R[(v,w)]["core_basket_outcomes"])!=core_sig[w]:return False
 return True
def exp_rows(v): return [r for w in W for r in R[(v,w)]["expansion_basket_outcomes"]]
def exp_windows_positive(v): return sum(R[(v,w)]["expansion_metrics"]["net"]>0 for w in W)
def floor(z):
 return z["positive_windows"]==3 and z["net"]>V51["net"] and z["pf"]>V51["pf"] and z["expectancy"]>V51["expectancy"] and z["win_rate"]>=V51["win_rate"] and z["frequency"]>=60 and z["max_dd_pct"]<=V51["max_dd_pct"] and z["engineering_clean"]
def expansion_good(v):
 e=exp_rows(v); return len(e)>0 and sum(r["net"] for r in e)>0 and pf(e)>=1.20 and exp_windows_positive(v)>=2
def delta(v,a):
 return {"delta_net":A[v]["net"]-A[a]["net"],"delta_pf":A[v]["pf"]-A[a]["pf"],"delta_expectancy":A[v]["expectancy"]-A[a]["expectancy"],
         "positive_delta_windows":sum(R[(v,w)]["net"]>R[(a,w)]["net"] for w in W)}
M={"B-A":delta(V[1],V[0]),"C-B":delta(V[2],V[1]),"C-A":delta(V[2],V[0])}
model_gate=bool(model.get("crossfit_gate"))
B=replay_gate and model_gate and core_preserved(V[1]) and floor(A[V[1]]) and expansion_good(V[1]) and M["B-A"]["delta_net"]>0 and M["B-A"]["delta_pf"]>=0 and M["B-A"]["delta_expectancy"]>=0 and M["B-A"]["positive_delta_windows"]>=2
C=replay_gate and model_gate and core_preserved(V[2]) and floor(A[V[2]]) and expansion_good(V[2]) and M["C-A"]["delta_net"]>0 and M["C-A"]["delta_pf"]>=0 and M["C-A"]["delta_expectancy"]>=0 and M["C-A"]["positive_delta_windows"]>=2 and A[V[2]]["net"]>A[V[1]]["net"] and A[V[2]]["pf"]>=A[V[1]]["pf"] and A[V[2]]["expectancy"]>=A[V[1]]["expectancy"]
candidate=V[2] if C else V[1] if B else None
for v in V:
 A[v]["core_preserved"]=core_preserved(v)
 e=exp_rows(v); A[v]["expansion_metrics"]={"baskets":len(e),"net":sum(r["net"] for r in e),"pf":pf(e),"positive_windows":exp_windows_positive(v)}
 A[v].pop("_rows",None)

freeze={"version":"HarmonyBot V71","architecture":"PROTECTED_V51_CORE_PLUS_PREREGISTERED_HIERARCHICAL_REGIME_SLOT_EXPANSION",
 "trusted_v51_parent":"1b670a0f43ba8ecaa637febfdacf605b1b146f01","windows":W,
 "v51_reference_replay":replay,"v51_reference_replay_evidence":replay_evidence,"v51_reference_replay_gate":replay_gate,
 "edge_model_crossfit_gate":model_gate,"edge_model_manifest":model,"v51_floor":V51,"variants":A,"marginal":M,
 "gates":{"B_protected_xfit_single":B,"C_protected_xfit_grid":C},"candidate":candidate,
 "candidate_selection_source":"BURNED_2021_2023_PREREGISTERED_H1_H2_H3_ONLY","risk_for_alpha_qualification_pct":1.0,
 "validation_used":False,"fresh_used":False,"decision":"CALIBRATION_CANDIDATE_FROZEN" if candidate else "CALIBRATION_HOLD"}
(out/"V71_CALIBRATION_FREEZE.json").write_text(json.dumps(freeze,indent=2))
(out/"candidate.txt").write_text(candidate or "")
(out/"dev_matrix.json").write_text(json.dumps([V[0],candidate] if candidate else [V[0]],separators=(",",":")))
manifest={"version":"HarmonyBot V71","source_sha":os.environ.get("GITHUB_SHA","UNKNOWN"),
 "breakthrough_definition":{"v51_replay_3of3":replay_gate,"core_preserved_B":core_preserved(V[1]),"core_preserved_C":core_preserved(V[2]),
 "crossfit_3of3_conservative_lcb":model_gate,"calibration_candidate_over_v51_floor":bool(candidate)},
 "selected_architecture":model.get("selected_architecture"),"crossfit_folds":model.get("folds"),"challenger_summary":model.get("challenger_summary"),
 "candidate":candidate,"risk_pct":1.0,"validation_access_count":0,"fresh_access_count":0,
 "all_engineering_clean":all(A[v]["engineering_clean"] for v in V),
 "all_violation_totals":{v:A[v]["violation_totals"] for v in V},
 "model_manifest_sha256":hashlib.sha256(model_manifest.read_bytes()).hexdigest(),
 "decision":"BREAKTHROUGH_PRE_DEV_PASS" if candidate else "HOLD_WITH_EVIDENCE"}
(out/"V71_BREAKTHROUGH_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(freeze,indent=2))
print(json.dumps(manifest,indent=2))
