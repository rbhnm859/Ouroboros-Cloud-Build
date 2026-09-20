#!/usr/bin/env python3
import json,pathlib,sys,collections
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["V51_QUALITY_CORE_REPLAY","V52_LIBERATION_CONTROL","V54_CORE_PLUS_LIBERATION","V54_FULL_ALPHA"]
COMM={"baskets":90,"frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
HIST_V51={"baskets":58,"frequency":38.6666666667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
HIST_V52={"baskets":179,"frequency":119.3333333333,"net":2967.34,"pf":1.429,"expectancy":16.58,"win_rate":.4469,"max_dd_pct":9.815}
def find(n):
 xs=list(root.rglob(n))
 if not xs: raise SystemExit("missing "+n)
 return xs[0]
def rd(f,w): return json.load(open(find(f"alpha-{f}-{w}.json")))
def pf(v):
 gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))
 return gp/gl if gl else (999.0 if gp else 0.0)
def summary(rows):
 v=[r["net"] for r in rows]; n=len(v)
 return {"trades":n,"net":sum(v),"pf":pf(v),"expectancy":sum(v)/n if n else 0.0,"win_rate":sum(x>0 for x in v)/n if n else 0.0}
def agg(f):
 xs=[rd(f,w) for w in "ABC"]; rows=[r for x in xs for r in x.get("basket_outcomes",[])]; v=[r["net"] for r in rows]; n=len(rows)
 pipes={}; conv=collections.defaultdict(collections.Counter); det=collections.defaultdict(collections.Counter)
 for x in xs:
  for p,st in x.get("conversion_truth",{}).items(): conv[p].update(st)
  for p,st in x.get("detector_truth",{}).items(): det[p].update(st)
  for p,row in x.get("pattern_pipeline",{}).items():
   q=pipes.setdefault(p,{k:0 for k in row})
   for k,z in row.items(): q[k]+=z
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len({r["setup"] for r in rows}),"net":sum(v),"pf":pf(v),
 "expectancy":sum(v)/n if n else 0.0,"win_rate":sum(x>0 for x in v)/n if n else 0.0,
 "max_dd_pct":max(x["max_dd_pct"] for x in xs),"all_windows_positive":all(x["net"]>0 for x in xs),
 "engineering_clean":all(x["engineering_clean"] for x in xs),
 "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
 "windows":{w:rd(f,w) for w in "ABC"},"rows":rows,"pipeline":pipes,
 "conversion_truth":{p:dict(c) for p,c in conv.items()},"detector_truth":{p:dict(c) for p,c in det.items()}}
A={f:agg(f) for f in F}

data_snapshot_by_window={}; data_snapshot_valid=True
for w in "ABC":
 shas={A[f]["windows"][w].get("data_snapshot_sha","") for f in F}; shas.discard("")
 data_snapshot_by_window[w]=sorted(shas)
 if len(shas)!=1: data_snapshot_valid=False

def hist_repro(z,h):
 return abs(z["baskets"]-h["baskets"])<=3 and abs(z["net"]-h["net"])<=250 and abs(z["pf"]-h["pf"])<=.20 and abs(z["max_dd_pct"]-h["max_dd_pct"])<=1.0
hist_v51_reproduced=hist_repro(A["V51_QUALITY_CORE_REPLAY"],HIST_V51)
hist_v52_reproduced=hist_repro(A["V52_LIBERATION_CONTROL"],HIST_V52)

core_rows=A["V51_QUALITY_CORE_REPLAY"]["rows"]; core_set={r["setup"] for r in core_rows}
core_window_sets={w:{r["setup"] for r in A["V51_QUALITY_CORE_REPLAY"]["windows"][w].get("basket_outcomes",[])} for w in "ABC"}
def preservation(f):
 z=A[f]; retained=[r for r in z["rows"] if r["setup"] in core_set]; m=summary(retained); base=summary(core_rows)
 rate=len({r["setup"] for r in retained})/max(1,len(core_set))
 net_floor=.90*base["net"] if base["net"]>0 else base["net"]
 pf_floor=.90*base["pf"] if base["pf"]>0 else 0
 return {"retention_rate":rate,"retained":m,"control":base,
         "pass":rate>=.90 and m["net"]>=net_floor and m["pf"]>=pf_floor}

def expansion(f):
 z=A[f]; added=[r for r in z["rows"] if r["setup"] not in core_set]; m=summary(added); wins={}
 for w in "ABC":
  rows=[r for r in z["windows"][w].get("basket_outcomes",[]) if r["setup"] not in core_window_sets[w]]
  wins[w]=summary(rows)
 ok=m["trades"]>0 and m["net"]>0 and m["expectancy"]>0 and m["pf"]>=1.25 and all(wins[w]["net"]>=0 for w in "ABC")
 return {"aggregate":m,"windows":wins,"pass":ok}

def liberation(f):
 z=A[f]; fam={}
 for p,row in z["pipeline"].items():
  detected=row.get("detected",0); c=z["conversion_truth"].get(p,{})
  lib=c.get("LIBERATION_IDENTITY_PASS",0); qpass=c.get("QUALIFICATION_PASS",0)
  fam[p]={"detected":detected,"liberation_pass":lib,"qualification_pass":qpass,"ok":detected==0 or lib>0 or qpass>0}
 return {"families":fam,"pass":all(x["ok"] for x in fam.values())}

for f,z in A.items():
 g=collections.defaultdict(list); lanes=collections.defaultdict(list)
 for r in z["rows"]:
  g[r.get("pattern","?")].append(r); lanes[r.get("alpha_lane","LEGACY")].append(r)
 z["pattern_economics"]={p:summary(rows) for p,rows in g.items()}
 z["lane_economics"]={p:summary(rows) for p,rows in lanes.items()}
 z["family_detected"]={p:r.get("detected",0) for p,r in z["pipeline"].items()}
 z["family_executed"]={p:r.get("executed",0) for p,r in z["pipeline"].items()}
 z["starved_families"]=[p for p,n in z["family_detected"].items() if n>0 and z["family_executed"].get(p,0)==0]
 z["commercial_gate"]=z["baskets"]>=COMM["baskets"] and z["frequency"]>=COMM["frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"]

P={f:preservation(f) for f in ["V54_CORE_PLUS_LIBERATION","V54_FULL_ALPHA"]}
E={f:expansion(f) for f in ["V54_CORE_PLUS_LIBERATION","V54_FULL_ALPHA"]}
L={f:liberation(f) for f in ["V54_CORE_PLUS_LIBERATION","V54_FULL_ALPHA"]}
full="V54_FULL_ALPHA"
candidate=full if data_snapshot_valid and A[full]["commercial_gate"] and P[full]["pass"] and E[full]["pass"] and L[full]["pass"] else None

for z in A.values(): z.pop("rows",None)
front={"version":"HarmonyBot V54","stage":"ALPHA_DEV","architecture":"UNIVERSAL_HARMONIC_LIBERATION_PLUS_CORE_PRESERVATION",
"commercial_minimum":COMM,"historical_v51":HIST_V51,"historical_v52":HIST_V52,"historical_v51_reproduced":hist_v51_reproduced,
"historical_v52_reproduced":hist_v52_reproduced,"data_snapshot_valid":data_snapshot_valid,"data_snapshot_by_window":data_snapshot_by_window,
"families":A,"core_preservation":P,"expansion_marginal":E,"liberation_gate":L,"alpha_candidate":candidate,
"status":"ALPHA_DEV_PASS" if candidate else "HOLD_WITH_EVIDENCE","fresh_used":False}
(out/"V54_ALPHA_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V54_CORE_PRESERVATION.json").write_text(json.dumps(P,indent=2))
(out/"V54_EXPANSION_MARGINAL.json").write_text(json.dumps(E,indent=2))
(out/"V54_HARMONIC_LIBERATION.json").write_text(json.dumps(L,indent=2))
(out/"alpha_candidate.txt").write_text(candidate or "")
print(json.dumps(front,indent=2))
