#!/usr/bin/env python3
import json,pathlib,sys,collections,math
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
V=["V51_CHAMPION_CONTROL","V55_CORE_PARITY","V55_CORE_PLUS_EXPANSION","V55_FULL_GRID_V4"]
COMM={"baskets":90,"frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
def find(n):
 xs=list(root.rglob(n))
 if not xs: raise SystemExit("missing "+n)
 return xs[0]
def rd(v,w): return json.load(open(find(f"{v}-{w}.json")))
def calc(rows):
 vals=[r["net"] for r in rows];gp=sum(x for x in vals if x>0);gl=abs(sum(x for x in vals if x<0));n=len(vals)
 return {"trades":n,"net":sum(vals),"gp":gp,"gl":gl,"pf":gp/gl if gl else (999 if gp else 0),"expectancy":sum(vals)/n if n else 0,"win_rate":sum(x>0 for x in vals)/n if n else 0}
def agg(v):
 xs={w:rd(v,w) for w in "ABC"};rows=[r for w in "ABC" for r in xs[w].get("basket_outcomes",[])]
 z=calc(rows);z.update({"baskets":z.pop("trades"),"frequency":len(rows)/1.5,"unique_setups":len({r["setup"] for r in rows}),
 "max_dd_pct":max(xs[w]["max_dd_pct"] for w in "ABC"),"all_windows_positive":all(xs[w]["net"]>0 for w in "ABC"),
 "engineering_clean":all(xs[w]["engineering_clean"] for w in "ABC"),"risk_clean":all(xs[w]["actual_basket_risk_violations"]==0 and xs[w]["margin_risk_violations"]==0 for w in "ABC"),
 "windows":xs,"rows":rows})
 z["core_rows"]=[r for r in rows if r.get("lane")=="CHAMPION_CORE"];z["expansion_rows"]=[r for r in rows if r.get("lane")=="EVIDENCE_EXPANSION"]
 z["core"]=calc(z["core_rows"]);z["expansion"]=calc(z["expansion_rows"])
 z["research"]={k:sum(xs[w].get(k,0) for w in "ABC") for k in ["research_detected","research_prz_touched","research_confirmed","research_economic_evaluated","research_terminal","expansion_admitted","expansion_rejected","expansion_deferred_for_core","core_signals_during_expansion_slot"]}
 det=collections.defaultdict(lambda:collections.Counter())
 for w in "ABC":
  for p,st in xs[w].get("research_detector_truth",{}).items():det[p].update(st)
 z["research_detector_truth"]={p:dict(c) for p,c in det.items()}
 return z
A={v:agg(v) for v in V}
data_snapshot_by_window={};data_snapshot_valid=True
for w in "ABC":
 shas={A[v]["windows"][w].get("data_snapshot_sha","") for v in V};shas.discard("")
 data_snapshot_by_window[w]=sorted(shas)
 if len(shas)!=1:data_snapshot_valid=False

def setupmap(z,lane=None):
 rows=z["rows"] if lane is None else [r for r in z["rows"] if r.get("lane")==lane]
 return {(r["setup"],r["pattern"],r["direction"]) for r in rows}
control=A["V51_CHAMPION_CONTROL"]; parity=A["V55_CORE_PARITY"]
core_parity_gate=(setupmap(control,"CHAMPION_CORE")==setupmap(parity,"CHAMPION_CORE") and
                  abs(control["core"]["net"]-parity["core"]["net"])<=.01 and control["core"]["trades"]==parity["core"]["trades"])
for name in ["V55_CORE_PLUS_EXPANSION","V55_FULL_GRID_V4"]:
 z=A[name];z["core_preservation_gate"]=(setupmap(z,"CHAMPION_CORE")==setupmap(parity,"CHAMPION_CORE") and
                                      abs(z["core"]["net"]-parity["core"]["net"])<=.01 and
                                      z["research"]["core_signals_during_expansion_slot"]==0)
 exp=z["expansion"];win={}
 for w in "ABC":
  rr=[r for r in z["windows"][w].get("basket_outcomes",[]) if r.get("lane")=="EVIDENCE_EXPANSION"]
  win[w]=calc(rr)
 z["expansion_windows"]=win
 z["commercial_margin_2x"]=exp["gp"]-2.0*exp["gl"]
 z["commercial_margin_25x"]=exp["gp"]-2.5*exp["gl"]
 z["expansion_admission_gate"]=(exp["trades"]>0 and exp["net"]>0 and exp["expectancy"]>0 and z["commercial_margin_2x"]>=0 and all(win[w]["net"]>=0 for w in "ABC"))
 z["commercial_gate"]=(data_snapshot_valid and core_parity_gate and z["core_preservation_gate"] and z["expansion_admission_gate"] and
  z["baskets"]>=COMM["baskets"] and z["frequency"]>=COMM["frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and
  z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and
  z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"])
# Grid V4 is evidence-governed: it must not damage the same admitted alpha kernel.
g=A["V55_FULL_GRID_V4"];l=A["V55_CORE_PLUS_EXPANSION"]
grid_v4={"delta_net":g["net"]-l["net"],"delta_pf":g["pf"]-l["pf"],"delta_expectancy":g["expectancy"]-l["expectancy"],"delta_dd":g["max_dd_pct"]-l["max_dd_pct"],
 "safe_parity":setupmap(g)==setupmap(l) and abs(g["net"]-l["net"])<=.01 and abs(g["pf"]-l["pf"])<=.001}
eligible=[n for n in ["V55_CORE_PLUS_EXPANSION","V55_FULL_GRID_V4"] if A[n].get("commercial_gate")]
winner=max(eligible,key=lambda n:(A[n]["net"],A[n]["pf"])) if eligible else None
front={"version":"HarmonyBot V55","architecture":"CHAMPION_CORE_REBASE_UNIVERSAL_EVIDENCE_ADMISSION","commercial_minimum":COMM,
 "data_snapshot_valid":data_snapshot_valid,"data_snapshot_by_window":data_snapshot_by_window,"core_parity_gate":core_parity_gate,
 "variants":{}, "grid_v4_attribution":grid_v4,"development_candidate":winner,"fresh_used":False,
 "status":"COMMERCIAL_DEV2_PASS" if winner else "HOLD_WITH_EVIDENCE","next_stage":"VALIDATION" if winner else "STOP_DEV2_HOLD"}
for n,z in A.items():
 zz={k:v for k,v in z.items() if k not in ("rows","core_rows","expansion_rows")}
 front["variants"][n]=zz
(out/"V55_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V55_FINAL_DEV2_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V55","decision":front["status"],"candidate":winner,"fresh_used":False},indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps(front,indent=2))
