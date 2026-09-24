#!/usr/bin/env python3
import json,pathlib,sys,math
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["V61_V51_EXACT_CONTROL","V61_CHAMPION_FIB_GRID","V61_GRID_REGIME_SURVIVAL","V61_COMMERCIAL_MAX"]; H={"frequency":38.6666666667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}; COMM={"max_baskets":90,"min_frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
def find(v,w):
 xs=list(root.rglob(f"{v}-{w}.json"))
 if not xs: raise SystemExit(f"missing {v}-{w}")
 return json.load(open(xs[0]))
def pf(vals):
 gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0)); return gp/gl if gl else (999 if gp else 0)
def pct(xs,p):
 if not xs:return 0
 y=sorted(xs); pos=(len(y)-1)*p; lo=int(math.floor(pos)); hi=int(math.ceil(pos)); return y[lo] if lo==hi else y[lo]+(y[hi]-y[lo])*(pos-lo)
def agg(v):
 ws={w:find(v,w) for w in "ABC"}; rows=[r for x in ws.values() for r in x.get("basket_outcomes",[])]; vals=[r["net"] for r in rows]; rs=[r.get("r",0) for r in rows]; winners=[x for x in rs if x>0]; n=len(rows)
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len({r["setup"] for r in rows}),"net":sum(vals),"pf":pf(vals),"expectancy":sum(vals)/n if n else 0,"win_rate":sum(x>0 for x in vals)/n if n else 0,"max_dd_pct":max(x["max_dd_pct"] for x in ws.values()),"all_windows_positive":all(x["net"]>0 for x in ws.values()),"engineering_clean":all(x["engineering_clean"] for x in ws.values()),"risk_clean":all(x.get("actual_basket_risk_violations",0)==0 and x.get("margin_risk_violations",0)==0 for x in ws.values()),"p95_winner_r":pct(winners,.95),"max_winner_r":max(winners) if winners else 0,"windows":ws}
A={v:agg(v) for v in F}
def delta(x,y):
 a=A[x]; b=A[y]; wd={w:a["windows"][w]["net"]-b["windows"][w]["net"] for w in "ABC"}
 return {"candidate":x,"control":y,"delta_net":a["net"]-b["net"],"delta_pf":a["pf"]-b["pf"],"delta_expectancy":a["expectancy"]-b["expectancy"],"delta_dd":a["max_dd_pct"]-b["max_dd_pct"],"delta_frequency":a["frequency"]-b["frequency"],"delta_p95_winner_r":a["p95_winner_r"]-b["p95_winner_r"],"delta_max_winner_r":a["max_winner_r"]-b["max_winner_r"],"positive_delta_windows":sum(z>0 for z in wd.values()),"windows":wd,"right_tail_preserved":a["p95_winner_r"]>0 and a["max_winner_r"]>=b["max_winner_r"]}
D_BA=delta("V61_CHAMPION_FIB_GRID","V61_V51_EXACT_CONTROL"); D_CB=delta("V61_GRID_REGIME_SURVIVAL","V61_CHAMPION_FIB_GRID"); D_DC=delta("V61_COMMERCIAL_MAX","V61_GRID_REGIME_SURVIVAL")
grid_pass=D_BA["delta_net"]>0 and D_BA["delta_pf"]>=0 and D_BA["delta_expectancy"]>=0 and D_BA["positive_delta_windows"]>=2 and D_BA["right_tail_preserved"] and A["V61_CHAMPION_FIB_GRID"]["max_dd_pct"]<=COMM["max_dd_pct"] and A["V61_CHAMPION_FIB_GRID"]["risk_clean"] and A["V61_CHAMPION_FIB_GRID"]["engineering_clean"]
def superior(z): return z["frequency"]>H["frequency"] and z["net"]>H["net"] and z["pf"]>H["pf"] and z["expectancy"]>H["expectancy"] and z["win_rate"]>=H["win_rate"] and z["max_dd_pct"]<=H["max_dd_pct"] and z["all_windows_positive"] and z["risk_clean"] and z["engineering_clean"] and z["unique_setups"]==z["baskets"]
def commercial(z): return z["baskets"]<=COMM["max_baskets"] and z["frequency"]>=COMM["min_frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["risk_clean"] and z["engineering_clean"]
for v,z in A.items(): z["historical_superiority_gate"]=superior(z); z["commercial_gate"]=commercial(z)
eligible=[v for v in F[1:] if grid_pass and superior(A[v]) and commercial(A[v])]; winner=max(eligible,key=lambda v:(A[v]["net"],A[v]["pf"],A[v]["expectancy"])) if eligible else None
def stage(passv,rej,years=1.5): return {"pass":passv,"reject":rej,"rate":passv/(passv+rej) if passv+rej else None,"trades_lost_per_year":rej/years if years else None}
funnel={}
for v,z in A.items():
 pipes={}
 for x in z["windows"].values():
  for fam,row in x.get("pattern_pipeline",{}).items():
   q=pipes.setdefault(fam,{k:0 for k in row})
   for k,val in row.items():q[k]+=val
 raw=sum(x.get("detected",0) for x in pipes.values()); qual=sum(x.get("validated",0) for x in pipes.values()); routed=sum(x.get("routed",0) for x in pipes.values()); exe=sum(x.get("executed",0) for x in pipes.values())
 funnel[v]={"Raw Harmonic Signals":stage(raw,0),"Pattern Qualification":stage(qual,max(0,raw-qual)),"PRZ":{"status":"unavailable"},"Direction Gate":{"status":"unavailable"},"HTF Conflict":{"status":"unavailable"},"ATR":{"status":"unavailable"},"Regime":stage(routed,max(0,qual-routed)),"Session":{"status":"unavailable"},"Spread":{"status":"unavailable"},"Cooldown":{"status":"unavailable"},"Pending Logic":{"status":"unavailable"},"Risk":{"status":"unavailable"},"MinVolume":{"status":"unavailable"},"Margin":{"status":"unavailable"},"Executed Basket":stage(exe,max(0,routed-exe))}
front={"version":"HarmonyBot V61","historical_reference":H,"commercial_minimum":COMM,"variants":A,"grid_causal_attribution":D_BA,"regime_causal_attribution":D_CB,"commercial_max_causal_attribution":D_DC,"grid_promotion_pass":grid_pass,"development_candidate":winner,"status":"DEV_CANDIDATE" if winner else "HOLD_WITH_EVIDENCE","next_stage":"VALIDATION_2026_Q1_Q2" if winner else "STOP_DEV_HOLD","fresh_used":False,"funnel":funnel}; (out/"V61_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2)); (out/"candidate.txt").write_text(winner or ""); print(json.dumps(front,indent=2))
