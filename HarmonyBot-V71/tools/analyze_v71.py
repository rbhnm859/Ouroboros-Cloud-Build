#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
freeze=json.load(open(next(root.rglob("V71_CALIBRATION_FREEZE.json"))))
cand=freeze.get("candidate")
V51=freeze["v51_floor"]
def find(n):
 xs=list(root.rglob(n))
 if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {n}: {len(xs)}")
 return xs[0]
def pf(rows):
 gp=sum(r["net"] for r in rows if r["net"]>0); gl=-sum(r["net"] for r in rows if r["net"]<0)
 return gp/gl if gl else (999 if gp else 0)
def agg(v):
 W=["H2024H2","H2025H1","H2025H2"]; xs=[json.load(open(find(f"{v}-{w}.json"))) for w in W]
 rows=[r for x in xs for r in x["basket_outcomes"]]; n=len(rows); net=sum(r["net"] for r in rows)
 return {"baskets":n,"frequency":n/1.5,"net":net,"pf":pf(rows),"expectancy":net/n if n else 0,
 "win_rate":sum(r["net"]>0 for r in rows)/n if n else 0,"max_dd_pct":max(x["max_dd_pct"] for x in xs),
 "positive_windows":sum(x["net"]>0 for x in xs),"engineering_clean":all(x["engineering_clean"] for x in xs),
 "core_signatures":{w:{(r["setup"],r["pattern"],r["route"]) for r in xs[i]["core_basket_outcomes"]} for i,w in enumerate(W)},
 "windows":{w:{k:xs[i][k] for k in ["baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct"]} for i,w in enumerate(W)}}
if not cand:
 result={"version":"HarmonyBot V71","decision":"HOLD_WITH_EVIDENCE","reason":"NO_CALIBRATION_CANDIDATE",
 "calibration":freeze,"validation_used":False,"fresh_used":False}
 (out/"V71_PERFORMANCE_FRONTIER.json").write_text(json.dumps(result,indent=2)); (out/"promotion.txt").write_text("false"); print(json.dumps(result,indent=2)); raise SystemExit(0)
A=agg("A_V51_PROTECTED_CORE"); C=agg(cand)
core_preserved=all(C["core_signatures"][w]==A["core_signatures"][w] for w in A["core_signatures"])
for z in (A,C): z.pop("core_signatures",None)
delta={"net":C["net"]-A["net"],"pf":C["pf"]-A["pf"],"expectancy":C["expectancy"]-A["expectancy"],
 "positive_delta_windows":sum(C["windows"][w]["net"]>A["windows"][w]["net"] for w in A["windows"])}
gate=C["engineering_clean"] and core_preserved and C["positive_windows"]==3 and C["frequency"]>V51["frequency"] and C["net"]>V51["net"] and C["pf"]>V51["pf"] and C["expectancy"]>V51["expectancy"] and C["win_rate"]>=V51["win_rate"] and C["max_dd_pct"]<=V51["max_dd_pct"] and delta["net"]>0 and delta["pf"]>=0 and delta["expectancy"]>=0 and delta["positive_delta_windows"]>=2
result={"version":"HarmonyBot V71","candidate":cand,"control":A,"candidate_dev":C,"core_displacement_zero":core_preserved,"delta":delta,
 "v51_floor":V51,"decision":"BREAKTHROUGH_PASS_V72_ELIGIBLE" if gate else "HOLD_WITH_EVIDENCE",
 "validation_used":False,"fresh_used":False}
(out/"V71_PERFORMANCE_FRONTIER.json").write_text(json.dumps(result,indent=2))
(out/"promotion.txt").write_text("true" if gate else "false")
print(json.dumps(result,indent=2))
