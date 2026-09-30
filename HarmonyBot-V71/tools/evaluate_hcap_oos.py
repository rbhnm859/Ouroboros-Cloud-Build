#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); stage=sys.argv[3].upper()
years=float(sys.argv[4]); windows=[x for x in sys.argv[5].split(",") if x]
out.mkdir(parents=True,exist_ok=True)
CAND="B_V72_HCAP_ALPHA"
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
gate=(metrics["engineering_clean"] and core_preserved and all(v==0 for v in viol.values()) and
      metrics["positive_windows"]==len(windows) and metrics["positive_delta_windows"]==len(windows) and
      metrics["frequency"]>=60.0 and metrics["pf"]>1.25 and metrics["expectancy"]>0 and metrics["max_dd_pct"]<=10.0)
manifest={"architecture":"V72_HARMONIC_COUNTERFACTUAL_ACTION_POLICY","stage":stage,"windows":windows,
          "years":years,"candidate":CAND,"metrics":metrics,"violations":viol,
          "core_displacement_zero":core_preserved,
          "window_metrics":{w:{"candidate":{k:C[w][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct"]},
                               "control":{k:REF[w][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct"]}}
                            for w in windows},
          "gate":gate,
          "gate_semantics":"POSITIVE_EVERY_WINDOW_DELTA_NET_POSITIVE_EVERY_WINDOW_FREQ_GE_60_PF_GT_1P25_EXPECTANCY_GT_0_DD_LE_10_CORE_DISPLACEMENT_ZERO_ZERO_ENGINEERING_VIOLATIONS",
          "validation_used":stage=="VALIDATION","fresh_used":stage=="FRESH"}
(out/f"HCAP_{stage}_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
(out/"pass.txt").write_text("true" if gate else "false")
print(json.dumps(manifest,indent=2))
