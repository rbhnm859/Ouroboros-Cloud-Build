#!/usr/bin/env python3
import json,pathlib,sys,os,hashlib
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); model_manifest=pathlib.Path(sys.argv[3])
out.mkdir(parents=True,exist_ok=True)
CAP=["B_H5_SINGLE_REACTION","C_H5_GRID_REACTION","D_H5_SINGLE_RUNNER","E_H5_GRID_RUNNER"]
BASE="A_V51_CHAMPION_KERNEL"; W=["Y2021","Y2022","Y2023"]
V51={"frequency":38.6667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
VIOL=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]

def find(n):
    xs=list(root.rglob(n))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {n}: {len(xs)}")
    return xs[0]

model=json.load(open(model_manifest)); model_gate=bool(model.get("crossfit_gate"))
REF={w:json.load(open(find(f"V51_REFERENCE-{w}.json"))) for w in W}
R={(v,w):json.load(open(find(f"{v}-{w}.json"))) for v in CAP for w in W} if model_gate else {}

def pf(rows):
    gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
    return gp/gl if gl else (999 if gp else 0)

def aggregate(xs_by_w):
    xs=[xs_by_w[w] for w in W]; rows=[r for x in xs for r in x["basket_outcomes"]]; n=len(rows); net=sum(r["net"] for r in rows)
    return {"baskets":n,"frequency":n/3.0,"net":net,"pf":pf(rows),"expectancy":net/n if n else 0,
      "win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,"max_dd_pct":max(x["max_dd_pct"] for x in xs),
      "positive_windows":sum(x["net"]>0 for x in xs),"engineering_clean":all(x["engineering_clean"] for x in xs),
      "violation_totals":{k:sum(int(x.get(k,0)) for x in xs) for k in VIOL},
      "windows":{w:{k:xs_by_w[w][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct"]} for w in W}}

A={BASE:aggregate(REF)}
A[BASE]["core_preserved"]=True
A[BASE]["expansion_metrics"]={"baskets":0,"net":0,"pf":0,"positive_windows":0}

def sig(rows): return {(r["setup"],r["pattern"],r["route"]) for r in rows}
def fp(x):
    z=x.get("core_execution_fingerprint")
    return (int(z["executed"]),str(z["fnv64"]).upper()) if z and z.get("fnv64") else None
def core_preserved(v):
    for w in W:
        ref=REF[w]; cur=R[(v,w)]
        if not ref.get("data_snapshot_sha256") or ref.get("data_snapshot_sha256")!=cur.get("data_snapshot_sha256"): return False
        a,z=fp(ref),fp(cur)
        if a is not None and z is not None:
            if a!=z:return False
        elif sig(cur["core_basket_outcomes"])!=sig(ref["core_basket_outcomes"]):return False
    return True
def exp_rows(v): return [r for w in W for r in R[(v,w)]["expansion_basket_outcomes"]]
def exp_windows_positive(v): return sum(R[(v,w)]["expansion_metrics"]["net"]>0 for w in W)
def material_breakthrough(z):
    x={"net_25pct":z["net"]>=1.25*V51["net"],
       "pf_10pct":z["pf"]>=1.10*V51["pf"],
       "expectancy_10pct":z["expectancy"]>=1.10*V51["expectancy"],
       "win_rate_plus_5pp":z["win_rate"]>=V51["win_rate"]+.05,
       "dd_minus_15pct":z["max_dd_pct"]<=.85*V51["max_dd_pct"]}
    return x,sum(bool(v) for v in x.values())>=2
def floor(z):
    br,brpass=material_breakthrough(z)
    return z["positive_windows"]==3 and z["net"]>V51["net"] and z["pf"]>V51["pf"] and z["expectancy"]>V51["expectancy"] and z["win_rate"]>=V51["win_rate"] and z["frequency"]>=60 and z["max_dd_pct"]<=V51["max_dd_pct"] and z["engineering_clean"] and all(int(z["violation_totals"].get(k,0))==0 for k in VIOL) and brpass
def expansion_good(v):
    e=exp_rows(v)
    return len(e)>0 and sum(r["net"] for r in e)>0 and pf(e)>=1.50 and exp_windows_positive(v)==3
def delta(v,a):
    ref=lambda w: REF[w] if a==BASE else R[(a,w)]
    return {"delta_net":A[v]["net"]-A[a]["net"],"delta_pf":A[v]["pf"]-A[a]["pf"],"delta_expectancy":A[v]["expectancy"]-A[a]["expectancy"],
            "positive_delta_windows":sum(R[(v,w)]["net"]>ref(w)["net"] for w in W)}
def nonreg(d,positive_windows=3):
    return d["delta_net"]>0 and d["delta_pf"]>=0 and d["delta_expectancy"]>=0 and d["positive_delta_windows"]==positive_windows

M={}; legal={v:False for v in CAP}; candidate=None
if model_gate:
    for v in CAP:
        A[v]=aggregate({w:R[(v,w)] for w in W}); A[v]["core_preserved"]=core_preserved(v)
        e=exp_rows(v); A[v]["expansion_metrics"]={"baskets":len(e),"net":sum(r["net"] for r in e),"pf":pf(e),"positive_windows":exp_windows_positive(v)}
        A[v]["material_breakthrough"],A[v]["material_breakthrough_pass"]=material_breakthrough(A[v])
    B,C,D,E=CAP
    M={"B-A":delta(B,BASE),"C-A":delta(C,BASE),"D-A":delta(D,BASE),"E-A":delta(E,BASE),
       "C-B":delta(C,B),"D-B":delta(D,B),"E-C":delta(E,C),"E-D":delta(E,D)}
    base_ok={v:core_preserved(v) and floor(A[v]) and expansion_good(v) and nonreg(M[f"{v[0]}-A"]) for v in CAP}
    legal[B]=base_ok[B]
    legal[C]=base_ok[C] and nonreg(M["C-B"])
    legal[D]=base_ok[D] and nonreg(M["D-B"])
    legal[E]=base_ok[E] and nonreg(M["E-C"]) and nonreg(M["E-D"])
    candidates=[v for v in CAP if legal[v]]
    candidate=max(candidates,key=lambda v:(A[v]["net"],A[v]["pf"],A[v]["expectancy"])) if candidates else None

freeze={"version":"HarmonyBot V71","architecture":"IMMUTABLE_V51_CHAMPION_KERNEL_PLUS_FROZEN_HARMONIC_DETECTOR_PLUS_H5_POSTERIOR_ALPHA",
 "trusted_v51_parent":"1b670a0f43ba8ecaa637febfdacf605b1b146f01","control_mode":"DIRECT_TRUSTED_V51_BINARY_REFERENCE","windows":W,
 "v51_reference_direct_kernel":True,"detector_frozen":True,"edge_model_crossfit_gate":model_gate,"edge_model_manifest":model,"v51_floor":V51,"variants":A,"marginal":M,
 "gates":{"B_h5_single_reaction":legal[CAP[0]],"C_h5_grid_reaction":legal[CAP[1]],"D_h5_single_runner":legal[CAP[2]],"E_h5_grid_runner":legal[CAP[3]]},
 "counterfactual_rules":{"grid_requires_nonregression_vs_same_exit_single":True,"runner_requires_nonregression_vs_reaction_same_grid_state":True,
                         "combined_grid_runner_requires_nonregression_vs_grid_reaction_and_single_runner":True},
 "breakthrough_rule":"PARETO_NON_REGRESSION_PLUS_AT_LEAST_2_OF_NET25_PF10_EXP10_WR5PP_DD15","candidate":candidate,
 "candidate_selection_source":"BURNED_2021_2023_ONLY__H5_NESTED_FRONTIER_3OF3_DUAL_POSTERIOR_LCB_BEFORE_CAPITAL",
 "risk_for_alpha_qualification_pct":1.0,"validation_used":False,"fresh_used":False,
 "decision":"CALIBRATION_CANDIDATE_FROZEN" if candidate else ("CROSSFIT_FAIL_CLOSED_HOLD" if not model_gate else "CALIBRATION_HOLD")}
(out/"V71_CALIBRATION_FREEZE.json").write_text(json.dumps(freeze,indent=2))
(out/"candidate.txt").write_text(candidate or "")
(out/"dev_matrix.json").write_text(json.dumps([candidate] if candidate else [],separators=(",",":")))
manifest={"version":"HarmonyBot V71","source_sha":os.environ.get("GITHUB_SHA","UNKNOWN"),
 "breakthrough_definition":{"immutable_v51_direct_kernel":True,"frozen_detector_oracle_gate":bool(model.get("detector_recall_gate")),
                            "h5_nested_frontier_crossfit_3of3":model_gate,"calibration_candidate_over_v51_floor":bool(candidate)},
 "selected_architecture":model.get("selected_architecture"),"selected_frontier":model.get("common_frontier"),"crossfit_folds":model.get("folds"),
 "candidate":candidate,"risk_pct":1.0,"validation_access_count":0,"fresh_access_count":0,
 "all_engineering_clean":all(z["engineering_clean"] for z in A.values()),"all_violation_totals":{v:A[v]["violation_totals"] for v in A},
 "model_manifest_sha256":hashlib.sha256(model_manifest.read_bytes()).hexdigest(),
 "decision":"BREAKTHROUGH_PRE_DEV_PASS" if candidate else "HOLD_WITH_EVIDENCE"}
(out/"V71_BREAKTHROUGH_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(freeze,indent=2)); print(json.dumps(manifest,indent=2))
