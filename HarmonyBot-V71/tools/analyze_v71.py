#!/usr/bin/env python3
import json,pathlib,sys,math
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
freeze=json.load(open(next(root.rglob("V71_CALIBRATION_FREEZE.json")))); cand=freeze.get("candidate"); V51=freeze["v51_floor"]
W=["H2024H2","H2025H1","H2025H2"]
TARGET={"annual_return_pct":150.0,"annual_net_multiple":1.50,"pf":3.0,"max_dd_pct":10.0,
        "win_rate":.68,"independent_trades_per_year":200,"average_realized_rr":2.2,"profitable_months_per_year":11}
WINDOW_YEARS=.5
def window_target(x,years=WINDOW_YEARS):
 target_return=((1.0+TARGET["annual_net_multiple"])**years-1.0)*100.0
 required_trades=math.ceil(TARGET["independent_trades_per_year"]*years)
 required_months=math.ceil((TARGET["profitable_months_per_year"]/12.0)*(12.0*years)-1e-12)
 return {"required_return_pct":target_return,"required_net":float(x.get("starting_balance",10000))*target_return/100.0,
         "required_trades":required_trades,"required_profitable_months":required_months,
         "pass":bool(float(x.get("return_pct",0))>=target_return and
                     float(x.get("net",0))>=float(x.get("starting_balance",10000))*target_return/100.0 and
                     float(x.get("pf",0))>=TARGET["pf"] and float(x.get("max_dd_pct",999))<=TARGET["max_dd_pct"] and
                     float(x.get("win_rate",0))>=TARGET["win_rate"] and int(x.get("baskets",0))>=required_trades and
                     bool(x.get("log_basket_telemetry_complete",False)) and
                     float(x.get("average_realized_rr",0))>=TARGET["average_realized_rr"] and
                     int(x.get("positive_months",0))>=required_months)}
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
 result={"version":"HarmonyBot V71","decision":"V71_TERMINAL_REJECT_NO_V72","reason":freeze.get("decision","NO_CALIBRATION_CANDIDATE"),
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
commercial_windows={w:window_target(C[w]) for w in W}
commercial_target_pass=all(z["pass"] for z in commercial_windows.values())
delta={"net":Z["net"]-A["net"],"pf":Z["pf"]-A["pf"],"expectancy":Z["expectancy"]-A["expectancy"],
 "positive_delta_windows":sum(Z["windows"][w]["net"]>A["windows"][w]["net"] for w in W)}
breakthrough={"net_50pct":Z["net"]>=1.50*V51["net"],
 "pf_15pct":Z["pf"]>=1.15*V51["pf"],
 "expectancy_25pct":Z["expectancy"]>=1.25*V51["expectancy"],
 "frequency_50pct":Z["frequency"]>=1.50*V51["frequency"],
 "win_rate_plus_7p5pp":Z["win_rate"]>=V51["win_rate"]+.075,
 "dd_minus_20pct":Z["max_dd_pct"]<=.80*V51["max_dd_pct"]}
breakthrough_pass=bool(breakthrough["net_50pct"] and sum(bool(v) for k,v in breakthrough.items() if k!="net_50pct")>=1)
gate=Z["engineering_clean"] and core_preserved and commercial_target_pass and Z["positive_windows"]==3 and Z["net"]>V51["net"] and Z["pf"]>=TARGET["pf"] and Z["win_rate"]>=TARGET["win_rate"] and Z["max_dd_pct"]<=TARGET["max_dd_pct"] and delta["net"]>0 and delta["pf"]>=0 and delta["expectancy"]>=0 and delta["positive_delta_windows"]==3
result={"version":"HarmonyBot V71","candidate":cand,"control_mode":"DIRECT_TRUSTED_V51_BINARY_REFERENCE","control":A,"candidate_dev":Z,
 "core_displacement_zero":core_preserved,"delta":delta,"v51_floor":V51,"commercial_hard_targets":TARGET,
 "commercial_window_targets":commercial_windows,"commercial_target_pass":commercial_target_pass,
 "material_breakthrough":breakthrough,"material_breakthrough_pass":breakthrough_pass,
 "decision":"BREAKTHROUGH_PASS_V72_ELIGIBLE" if gate else "V71_TERMINAL_DEV_REJECT_NO_V72","validation_used":False,"fresh_used":False}
(out/"V71_PERFORMANCE_FRONTIER.json").write_text(json.dumps(result,indent=2)); (out/"promotion.txt").write_text("true" if gate else "false"); print(json.dumps(result,indent=2))
