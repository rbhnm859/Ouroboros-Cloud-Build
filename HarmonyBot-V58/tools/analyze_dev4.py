#!/usr/bin/env python3
import json,pathlib,sys,collections
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["V58_MANIFOLD_BASELINE_L0","V58_MANIFOLD_CAPTURE_L0","V58_MANIFOLD_CAPTURE_LEGACY_GRID"]
COMM={"baskets":90,"frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
HIST={"frequency":38.6666666667,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
def find(n):
 xs=list(root.rglob(n))
 if not xs: raise SystemExit("missing "+n)
 return xs[0]
def rd(f,w): return json.load(open(find(f"{f}-{w}.json")))
def pf(vals):
 gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
 return gp/gl if gl else (999 if gp else 0)
def agg(f):
 xs=[rd(f,w) for w in "ABC"]; rows=[r for x in xs for r in x.get("basket_outcomes",[])]; vals=[r["net"] for r in rows]; n=len(rows)
 shadows=[r for x in xs for r in x.get("v58_shadow_outcomes",[])]; caps=[r for x in xs for r in x.get("v58_capture_outcomes",[])]
 pipes={}; books=collections.defaultdict(lambda:{"candidates":0,"shadow_started":0,"shadow_closed":0})
 for x in xs:
  for p,row in x.get("pattern_pipeline",{}).items():
   q=pipes.setdefault(p,{k:0 for k in row})
   for k,v in row.items():q[k]+=v
  for p,row in x.get("v58_family_books",{}).items():
   for k,v in row.items():books[p][k]+=v
 pat=collections.defaultdict(list)
 for r in rows:pat[r.get("pattern","?")].append(r["net"])
 pe={p:{"trades":len(v),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v)} for p,v in pat.items()}
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len({r["setup"] for r in rows}),"net":sum(vals),"pf":pf(vals),"expectancy":sum(vals)/n if n else 0,
 "win_rate":sum(x>0 for x in vals)/n if n else 0,"gross_profit":sum(x for x in vals if x>0),"gross_loss":abs(sum(x for x in vals if x<0)),
 "max_dd_pct":max(x["max_dd_pct"] for x in xs),"all_windows_positive":all(x["net"]>0 for x in xs),"engineering_clean":all(x["engineering_clean"] for x in xs),
 "risk_clean":all(x.get("actual_basket_risk_violations",0)==0 and x.get("margin_risk_violations",0)==0 for x in xs),
 "windows":{w:rd(f,w) for w in "ABC"},"pattern_economics":pe,"pipeline":pipes,"family_books":dict(books),
 "shadow_count":len(shadows),"capture_count":len(caps),
 "shadow_coverage_failures":[p for p,row in pipes.items() if row.get("confirming",0)>0 and books[p]["shadow_started"]==0]}
A={f:agg(f) for f in F}
snap={}; snapok=True
for w in "ABC":
 shas={A[f]["windows"][w].get("data_snapshot_sha","") for f in F}; shas.discard("");snap[w]=sorted(shas)
 if len(shas)!=1:snapok=False
def gate(z):
 return snapok and z["baskets"]>=COMM["baskets"] and z["frequency"]>=COMM["frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"] and not z["shadow_coverage_failures"] and z["pattern_economics"].get("AB=CD",{}).get("trades",0)==0
def superior(z):
 return z["frequency"]>HIST["frequency"] and z["net"]>HIST["net"] and z["pf"]>HIST["pf"] and z["expectancy"]>HIST["expectancy"] and z["win_rate"]>=HIST["win_rate"] and z["max_dd_pct"]<=HIST["max_dd_pct"] and z["all_windows_positive"]
def delta(a,b):
 x=A[a]; y=A[b]; wins={w:{"delta_net":x["windows"][w]["net"]-y["windows"][w]["net"]} for w in "ABC"}
 return {"candidate":a,"control":b,"delta_net":x["net"]-y["net"],"delta_pf":x["pf"]-y["pf"],"delta_expectancy":x["expectancy"]-y["expectancy"],"delta_dd":x["max_dd_pct"]-y["max_dd_pct"],
 "positive_delta_windows":sum(v["delta_net"]>0 for v in wins.values()),"windows":wins,
 "pass":x["net"]>y["net"] and x["pf"]>=y["pf"] and x["expectancy"]>=y["expectancy"] and sum(v["delta_net"]>0 for v in wins.values())>=2 and x["risk_clean"] and x["engineering_clean"]}
capture=delta("V58_MANIFOLD_CAPTURE_L0","V58_MANIFOLD_BASELINE_L0")
grid=delta("V58_MANIFOLD_CAPTURE_LEGACY_GRID","V58_MANIFOLD_CAPTURE_L0")
for f,z in A.items():
 z["commercial_gate"]=gate(z)
 z["historical_superiority_gate"]=superior(z)
eligible=[]
if gate(A["V58_MANIFOLD_CAPTURE_L0"]) and superior(A["V58_MANIFOLD_CAPTURE_L0"]) and capture["pass"]:
 eligible.append("V58_MANIFOLD_CAPTURE_L0")
if gate(A["V58_MANIFOLD_CAPTURE_LEGACY_GRID"]) and superior(A["V58_MANIFOLD_CAPTURE_LEGACY_GRID"]) and capture["pass"] and grid["pass"]:
 eligible.append("V58_MANIFOLD_CAPTURE_LEGACY_GRID")
winner=max(eligible,key=lambda f:(A[f]["net"],A[f]["pf"],A[f]["frequency"])) if eligible else None
front={"version":"HarmonyBot V58","architecture":"CANONICAL_HARMONIC_MANIFOLD_EXCURSION_CAPTURE","commercial_minimum":COMM,"historical_superiority_reference":HIST,
"data_snapshot_valid":snapok,"data_snapshot_by_window":snap,"variants":A,"capture_causal_attribution":capture,"legacy_grid_causal_attribution":grid,
"development_candidate":winner,"status":"DEV4_SUPERIORITY_PASS" if winner else "HOLD_WITH_EVIDENCE","fresh_used":False,
"next_stage":"UNTOUCHED_2026_VALIDATION" if winner else "STOP_DEV4_HOLD"}
(out/"V58_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V58_CAPTURE_CAUSAL_ATTRIBUTION.json").write_text(json.dumps(capture,indent=2))
(out/"V58_GRID_CAUSAL_ATTRIBUTION.json").write_text(json.dumps(grid,indent=2))
(out/"candidate.txt").write_text(winner or "")
(out/"V58_FINAL_DEV4_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V58","decision":"DEV4_SUPERIORITY_PASS" if winner else "HOLD_WITH_EVIDENCE","fresh_used":False},indent=2))
print(json.dumps(front,indent=2))
