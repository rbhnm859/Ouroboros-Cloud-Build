#!/usr/bin/env python3
import json,pathlib,sys,os,hashlib
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); manifest_path=pathlib.Path(sys.argv[3])
out.mkdir(parents=True,exist_ok=True)
CAP="B_V72_HCAP_ALPHA"; BASE="A_V51_CHAMPION_KERNEL"; W=["Y2021","Y2022","Y2023"]
V51={"frequency":38.6667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
TARGET={"annual_return_pct":150.0,"annual_net_multiple":1.50,"pf":3.0,"max_dd_pct":10.0,
        "win_rate":.68,"independent_trades_per_year":200,"average_realized_rr":2.2,"profitable_months":11}
def annual_target_pass(x):
    return bool(float(x.get("return_pct",0))>=TARGET["annual_return_pct"] and
                float(x.get("net",0))>=float(x.get("starting_balance",10000))*TARGET["annual_net_multiple"] and
                float(x.get("pf",0))>=TARGET["pf"] and float(x.get("max_dd_pct",999))<=TARGET["max_dd_pct"] and
                float(x.get("win_rate",0))>=TARGET["win_rate"] and int(x.get("baskets",0))>=TARGET["independent_trades_per_year"] and
                bool(x.get("log_basket_telemetry_complete",False)) and
                float(x.get("average_realized_rr",0))>=TARGET["average_realized_rr"] and
                int(x.get("positive_months",0))>=TARGET["profitable_months"])
VIOL=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
      "gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations",
      "execution_state_violations","margin_risk_violations"]

def find(n):
    xs=list(root.rglob(n))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {n}: {len(xs)}")
    return xs[0]
def pf(rows):
    gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
    return gp/gl if gl else (999 if gp else 0)
def aggregate(xs_by_w):
    xs=[xs_by_w[w] for w in W]; rows=[r for x in xs for r in x["basket_outcomes"]]
    n=len(rows); net=sum(r["net"] for r in rows)
    return {"baskets":n,"frequency":n/3.0,"net":net,"pf":pf(rows),"expectancy":net/n if n else 0,
            "win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,
            "max_dd_pct":max(x["max_dd_pct"] for x in xs),
            "positive_windows":sum(x["net"]>0 for x in xs),
            "engineering_clean":all(x["engineering_clean"] for x in xs),
            "violation_totals":{k:sum(int(x.get(k,0)) for x in xs) for k in VIOL},
            "windows":{w:{k:xs_by_w[w][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct"]} for w in W}}
def sig(rows): return {(r["setup"],r["pattern"],r["route"]) for r in rows}
def fp(x):
    z=x.get("core_execution_fingerprint")
    return (int(z["executed"]),str(z["fnv64"]).upper()) if z and z.get("fnv64") else None

manifest=json.load(open(manifest_path)); payoff_gate=bool(manifest.get("hcap_gate",False))
REF={w:json.load(open(find(f"V51_REFERENCE-{w}.json"))) for w in W}
A={BASE:aggregate(REF)}; A[BASE]["core_preserved"]=True
candidate=None; marginal={}; cap_gate=False

if payoff_gate:
    R={w:json.load(open(find(f"{CAP}-{w}.json"))) for w in W}
    def core_preserved():
        for w in W:
            ref=REF[w]; cur=R[w]
            if ref.get("data_snapshot_sha256")!=cur.get("data_snapshot_sha256"): return False
            a,z=fp(ref),fp(cur)
            if a is not None and z is not None:
                if a!=z:return False
            elif sig(cur["core_basket_outcomes"])!=sig(ref["core_basket_outcomes"]): return False
        return True
    Z=aggregate(R); Z["core_preserved"]=core_preserved()
    Z["annual_commercial_targets"]={w:{"pass":annual_target_pass(R[w]),
        "return_pct":R[w].get("return_pct",0),"net":R[w].get("net",0),"pf":R[w].get("pf",0),
        "max_dd_pct":R[w].get("max_dd_pct",0),"win_rate":R[w].get("win_rate",0),
        "independent_trades":R[w].get("baskets",0),"average_realized_rr":R[w].get("average_realized_rr",0),
        "profitable_months":R[w].get("positive_months",0)} for w in W}
    annual_target_3of3=all(v["pass"] for v in Z["annual_commercial_targets"].values())
    exp=[r for w in W for r in R[w]["expansion_basket_outcomes"]]
    exp_pf=pf(exp); exp_net=sum(r["net"] for r in exp); exp_pos=sum(R[w]["expansion_metrics"]["net"]>0 for w in W)
    Z["expansion_metrics"]={"baskets":len(exp),"net":exp_net,"pf":exp_pf,"positive_windows":exp_pos}
    breakthrough={
      "net_50pct":Z["net"]>=1.50*V51["net"],
      "pf_15pct":Z["pf"]>=1.15*V51["pf"],
      "expectancy_25pct":Z["expectancy"]>=1.25*V51["expectancy"],
      "frequency_50pct":Z["frequency"]>=1.50*V51["frequency"],
      "win_rate_plus_7p5pp":Z["win_rate"]>=V51["win_rate"]+.075,
      "dd_minus_20pct":Z["max_dd_pct"]<=.80*V51["max_dd_pct"]}
    Z["material_breakthrough"]=breakthrough
    Z["material_breakthrough_pass"]=bool(breakthrough["net_50pct"] and sum(bool(v) for k,v in breakthrough.items() if k!="net_50pct")>=1)
    A[CAP]=Z
    marginal={"delta_net":Z["net"]-A[BASE]["net"],"delta_pf":Z["pf"]-A[BASE]["pf"],
              "delta_expectancy":Z["expectancy"]-A[BASE]["expectancy"],
              "positive_delta_windows":sum(R[w]["net"]>REF[w]["net"] for w in W)}
    cap_gate=(Z["core_preserved"] and Z["engineering_clean"] and annual_target_3of3 and all(int(Z["violation_totals"].get(k,0))==0 for k in VIOL)
              and Z["positive_windows"]==3 and Z["frequency"]>=200
              and Z["net"]>V51["net"] and Z["pf"]>V51["pf"] and Z["expectancy"]>V51["expectancy"]
              and Z["win_rate"]>=V51["win_rate"] and Z["max_dd_pct"]<=V51["max_dd_pct"]
              and exp_net>0 and exp_pf>=1.50 and exp_pos==3
              and marginal["delta_net"]>0 and marginal["delta_pf"]>=0 and marginal["delta_expectancy"]>=0
              and marginal["positive_delta_windows"]==3 and Z["material_breakthrough_pass"])
    candidate=CAP if cap_gate else None

freeze={"version":"HarmonyBot V72 Candidate","architecture":"IMMUTABLE_V51_ECONOMIC_SPINE_PLUS_FROZEN_12_FAMILY_EVENT_PLUS_HARMONIC_COUNTERFACTUAL_ACTION_POLICY",
 "trusted_v51_parent":"1b670a0f43ba8ecaa637febfdacf605b1b146f01","control_mode":"DIRECT_TRUSTED_V51_BINARY_REFERENCE",
 "hcap_manifest":manifest,"v51_floor":V51,"commercial_hard_targets":TARGET,"variants":A,"marginal":marginal,
 "gates":{"hcap_counterfactual_alpha_3year":payoff_gate,"hcap_capital_commercial":cap_gate},
 "candidate":candidate,"candidate_selection_source":"BURNED_2021_2023_HCAP_CAUSAL_CONVERSION__TEMPORAL_OOF_ACTION_VALUE_NO_YEAR_FEATURE_NO_THRESHOLD_TUNING",
 "risk_for_alpha_qualification_pct":1.0,"validation_used":False,"fresh_used":False,
 "decision":"V72_HCAP_CANDIDATE_FROZEN" if candidate else ("HCAP_CAUSAL_ALPHA_REJECT" if not payoff_gate else "HCAP_CAPITAL_CONVERSION_REJECT")}
(out/"V71_CALIBRATION_FREEZE.json").write_text(json.dumps(freeze,indent=2))
(out/"candidate.txt").write_text(candidate or "")
(out/"dev_matrix.json").write_text(json.dumps([candidate] if candidate else [],separators=(",",":")))
summary={"version":"HarmonyBot V71 -> V72","source_sha":os.environ.get("GITHUB_SHA","UNKNOWN"),
 "candidate":candidate,"payoff_gate":payoff_gate,"capital_gate":cap_gate,
 "validation_access_count":0,"fresh_access_count":0,
 "manifest_sha256":hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
 "decision":"V72_PRE_DEV_PASS" if candidate else "HOLD_WITH_EVIDENCE"}
(out/"V71_BREAKTHROUGH_MANIFEST.json").write_text(json.dumps(summary,indent=2))
print(json.dumps(freeze,indent=2)); print(json.dumps(summary,indent=2))
