#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
freeze=json.load(open(next(root.rglob("V71_CALIBRATION_FREEZE.json")))); cand=freeze.get("candidate"); V51=freeze["v51_floor"]
W=["H2024H2","H2025H1","H2025H2"]
def find(n):
 xs=list(root.rglob(n))
 if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {n}: {len(xs)}")
 return xs[0]
def pf(rows):
 gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
 return gp/gl if gl else (999 if gp else 0)
def agg(xs_by_w):
 xs=[xs_by_w[w] for w in W]; rows=[r for x in xs for r in x["basket_outcomes"]]; n=len(rows); net=sum(r["net"] for r in rows)
 return {"baskets":n,"frequency":n/1.5,"net":net,"pf":pf(rows),"expectancy":net/n if n else 0,
 "win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,"max_dd_pct":max(x["max_dd_pct"] for x in xs),
 "positive_windows":sum(x["net"]>0 for x in xs),"engineering_clean":all(x["engineering_clean"] for x in xs),
 "windows":{w:{k:xs_by_w[w][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct"]} for w in W}}
if not cand:
 result={"version":"HarmonyBot V71","decision":"HOLD_WITH_EVIDENCE","reason":"NO_CALIBRATION_CANDIDATE",
 "control_mode":"DIRECT_TRUSTED_V51_BINARY_REFERENCE","calibration":freeze,"validation_used":False,"fresh_used":False}
 (out/"V71_PERFORMANCE_FRONTIER.json").write_text(json.dumps(result,indent=2)); (out/"promotion.txt").write_text("false"); print(json.dumps(result,indent=2)); raise SystemExit(0)
REF={w:json.load(open(find(f"V51_REFERENCE-{w}.json"))) for w in W}
C={w:json.load(open(find(f"{cand}-{w}.json"))) for w in W}
A=agg(REF); Z=agg(C)
def sig(rows): return {(r["setup"],r["pattern"],r["route"]) for r in rows}
core_preserved=True
for w in W:
 if REF[w].get("data_snapshot_sha256")!=C[w].get("data_snapshot_sha256"): core_preserved=False
 if sig(REF[w]["core_basket_outcomes"])!=sig(C[w]["core_basket_outcomes"]): core_preserved=False
delta={"net":Z["net"]-A["net"],"pf":Z["pf"]-A["pf"],"expectancy":Z["expectancy"]-A["expectancy"],
 "positive_delta_windows":sum(Z["windows"][w]["net"]>A["windows"][w]["net"] for w in W)}
gate=Z["engineering_clean"] and core_preserved and Z["positive_windows"]==3 and Z["frequency"]>=60 and Z["net"]>V51["net"] and Z["pf"]>V51["pf"] and Z["expectancy"]>V51["expectancy"] and Z["win_rate"]>=V51["win_rate"] and Z["max_dd_pct"]<=V51["max_dd_pct"] and delta["net"]>0 and delta["pf"]>=0 and delta["expectancy"]>=0 and delta["positive_delta_windows"]==3
result={"version":"HarmonyBot V71","candidate":cand,"control_mode":"DIRECT_TRUSTED_V51_BINARY_REFERENCE","control":A,"candidate_dev":Z,
 "core_displacement_zero":core_preserved,"delta":delta,"v51_floor":V51,
 "decision":"BREAKTHROUGH_PASS_V72_ELIGIBLE" if gate else "HOLD_WITH_EVIDENCE","validation_used":False,"fresh_used":False}
(out/"V71_PERFORMANCE_FRONTIER.json").write_text(json.dumps(result,indent=2)); (out/"promotion.txt").write_text("true" if gate else "false"); print(json.dumps(result,indent=2))
