#!/usr/bin/env python3
import json,pathlib,sys,math
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
V=["V63_GOLDEN_V51_CONTROL","V63_V51_CONDITIONAL","V63_CELL_POLICY_ROUTER","V63_CELL_POLICY_RUNNER","V63_POSITIVE_COHORT_RECOVERY","V63_OCCUPANCY_GOVERNOR"]
H={"baskets":58,"frequency":38.6666666667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
COMM={"max_baskets":90,"min_frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
def find(v,w):
 xs=list(root.rglob(f"{v}-{w}.json"))
 if not xs: raise SystemExit(f"missing {v}-{w}")
 return json.load(open(xs[0]))
def pf(vals):
 gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0)); return gp/gl if gl else (999 if gp else 0)
def pct(xs,p):
 if not xs:return 0
 y=sorted(xs); q=(len(y)-1)*p; lo=int(q); hi=min(len(y)-1,lo+1); return y[lo]+(y[hi]-y[lo])*(q-lo)
def agg(v):
 ws={w:find(v,w) for w in "ABC"}; rows=[r for x in ws.values() for r in x.get("basket_outcomes",[])]; vals=[r["net"] for r in rows]; rs=[r.get("r",0) for r in rows]; win=[x for x in rs if x>0]; n=len(rows)
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len({r["setup"] for r in rows}),"net":sum(vals),"pf":pf(vals),"expectancy":sum(vals)/n if n else 0,"win_rate":sum(x>0 for x in vals)/n if n else 0,"max_dd_pct":max(x["max_dd_pct"] for x in ws.values()),"all_windows_positive":all(x["net"]>0 and x["pf"]>1 and x["expectancy"]>0 for x in ws.values()),"engineering_clean":all(x["engineering_clean"] for x in ws.values()),"risk_clean":all(x.get("actual_basket_risk_violations",0)==0 and x.get("margin_risk_violations",0)==0 for x in ws.values()),"p95_winner_r":pct(win,.95),"max_winner_r":max(win) if win else 0,"windows":{w:{k:ws[w].get(k) for k in ["baskets","net","pf","expectancy","win_rate","max_dd_pct"]} for w in "ABC"},"rows":rows}
A={v:agg(v) for v in V}; ctl=A[V[0]]
for v,z in A.items():
 z["rtp"]=z["p95_winner_r"]/ctl["p95_winner_r"] if ctl["p95_winner_r"] else 0
 z["right_tail_gate"]=v==V[0] or z["rtp"]>=.80
 z["historical_superiority_gate"]=z["frequency"]>H["frequency"] and z["net"]>H["net"] and z["pf"]>H["pf"] and z["expectancy"]>H["expectancy"] and z["win_rate"]>=H["win_rate"] and z["max_dd_pct"]<=H["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"]
 z["commercial_gate"]=z["baskets"]<=COMM["max_baskets"] and z["frequency"]>=COMM["min_frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"]
for i in range(1,len(V)):
 p=A[V[i-1]]; z=A[V[i]]
 z["marginal_vs_previous"]={"delta_trades":z["baskets"]-p["baskets"],"delta_net":z["net"]-p["net"],"delta_pf":z["pf"]-p["pf"],"delta_expectancy":z["expectancy"]-p["expectancy"]}
 z["frequency_expansion_gate"]=not (z["baskets"]>p["baskets"]) or z["net"]>p["net"]
# robustness: remove top five winners and require residual net positive for promotion
for v,z in A.items():
 vals=sorted([r["net"] for r in z["rows"]],reverse=True); z["net_without_top5"]=sum(vals[5:]) if len(vals)>5 else 0; z["concentration_gate"]=z["net_without_top5"]>0
eligible=[v for v in V[1:] if A[v]["right_tail_gate"] and A[v]["historical_superiority_gate"] and A[v]["commercial_gate"] and A[v].get("frequency_expansion_gate",True) and A[v]["concentration_gate"]]
winner=max(eligible,key=lambda v:(A[v]["net"],A[v]["pf"],A[v]["expectancy"])) if eligible else None
front={"version":"HarmonyBot V63","architecture":"REGIME_NATIVE_ALPHA_PORTFOLIO_ADAPTIVE_EXECUTION","historical_reference":H,"commercial_minimum":COMM,"governance_note":"60 trades/year and <=90 baskets/1.5y implies exactly 90 baskets/1.5y","variants":{v:{k:x for k,x in A[v].items() if k!="rows"} for v in V},"development_candidate":winner,"status":"DEV_CANDIDATE" if winner else "HOLD_WITH_EVIDENCE","next_stage":"VALIDATION_2026_Q1_Q2" if winner else "STOP_DEV_HOLD","fresh_used":False}
(out/"V63_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2)); (out/"candidate.txt").write_text(winner or ""); print(json.dumps(front,indent=2))