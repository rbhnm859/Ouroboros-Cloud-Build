#!/usr/bin/env python3
import json,pathlib,sys,math
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["V62_V51_EXACT_CONTROL","V62_DAG_SINGLE_ENTRY","V62_CURRENT_V61_GRID","V62_FRONT_LOADED_GRID","V62_CONDITIONAL_GRID","V62_CONDITIONAL_STRUCTURAL_EXIT","V62_CONDITIONAL_RUNNER","V62_PATTERN_NATIVE"]
H={"frequency":38.6666666667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
COMM={"max_baskets":90,"min_frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
def find(v,w):
 xs=list(root.rglob(f"{v}-{w}.json"))
 if not xs: raise SystemExit(f"missing {v}-{w}")
 return json.load(open(xs[0]))
def pf(vals):
 gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0)); return gp/gl if gl else (999 if gp else 0)
def pct(xs,p):
 if not xs:return 0
 y=sorted(xs); q=(len(y)-1)*p; lo=int(math.floor(q)); hi=int(math.ceil(q)); return y[lo] if lo==hi else y[lo]+(y[hi]-y[lo])*(q-lo)
def agg(v):
 ws={w:find(v,w) for w in "ABC"}; rows=[r for x in ws.values() for r in x.get("basket_outcomes",[])]; vals=[r["net"] for r in rows]; rs=[r.get("r",0) for r in rows]; win=[x for x in rs if x>0]; n=len(rows)
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len({r["setup"] for r in rows}),"net":sum(vals),"pf":pf(vals),"expectancy":sum(vals)/n if n else 0,"win_rate":sum(x>0 for x in vals)/n if n else 0,"max_dd_pct":max(x["max_dd_pct"] for x in ws.values()),"all_windows_positive":all(x["net"]>0 for x in ws.values()),"engineering_clean":all(x["engineering_clean"] for x in ws.values()),"risk_clean":all(x.get("actual_basket_risk_violations",0)==0 and x.get("margin_risk_violations",0)==0 for x in ws.values()),"p95_winner_r":pct(win,.95),"max_winner_r":max(win) if win else 0,"mean_mfe_r":sum(x.get("mfe",0) for x in rows)/n if n else 0,"capture_ratio":sum(x.get("r",0) for x in rows)/sum(max(0,x.get("mfe",0)) for x in rows) if sum(max(0,x.get("mfe",0)) for x in rows)>0 else 0,"windows":ws}
A={v:agg(v) for v in F}; control=A["V62_DAG_SINGLE_ENTRY"]
for v,z in A.items():
 z["right_tail_preservation_ratio"]=z["p95_winner_r"]/control["p95_winner_r"] if control["p95_winner_r"]>0 else 0
 z["right_tail_gate"]=v in ("V62_V51_EXACT_CONTROL","V62_DAG_SINGLE_ENTRY") or z["right_tail_preservation_ratio"]>=.80
 z["historical_superiority_gate"]=z["frequency"]>H["frequency"] and z["net"]>H["net"] and z["pf"]>H["pf"] and z["expectancy"]>H["expectancy"] and z["win_rate"]>=H["win_rate"] and z["max_dd_pct"]<=H["max_dd_pct"] and z["all_windows_positive"] and z["risk_clean"] and z["engineering_clean"]
 z["commercial_gate"]=z["baskets"]<=COMM["max_baskets"] and z["frequency"]>=COMM["min_frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["risk_clean"] and z["engineering_clean"]
eligible=[v for v in F[3:] if A[v]["right_tail_gate"] and A[v]["historical_superiority_gate"] and A[v]["commercial_gate"]]
winner=max(eligible,key=lambda v:(A[v]["net"],A[v]["pf"],A[v]["expectancy"])) if eligible else None
deltas={}
for v in F[2:]:
 z=A[v]; deltas[v]={"delta_net_vs_dag":z["net"]-control["net"],"delta_pf_vs_dag":z["pf"]-control["pf"],"delta_expectancy_vs_dag":z["expectancy"]-control["expectancy"],"delta_frequency_vs_dag":z["frequency"]-control["frequency"],"rtp":z["right_tail_preservation_ratio"]}
front={"version":"HarmonyBot V62","architecture":"ALPHA_PRESERVING_EXECUTION_CONVERSION","historical_reference":H,"commercial_minimum":COMM,"variants":A,"causal_deltas":deltas,"development_candidate":winner,"status":"DEV_CANDIDATE" if winner else "HOLD_WITH_EVIDENCE","next_stage":"VALIDATION_2026_Q1_Q2" if winner else "STOP_DEV_HOLD","fresh_used":False}
(out/"V62_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2)); (out/"candidate.txt").write_text(winner or ""); print(json.dumps(front,indent=2))