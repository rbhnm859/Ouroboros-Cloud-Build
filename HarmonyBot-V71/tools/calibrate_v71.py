#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); model_manifest=pathlib.Path(sys.argv[3])
out.mkdir(parents=True,exist_ok=True)
V=["A_V51_PROTECTED_CORE","B_PROTECTED_XFIT_SINGLE","C_PROTECTED_XFIT_GRID","D_PROTECTED_XFIT_GRID_RISK5"]
W=["Y2021","Y2022","Y2023"]
V51={"frequency":38.6667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
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
 xs=[R[(v,w)] for w in W]; rows=[r for x in xs for r in x["basket_outcomes"]]
 n=len(rows); net=sum(r["net"] for r in rows)
 return {"baskets":n,"frequency":n/3.0,"net":net,"pf":pf(rows),"expectancy":net/n if n else 0,
  "win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,"max_dd_pct":max(x["max_dd_pct"] for x in xs),
  "positive_windows":sum(x["net"]>0 for x in xs),"engineering_clean":all(x["engineering_clean"] for x in xs),
  "windows":{w:{k:R[(v,w)][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct"]} for w in W},
  "_rows":rows}
A={v:agg(v) for v in V}
replay={}
replay_evidence={}
for w in W:
 a=R[(V[0],w)]; r=REF[w]
 report_exact=(a.get("canonical_report_sha256") and a.get("canonical_report_sha256")==r.get("canonical_report_sha256"))
 pipeline_exact=(a.get("core_pipeline_sha256") and a.get("core_pipeline_sha256")==r.get("core_pipeline_sha256"))
 replay[w]=bool(report_exact and pipeline_exact)
 replay_evidence[w]={"canonical_report_exact":bool(report_exact),"core_pipeline_exact":bool(pipeline_exact),
                     "a_report_sha256":a.get("canonical_report_sha256"),"reference_report_sha256":r.get("canonical_report_sha256"),
                     "a_pipeline_sha256":a.get("core_pipeline_sha256"),"reference_pipeline_sha256":r.get("core_pipeline_sha256")}
replay_gate=all(replay.values())

def sig(rows):
 return {(r["setup"],r["pattern"],r["route"]) for r in rows}
def core_fp(x):
 z=x.get("core_execution_fingerprint")
 if z and z.get("executed") is not None and z.get("fnv64"):
  return (int(z["executed"]),str(z["fnv64"]).upper())
 return None
core_sig={w:sig(R[(V[0],w)]["core_basket_outcomes"]) for w in W}
def core_preserved(v):
 for w in W:
  a=core_fp(R[(V[0],w)]); z=core_fp(R[(v,w)])
  if a is not None and z is not None:
   if z != a: return False
  elif sig(R[(v,w)]["core_basket_outcomes"]) != core_sig[w]:
   return False
 return True
def exp_rows(v): return [r for w in W for r in R[(v,w)]["expansion_basket_outcomes"]]
def exp_windows_positive(v): return sum(R[(v,w)]["expansion_metrics"]["net"]>0 for w in W)
def floor(z):
 return z["positive_windows"]==3 and z["net"]>V51["net"] and z["pf"]>V51["pf"] and z["expectancy"]>V51["expectancy"] and z["win_rate"]>=V51["win_rate"] and z["frequency"]>=60 and z["max_dd_pct"]<=V51["max_dd_pct"] and z["engineering_clean"]
def expansion_good(v):
 e=exp_rows(v)
 return len(e)>0 and sum(r["net"] for r in e)>0 and pf(e)>=1.20 and exp_windows_positive(v)>=2
def delta(v,a):
 return {"delta_net":A[v]["net"]-A[a]["net"],"delta_pf":A[v]["pf"]-A[a]["pf"],"delta_expectancy":A[v]["expectancy"]-A[a]["expectancy"],
         "positive_delta_windows":sum(R[(v,w)]["net"]>R[(a,w)]["net"] for w in W)}
M={"B-A":delta(V[1],V[0]),"C-B":delta(V[2],V[1]),"C-A":delta(V[2],V[0]),"D-C":delta(V[3],V[2])}
model_gate=bool(model.get("crossfit_gate"))
B=replay_gate and model_gate and core_preserved(V[1]) and floor(A[V[1]]) and expansion_good(V[1]) and M["B-A"]["delta_net"]>0 and M["B-A"]["delta_pf"]>=0 and M["B-A"]["delta_expectancy"]>=0 and M["B-A"]["positive_delta_windows"]>=2
C=replay_gate and model_gate and core_preserved(V[2]) and floor(A[V[2]]) and expansion_good(V[2]) and M["C-A"]["delta_net"]>0 and M["C-A"]["delta_pf"]>=0 and M["C-A"]["delta_expectancy"]>=0 and M["C-A"]["positive_delta_windows"]>=2 and A[V[2]]["net"]>A[V[1]]["net"] and A[V[2]]["pf"]>=A[V[1]]["pf"] and A[V[2]]["expectancy"]>=A[V[1]]["expectancy"]
D=core_preserved(V[3]) and A[V[3]]["engineering_clean"] and A[V[3]]["max_dd_pct"]<=10
candidate=V[2] if C else V[1] if B else None
for v in V:
 A[v]["core_preserved"]=core_preserved(v)
 A[v]["expansion_metrics"]={"baskets":len(exp_rows(v)),"net":sum(r["net"] for r in exp_rows(v)),"pf":pf(exp_rows(v)),"positive_windows":exp_windows_positive(v)}
 A[v].pop("_rows",None)
freeze={"version":"HarmonyBot V71","architecture":"PROTECTED_V51_CORE_PLUS_CROSSFIT_INCREMENTAL_EXPANSION",
 "trusted_v51_parent":"1b670a0f43ba8ecaa637febfdacf605b1b146f01","windows":W,
 "v51_reference_replay":replay,"v51_reference_replay_evidence":replay_evidence,"v51_reference_replay_gate":replay_gate,"edge_model_crossfit_gate":model_gate,
 "edge_model_manifest":model,"v51_floor":V51,"variants":A,"marginal":M,
 "gates":{"B_protected_xfit_single":B,"C_protected_xfit_grid":C,"D_risk5_research_only":D},
 "candidate":candidate,"candidate_selection_source":"BURNED_2021_2023_CROSSFIT_ONLY",
 "validation_used":False,"fresh_used":False,"decision":"CALIBRATION_CANDIDATE_FROZEN" if candidate else "CALIBRATION_HOLD"}
(out/"V71_CALIBRATION_FREEZE.json").write_text(json.dumps(freeze,indent=2))
(out/"candidate.txt").write_text(candidate or "")
(out/"dev_matrix.json").write_text(json.dumps([V[0],candidate] if candidate else [V[0]],separators=(",",":")))
print(json.dumps(freeze,indent=2))
