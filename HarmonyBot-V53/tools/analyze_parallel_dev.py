#!/usr/bin/env python3
import json,pathlib,sys,collections
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["V52_CONTROL_NOGRID","V52_CONTROL_GRID","V53_CONVERSION_NOGRID","V53_CONVERSION_GRID"]
COMM={"baskets":90,"frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
V52_GRID={"baskets":200,"frequency":133.3333333333,"net":2902.27,"pf":1.375,"expectancy":14.51,"win_rate":.435,"max_dd_pct":9.815}
def find(n):
 xs=list(root.rglob(n))
 if not xs: raise SystemExit("missing "+n)
 return xs[0]
def rd(f,w): return json.load(open(find(f"{f}-{w}.json")))
def pf(v):
 gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))
 return gp/gl if gl else (999 if gp else 0)
def agg(f):
 xs=[rd(f,w) for w in "ABC"]; rows=[r for x in xs for r in x.get("basket_outcomes",[])]; v=[r["net"] for r in rows]; n=len(rows)
 pipes={}; conv=collections.defaultdict(lambda:collections.Counter()); det=collections.defaultdict(lambda:collections.Counter())
 for x in xs:
  for p,st in x.get("conversion_truth",{}).items(): conv[p].update(st)
  for p,st in x.get("detector_truth",{}).items(): det[p].update(st)
  for p,row in x.get("pattern_pipeline",{}).items():
   q=pipes.setdefault(p,{k:0 for k in row})
   for k,z in row.items(): q[k]+=z
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len({r["setup"] for r in rows}),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/n if n else 0,"win_rate":sum(x>0 for x in v)/n if n else 0,"max_dd_pct":max(x["max_dd_pct"] for x in xs),"all_windows_positive":all(x["net"]>0 for x in xs),"engineering_clean":all(x["engineering_clean"] for x in xs),"risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),"windows":{w:rd(f,w) for w in "ABC"},"rows":rows,"pipeline":pipes,"conversion_truth":{p:dict(c) for p,c in conv.items()},"detector_truth":{p:dict(c) for p,c in det.items()}}
A={f:agg(f) for f in F}
def repro(z,b): return z["baskets"]==b["baskets"] and abs(z["net"]-b["net"])<=.30 and abs(z["pf"]-b["pf"])<=.006 and abs(z["max_dd_pct"]-b["max_dd_pct"])<=.15
controls_ok=repro(A["V52_CONTROL_GRID"],V52_GRID); A["V52_CONTROL_GRID"]["control_reproduction_pass"]=controls_ok
for f,z in A.items():
 g=collections.defaultdict(list)
 for r in z["rows"]: g[r.get("pattern","?")].append(r)
 z["pattern_economics"]={}
 for p,rows in g.items():
  v=[r["net"] for r in rows]
  z["pattern_economics"][p]={"trades":len(v),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v),"win_rate":sum(x>0 for x in v)/len(v),"mean_filled_legs":sum(r.get("filled_legs",1) for r in rows)/len(rows),"mean_entry_improve_pips":sum(r.get("entry_improve_pips",0) for r in rows)/len(rows)}
 z["family_detected"]={p:r.get("detected",0) for p,r in z["pipeline"].items()}; z["family_executed"]={p:r.get("executed",0) for p,r in z["pipeline"].items()}
 z["starved_families"]=[p for p,n in z["family_detected"].items() if n>0 and z["family_executed"].get(p,0)==0]
 z["mean_filled_legs"]=sum(r.get("filled_legs",1) for r in z["rows"])/len(z["rows"]) if z["rows"] else 0
 z["mean_entry_improve_pips"]=sum(r.get("entry_improve_pips",0) for r in z["rows"])/len(z["rows"]) if z["rows"] else 0
def gd(grid,nogrid):
 g,n=A[grid],A[nogrid]; wins={w:{"delta_net":g["windows"][w]["net"]-n["windows"][w]["net"],"grid_net":g["windows"][w]["net"],"nogrid_net":n["windows"][w]["net"]} for w in "ABC"}
 d={"grid_variant":grid,"nogrid_variant":nogrid,"delta_net":g["net"]-n["net"],"delta_pf":g["pf"]-n["pf"],"delta_expectancy":g["expectancy"]-n["expectancy"],"delta_win_rate":g["win_rate"]-n["win_rate"],"delta_max_dd_pct":g["max_dd_pct"]-n["max_dd_pct"],"net_multiplier":g["net"]/n["net"] if n["net"]>0 else None,"windows":wins,"positive_delta_windows":sum(1 for x in wins.values() if x["delta_net"]>0),"grid_engineering_clean":g["engineering_clean"],"grid_risk_clean":g["risk_clean"]}
 d["grid_alpha_amplifier_pass"]=d["delta_net"]>0 and g["pf"]>=n["pf"] and g["expectancy"]>=n["expectancy"] and d["positive_delta_windows"]>=2 and g["max_dd_pct"]<=COMM["max_dd_pct"] and g["engineering_clean"] and g["risk_clean"]; return d
grid_causal={"V52_CONTROL":gd("V52_CONTROL_GRID","V52_CONTROL_NOGRID"),"V53_CONVERSION":gd("V53_CONVERSION_GRID","V53_CONVERSION_NOGRID")}
def cd(v53,v52):
 a,b=A[v53],A[v52]; aset={r["setup"] for r in a["rows"]}; bset={r["setup"] for r in b["rows"]}; add=[r for r in a["rows"] if r["setup"] not in bset]; rem=[r for r in b["rows"] if r["setup"] not in aset]
 return {"delta_trades":a["baskets"]-b["baskets"],"delta_net":a["net"]-b["net"],"delta_pf":a["pf"]-b["pf"],"delta_expectancy":a["expectancy"]-b["expectancy"],"delta_win_rate":a["win_rate"]-b["win_rate"],"delta_dd":a["max_dd_pct"]-b["max_dd_pct"],"windows":{w:{"delta_net":a["windows"][w]["net"]-b["windows"][w]["net"]} for w in "ABC"},"added_cohort":{"trades":len(add),"net":sum(r["net"] for r in add),"pf":pf([r["net"] for r in add])},"removed_cohort":{"trades":len(rem),"net":sum(r["net"] for r in rem),"pf":pf([r["net"] for r in rem])}}
conversion={"NOGRID":cd("V53_CONVERSION_NOGRID","V52_CONTROL_NOGRID"),"GRID":cd("V53_CONVERSION_GRID","V52_CONTROL_GRID")}
for f,z in A.items():
 z["commercial_gate"]=controls_ok and f.startswith("V53_") and z["baskets"]>=COMM["baskets"] and z["frequency"]>=COMM["frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"]
 z.pop("rows",None)
eligible=[f for f in ["V53_CONVERSION_NOGRID","V53_CONVERSION_GRID"] if A[f]["commercial_gate"]]; winner=max(eligible,key=lambda f:(A[f]["net"],A[f]["pf"],A[f]["frequency"])) if eligible else None
front={"version":"HarmonyBot V53","architecture":"FAMILY_NATIVE_CONVERSION_AND_GRID_CAUSAL_ATTRIBUTION","v52_grid_control":V52_GRID,"commercial_minimum":COMM,"controls_reproduced":controls_ok,"families":A,"conversion_attribution":conversion,"grid_causal_attribution":grid_causal,"development_candidate":winner,"status":"COMMERCIAL_FREEZE_CANDIDATE_DEV_PASS" if winner else "HOLD_WITH_EVIDENCE","fresh_used":False,"next_stage":"CAPITAL_COMPATIBILITY" if winner else "STOP_DEV_HOLD"}
(out/"V53_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2)); (out/"V53_CONVERSION_TRUTH_LEDGER.json").write_text(json.dumps({f:A[f]["conversion_truth"] for f in F},indent=2)); (out/"V53_FAMILY_CONVERSION_ECONOMICS.json").write_text(json.dumps({f:{"pipeline":A[f]["pipeline"],"pattern_economics":A[f]["pattern_economics"],"starved_families":A[f]["starved_families"]} for f in F},indent=2)); (out/"V53_GRID_CAUSAL_ATTRIBUTION.json").write_text(json.dumps(grid_causal,indent=2)); (out/"candidate.txt").write_text(winner or ""); (out/"V53_FINAL_COMMERCIAL_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V53","decision":"COMMERCIAL_FREEZE_CANDIDATE_DEV_PASS" if winner else "HOLD_WITH_EVIDENCE","stage":"DEV","fresh_used":False},indent=2)); print(json.dumps(front,indent=2))
