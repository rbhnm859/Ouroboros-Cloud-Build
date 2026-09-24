#!/usr/bin/env python3
import json,pathlib,sys,math
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
F=["V62_V51_EXACT_CONTROL","V62_DAG_SINGLE_ENTRY","V62_CURRENT_V61_GRID","V62_FRONT_LOADED_GRID","V62_CONDITIONAL_GRID","V62_CONDITIONAL_STRUCTURAL_EXIT","V62_CONDITIONAL_RUNNER","V62_PATTERN_NATIVE"]
H={"frequency":38.6666666667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
COMM={"max_baskets":90,"min_frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0,"min_realized_rr":2.0}
def find(v,w):
 x=list(root.rglob(f"{v}-{w}.json"))
 if not x:raise SystemExit(f"missing {v}-{w}")
 return json.load(open(x[0]))
def pf(v):
 gp=sum(x for x in v if x>0);gl=abs(sum(x for x in v if x<0));return gp/gl if gl else (999 if gp else 0)
def pct(v,p):
 if not v:return 0
 y=sorted(v);pos=(len(y)-1)*p;lo=int(math.floor(pos));hi=int(math.ceil(pos));return y[lo] if lo==hi else y[lo]+(y[hi]-y[lo])*(pos-lo)
def agg(v):
 ws={w:find(v,w) for w in "ABC"};rows=[r for x in ws.values() for r in x.get("basket_outcomes",[])];vals=[r["net"] for r in rows];rr=[r.get("r",0) for r in rows];win=[x for x in rr if x>0];n=len(rows)
 cap=[x.get("mean_capture_ratio",0) for x in ws.values() if x.get("baskets",0)>0]
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len({r["setup"] for r in rows}),"net":sum(vals),"pf":pf(vals),"expectancy":sum(vals)/n if n else 0,"win_rate":sum(x>0 for x in vals)/n if n else 0,"max_dd_pct":max(x["max_dd_pct"] for x in ws.values()),"all_windows_positive":all(x["net"]>0 for x in ws.values()),"engineering_clean":all(x["engineering_clean"] for x in ws.values()),"risk_clean":all(x.get("actual_basket_risk_violations",0)==0 and x.get("margin_risk_violations",0)==0 for x in ws.values()),"p95_winner_r":pct(win,.95),"max_winner_r":max(win) if win else 0,"mean_winner_r":sum(win)/len(win) if win else 0,"mean_capture_ratio":sum(cap)/len(cap) if cap else 0,"windows":ws}
A={v:agg(v) for v in F}
def delta(x,y):
 a=A[x];b=A[y];wd={w:a["windows"][w]["net"]-b["windows"][w]["net"] for w in "ABC"}
 return {"candidate":x,"control":y,"delta_net":a["net"]-b["net"],"delta_pf":a["pf"]-b["pf"],"delta_expectancy":a["expectancy"]-b["expectancy"],"delta_dd":a["max_dd_pct"]-b["max_dd_pct"],"delta_frequency":a["frequency"]-b["frequency"],"delta_p95_winner_r":a["p95_winner_r"]-b["p95_winner_r"],"delta_max_winner_r":a["max_winner_r"]-b["max_winner_r"],"positive_delta_windows":sum(z>0 for z in wd.values()),"windows":wd}
P={"dag_vs_exact":delta(F[1],F[0]),"current_v61_grid_vs_dag":delta(F[2],F[1]),"front_loaded_vs_dag":delta(F[3],F[1]),"conditional_vs_dag":delta(F[4],F[1]),"structural_exit_vs_conditional":delta(F[5],F[4]),"runner_vs_conditional":delta(F[6],F[4]),"pattern_native_vs_runner":delta(F[7],F[6])}
base=A[F[1]]
for v,z in A.items():
 z["right_tail_preservation_ratio"]=z["p95_winner_r"]/base["p95_winner_r"] if base["p95_winner_r"]>0 else 0
 z["max_winner_preservation_ratio"]=z["max_winner_r"]/base["max_winner_r"] if base["max_winner_r"]>0 else 0
 z["realized_rr_proxy"]=z["mean_winner_r"]
def superior(z):return z["frequency"]>H["frequency"] and z["net"]>H["net"] and z["pf"]>H["pf"] and z["expectancy"]>H["expectancy"] and z["win_rate"]>=H["win_rate"] and z["max_dd_pct"]<=H["max_dd_pct"] and z["all_windows_positive"] and z["risk_clean"] and z["engineering_clean"] and z["unique_setups"]==z["baskets"]
def commercial(z):return z["baskets"]<=COMM["max_baskets"] and z["frequency"]>=COMM["min_frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["realized_rr_proxy"]>=COMM["min_realized_rr"] and z["all_windows_positive"] and z["risk_clean"] and z["engineering_clean"]
parent={F[3]:F[1],F[4]:F[1],F[5]:F[4],F[6]:F[4],F[7]:F[6]}
def alpha(v):
 z=A[v];p=A[parent[v]];freq_ok=z["frequency"]<=p["frequency"]+1e-9 or z["net"]>p["net"]
 return z["right_tail_preservation_ratio"]>=.80 and z["max_winner_preservation_ratio"]>=.80 and z["net"]>p["net"] and z["expectancy"]>=p["expectancy"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and freq_ok and z["risk_clean"] and z["engineering_clean"]
for v,z in A.items():z["historical_superiority_gate"]=superior(z);z["commercial_gate"]=commercial(z);z["alpha_preservation_gate"]=alpha(v) if v in parent else False
eligible=[v for v in F[3:] if A[v]["alpha_preservation_gate"] and superior(A[v]) and commercial(A[v])]
winner=max(eligible,key=lambda v:(A[v]["net"],A[v]["pf"],A[v]["expectancy"],A[v]["right_tail_preservation_ratio"])) if eligible else None
controls={r["setup"]:r for w in A[F[1]]["windows"].values() for r in w.get("basket_outcomes",[])};matched={}
for v in F[2:]:
 rows={r["setup"]:r for w in A[v]["windows"].values() for r in w.get("basket_outcomes",[])};k=sorted(set(controls)&set(rows));ds=[rows[x]["r"]-controls[x]["r"] for x in k]
 matched[v]={"n":len(k),"mean_delta_r":sum(ds)/len(ds) if ds else 0,"positive_delta_share":sum(x>0 for x in ds)/len(ds) if ds else 0}
funnel={}
for v,z in A.items():
 st={}
 for x in z["windows"].values():
  for stage,q in x.get("gate_telemetry",{}).items():
   r=st.setdefault(stage,{"pass":0,"reject":0});r["pass"]+=q.get("pass",0);r["reject"]+=q.get("reject",0)
 for q in st.values():
  n=q["pass"]+q["reject"];q["rate"]=q["pass"]/n if n else None;q["trades_lost_per_year"]=q["reject"]/1.5
 funnel[v]=st
front={"version":"HarmonyBot V62","historical_reference":H,"commercial_minimum":COMM,"right_tail_min_ratio":.80,"variants":A,"causal_attribution":P,"matched_setup_attribution":matched,"funnel":funnel,"development_candidate":winner,"status":"DEV_CANDIDATE" if winner else "HOLD_WITH_EVIDENCE","next_stage":"VALIDATION_2026_Q1_Q2" if winner else "STOP_DEV_HOLD","fresh_used":False}
(out/"V62_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2));(out/"candidate.txt").write_text(winner or "");print(json.dumps(front,indent=2))
