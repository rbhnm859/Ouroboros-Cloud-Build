#!/usr/bin/env python3
import json,pathlib,sys,collections
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["L0_ONLY","LEGACY_GRID","FAMILY_NATIVE_GRID","FAMILY_NATIVE_GRID_STATE_AWARE"]
COMM={"baskets":90,"frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
def find(n):
 xs=list(root.rglob(n))
 if not xs: raise SystemExit("missing "+n)
 return xs[0]
def rd(f,w): return json.load(open(find(f"grid-{f}-{w}.json")))
def pf(v):
 gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))
 return gp/gl if gl else (999.0 if gp else 0.0)
def summary(rows):
 v=[r["net"] for r in rows]; n=len(v)
 return {"trades":n,"net":sum(v),"pf":pf(v),"expectancy":sum(v)/n if n else 0.0,"win_rate":sum(x>0 for x in v)/n if n else 0.0}
def agg(f):
 xs=[rd(f,w) for w in "ABC"]; rows=[r for x in xs for r in x.get("basket_outcomes",[])]; v=[r["net"] for r in rows]; n=len(rows)
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len({r["setup"] for r in rows}),"net":sum(v),"pf":pf(v),
 "expectancy":sum(v)/n if n else 0.0,"win_rate":sum(x>0 for x in v)/n if n else 0.0,
 "max_dd_pct":max(x["max_dd_pct"] for x in xs),"all_windows_positive":all(x["net"]>0 for x in xs),
 "engineering_clean":all(x["engineering_clean"] for x in xs),
 "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
 "windows":{w:rd(f,w) for w in "ABC"},"rows":rows}
A={f:agg(f) for f in F}
data_snapshot_valid=True; data_snapshot_by_window={}
for w in "ABC":
 shas={A[f]["windows"][w].get("data_snapshot_sha","") for f in F}; shas.discard("")
 data_snapshot_by_window[w]=sorted(shas)
 if len(shas)!=1: data_snapshot_valid=False

for f,z in A.items():
 pats=collections.defaultdict(list); depths=collections.defaultdict(list); lanes=collections.defaultdict(list)
 for r in z["rows"]:
  pats[r.get("pattern","?")].append(r); depths[str(r.get("filled_legs",1))].append(r); lanes[r.get("alpha_lane","LEGACY")].append(r)
 z["pattern_economics"]={p:{**summary(rows),"mean_filled_legs":sum(r.get("filled_legs",1) for r in rows)/len(rows),"mean_entry_improve_pips":sum(r.get("entry_improve_pips",0) for r in rows)/len(rows)} for p,rows in pats.items()}
 z["filled_leg_attribution"]={d:summary(rows) for d,rows in depths.items()}
 z["lane_economics"]={p:summary(rows) for p,rows in lanes.items()}
 z["mean_filled_legs"]=sum(r.get("filled_legs",1) for r in z["rows"])/len(z["rows"]) if z["rows"] else 0
 z["mean_entry_improve_pips"]=sum(r.get("entry_improve_pips",0) for r in z["rows"])/len(z["rows"]) if z["rows"] else 0
 z["commercial_gate"]=z["baskets"]>=COMM["baskets"] and z["frequency"]>=COMM["frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"]

def delta(f,base):
 a=A[f]; b=A[base]; wins={}
 for w in "ABC":
  aw=a["windows"][w]; bw=b["windows"][w]
  wins[w]={"delta_net":aw["net"]-bw["net"],"variant_net":aw["net"],"base_net":bw["net"]}
 d={"variant":f,"base":base,"delta_net":a["net"]-b["net"],"delta_pf":a["pf"]-b["pf"],"delta_expectancy":a["expectancy"]-b["expectancy"],
 "delta_win_rate":a["win_rate"]-b["win_rate"],"delta_max_dd_pct":a["max_dd_pct"]-b["max_dd_pct"],
 "positive_delta_windows":sum(1 for x in wins.values() if x["delta_net"]>0),"windows":wins}
 d["causal_pass"]=a["net"]>b["net"] and a["pf"]>=b["pf"] and a["expectancy"]>=b["expectancy"] and d["positive_delta_windows"]>=2 and a["max_dd_pct"]<=COMM["max_dd_pct"] and a["engineering_clean"] and a["risk_clean"]
 return d

D={f:{"vs_l0":delta(f,"L0_ONLY"),"vs_legacy":delta(f,"LEGACY_GRID") if f!="LEGACY_GRID" else None} for f in ["LEGACY_GRID","FAMILY_NATIVE_GRID","FAMILY_NATIVE_GRID_STATE_AWARE"]}
eligible=[]
for f in ["LEGACY_GRID","FAMILY_NATIVE_GRID","FAMILY_NATIVE_GRID_STATE_AWARE"]:
 if A[f]["commercial_gate"] and D[f]["vs_l0"]["causal_pass"]:
  if f=="LEGACY_GRID" or D[f]["vs_legacy"]["delta_net"]>0:
   eligible.append(f)
candidate=max(eligible,key=lambda f:(A[f]["net"],A[f]["pf"],A[f]["expectancy"])) if eligible else None
for z in A.values(): z.pop("rows",None)
front={"version":"HarmonyBot V54","stage":"GRID_DEV","architecture":"FIBONACCI_GRID_ALPHA_CORE_CAUSAL_MATRIX","commercial_minimum":COMM,
"data_snapshot_valid":data_snapshot_valid,"data_snapshot_by_window":data_snapshot_by_window,"variants":A,"grid_causal":D,
"grid_candidate":candidate,"grid_alpha_core_pass":candidate is not None,"status":"GRID_DEV_PASS" if candidate else "HOLD_WITH_EVIDENCE","fresh_used":False}
(out/"V54_GRID_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V54_GRID_CAUSAL_ATTRIBUTION.json").write_text(json.dumps(D,indent=2))
(out/"grid_candidate.txt").write_text(candidate or "")
print(json.dumps(front,indent=2))
