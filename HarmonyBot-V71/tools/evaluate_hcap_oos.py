#!/usr/bin/env python3
import json,pathlib,sys,math
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); stage=sys.argv[3].upper()
years=float(sys.argv[4]); windows=[x for x in sys.argv[5].split(",") if x]
out.mkdir(parents=True,exist_ok=True)
CAND="B_V72_HCAP_ALPHA"
TARGET={"annual_return_pct":150.0,"annual_net_multiple":1.50,"pf":3.0,"max_dd_pct":10.0,
        "win_rate":.68,"independent_trades_per_year":200,"average_realized_rr":2.2,"profitable_months_per_year":11}
VIOL=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders",
      "stop_widening_violations","gap_through_survivors","unprotected_survivors",
      "post_fill_protection_failures","actual_basket_risk_violations",
      "execution_state_violations","margin_risk_violations"]
def find(n):
    xs=list(root.rglob(n))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {n}: {len(xs)}")
    return xs[0]
def pf(rows):
    gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
    return gp/gl if gl else (999.0 if gp else 0.0)
def fp(x):
    z=x.get("core_execution_fingerprint")
    return (int(z["executed"]),str(z["fnv64"]).upper()) if z and z.get("fnv64") else None
def sig(rows): return {(r["setup"],r["pattern"],r["route"]) for r in rows}
REF={w:json.load(open(find(f"V51_REFERENCE-{w}.json"))) for w in windows}
C={w:json.load(open(find(f"{CAND}-{w}.json"))) for w in windows}
core_preserved=True
for w in windows:
    if REF[w].get("data_snapshot_sha256")!=C[w].get("data_snapshot_sha256"): core_preserved=False
    a,b=fp(REF[w]),fp(C[w])
    if a is not None and b is not None:
        if a!=b: core_preserved=False
    elif sig(REF[w]["core_basket_outcomes"])!=sig(C[w]["core_basket_outcomes"]):
        core_preserved=False
rows=[r for w in windows for r in C[w]["basket_outcomes"]]
n=len(rows); net=sum(r["net"] for r in rows)
metrics={"baskets":n,"frequency":n/years if years else 0.0,"net":net,"pf":pf(rows),
         "expectancy":net/n if n else 0.0,
         "win_rate":sum(r["net"]>0 for r in rows)/n if n else 0.0,
         "max_dd_pct":max(C[w]["max_dd_pct"] for w in windows),
         "positive_windows":sum(C[w]["net"]>0 for w in windows),
         "positive_delta_windows":sum(C[w]["net"]>REF[w]["net"] for w in windows),
         "engineering_clean":all(C[w]["engineering_clean"] for w in windows)}
viol={k:sum(int(C[w].get(k,0)) for w in windows) for k in VIOL}
window_years=years/len(windows) if windows else years
target_return=((1.0+TARGET["annual_net_multiple"])**window_years-1.0)*100.0
required_trades=math.ceil(TARGET["independent_trades_per_year"]*window_years)
required_months=math.ceil((TARGET["profitable_months_per_year"]/12.0)*(12.0*window_years)-1e-12)
commercial_windows={}
for w in windows:
    x=C[w]
    commercial_windows[w]={"required_return_pct":target_return,
      "required_net":float(x.get("starting_balance",10000))*target_return/100.0,
      "required_trades":required_trades,"required_profitable_months":required_months,
      "pass":bool(float(x.get("return_pct",0))>=target_return and
                  float(x.get("net",0))>=float(x.get("starting_balance",10000))*target_return/100.0 and
                  float(x.get("pf",0))>=TARGET["pf"] and float(x.get("max_dd_pct",999))<=TARGET["max_dd_pct"] and
                  float(x.get("win_rate",0))>=TARGET["win_rate"] and int(x.get("baskets",0))>=required_trades and
                  bool(x.get("log_basket_telemetry_complete",False)) and
                  float(x.get("average_realized_rr",0))>=TARGET["average_realized_rr"] and
                  int(x.get("positive_months",0))>=required_months)}
commercial_target_pass=all(v["pass"] for v in commercial_windows.values())
gate=(metrics["engineering_clean"] and core_preserved and commercial_target_pass and all(v==0 for v in viol.values()) and
      metrics["positive_windows"]==len(windows) and metrics["positive_delta_windows"]==len(windows))
manifest={"architecture":"V72_HARMONIC_COUNTERFACTUAL_ACTION_POLICY","stage":stage,"windows":windows,
          "years":years,"candidate":CAND,"metrics":metrics,"violations":viol,
          "core_displacement_zero":core_preserved,"commercial_hard_targets":TARGET,
          "commercial_window_targets":commercial_windows,"commercial_target_pass":commercial_target_pass,
          "window_metrics":{w:{"candidate":{k:C[w][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct"]},
                               "control":{k:REF[w][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct"]}}
                            for w in windows},
          "gate":gate,
          "gate_semantics":"EACH_OOS_WINDOW_ANNUAL_EQUIVALENT_RETURN_150PCT_NET_150PCT_PF_GE_3_DD_LE_10_WR_GE_68_INDEPENDENT_TRADES_GE_200_PER_YEAR_AVG_REALIZED_RR_GE_2P2_MONTHLY_CONSISTENCY_GE_11_OF_12_PLUS_POSITIVE_DELTA_CORE_ZERO",
          "validation_used":stage=="VALIDATION","fresh_used":stage=="FRESH"}
(out/f"HCAP_{stage}_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
(out/"pass.txt").write_text("true" if gate else "false")
print(json.dumps(manifest,indent=2))
