#!/usr/bin/env python3
import json,pathlib,sys,collections
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["V51_CHAMPION_CONTROL","V57_FAMILY_REP_CONTROL","V57_CALIBRATED_L0","V57_CALIBRATED_LEGACY_GRID"]
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
 sh=[r for x in xs for r in x.get("v57_shadow_outcomes",[])]
 pipes={}; books=collections.defaultdict(lambda:{"candidates":0,"shadow_started":0,"shadow_closed":0})
 for x in xs:
  for p,row in x.get("pattern_pipeline",{}).items():
   q=pipes.setdefault(p,{k:0 for k in row})
   for k,v in row.items(): q[k]+=v
  for p,row in x.get("v57_family_books",{}).items():
   for k,v in row.items(): books[p][k]+=v
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len({r["setup"] for r in rows}),"net":sum(vals),"pf":pf(vals),"expectancy":sum(vals)/n if n else 0,
 "win_rate":sum(x>0 for x in vals)/n if n else 0,"gross_profit":sum(x for x in vals if x>0),"gross_loss":abs(sum(x for x in vals if x<0)),
 "max_dd_pct":max(x["max_dd_pct"] for x in xs),"all_windows_positive":all(x["net"]>0 for x in xs),"engineering_clean":all(x["engineering_clean"] for x in xs),
 "risk_clean":all(x.get("actual_basket_risk_violations",0)==0 and x.get("margin_risk_violations",0)==0 for x in xs),
 "windows":{w:rd(f,w) for w in "ABC"},"rows":rows,"shadow_rows":sh,"pipeline":pipes,"family_books":dict(books)}
A={f:agg(f) for f in F}
data_snapshot_valid=True; snapshot={}
for w in "ABC":
 shas={A[f]["windows"][w].get("data_snapshot_sha","") for f in F}; shas.discard(""); snapshot[w]=sorted(shas)
 if len(shas)!=1:data_snapshot_valid=False
def economics(rows,key="net"):
 g=collections.defaultdict(list)
 for r in rows:g[r.get("pattern","?")].append(r)
 out={}
 for p,rs in g.items():
  v=[r[key] for r in rs]
  out[p]={"trades":len(v),"net_or_r":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v),"win_rate":sum(x>0 for x in v)/len(v)}
 return out
def shadow_econ(rows):
 g=collections.defaultdict(list); cells=collections.defaultdict(list)
 for r in rows:
  g[r.get("pattern","?")].append(r)
  cells[(r.get("pattern","?"),r.get("route","?"),r.get("regime","?"))].append(r)
 fam={}
 for p,rs in g.items():
  v=[x["realized_r"] for x in rs]
  fam[p]={"shadows":len(v),"sum_r":sum(v),"pf_r":pf(v),"mean_r":sum(v)/len(v),"win_rate":sum(x>0 for x in v)/len(v),"mean_hold_minutes":sum(x["hold_minutes"] for x in rs)/len(rs)}
 cell={}
 for k,rs in cells.items():
  v=[x["realized_r"] for x in rs]; token="|".join(k)
  cell[token]={"n":len(v),"mean_r":sum(v)/len(v),"pf_r":pf(v),"mean_hold_minutes":sum(x["hold_minutes"] for x in rs)/len(rs)}
 return fam,cell
for f,z in A.items():
 z["pattern_economics"]=economics(z["rows"])
 z["shadow_family_economics"],z["shadow_cell_economics"]=shadow_econ(z["shadow_rows"])
 z["family_detected"]={p:r.get("detected",0) for p,r in z["pipeline"].items()}
 z["family_confirming"]={p:r.get("confirming",0) for p,r in z["pipeline"].items()}
 z["family_executed"]={p:r.get("executed",0) for p,r in z["pipeline"].items()}
 z["shadow_coverage_failures"]=[p for p,n in z["family_confirming"].items() if n>0 and z["family_books"].get(p,{}).get("shadow_started",0)==0]
def cohort(f):
 z=A[f]; c=A["V51_CHAMPION_CONTROL"]; cset={r["setup"] for r in c["rows"]}; zset={r["setup"] for r in z["rows"]}
 add=[r for r in z["rows"] if r["setup"] not in cset]; rem=[r for r in c["rows"] if r["setup"] not in zset]
 vv=[r["net"] for r in add]; gp=sum(x for x in vv if x>0); gl=abs(sum(x for x in vv if x<0))
 wins={}
 for w in "ABC":
  cs={r["setup"] for r in c["windows"][w].get("basket_outcomes",[])}
  rs=[r for r in z["windows"][w].get("basket_outcomes",[]) if r["setup"] not in cs]
  wins[w]={"trades":len(rs),"net":sum(r["net"] for r in rs),"pf":pf([r["net"] for r in rs])}
 return {"added_trades":len(add),"added_net":sum(vv),"added_pf":pf(vv),"added_expectancy":sum(vv)/len(vv) if vv else 0,"added_gp":gp,"added_gl":gl,
 "commercial_margin_pf2":gp-2*gl,"removed_control_trades":len(rem),"removed_control_net":sum(r["net"] for r in rem),"windows":wins,
 "pass":len(add)>0 and sum(vv)>0 and (sum(vv)/len(vv) if vv else 0)>0 and gp-2*gl>=0 and all(wins[w]["net"]>=0 for w in "ABC")}
coh={f:cohort(f) for f in ["V57_CALIBRATED_L0","V57_CALIBRATED_LEGACY_GRID"]}
def gate(z):
 return data_snapshot_valid and z["baskets"]>=COMM["baskets"] and z["frequency"]>=COMM["frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"] and not z["shadow_coverage_failures"]
def superiority(z):
 return z["frequency"]>HIST["frequency"] and z["net"]>HIST["net"] and z["pf"]>HIST["pf"] and z["expectancy"]>HIST["expectancy"] and z["win_rate"]>=HIST["win_rate"] and z["max_dd_pct"]<=HIST["max_dd_pct"] and z["all_windows_positive"]
def grid_delta(a,b):
 x=A[a];y=A[b]; wins={w:{"delta_net":x["windows"][w]["net"]-y["windows"][w]["net"]} for w in "ABC"}
 return {"delta_net":x["net"]-y["net"],"delta_pf":x["pf"]-y["pf"],"delta_expectancy":x["expectancy"]-y["expectancy"],"delta_dd":x["max_dd_pct"]-y["max_dd_pct"],
 "positive_delta_windows":sum(v["delta_net"]>0 for v in wins.values()),"windows":wins,
 "pass":x["net"]>y["net"] and x["pf"]>=y["pf"] and x["expectancy"]>=y["expectancy"] and sum(v["delta_net"]>0 for v in wins.values())>=2 and x["max_dd_pct"]<=COMM["max_dd_pct"] and x["engineering_clean"] and x["risk_clean"]}
grid=grid_delta("V57_CALIBRATED_LEGACY_GRID","V57_CALIBRATED_L0")
for f,z in A.items():
 z["commercial_gate"]=gate(z) if f.startswith("V57_CALIBRATED_") else False
 z["historical_superiority_gate"]=superiority(z) if f.startswith("V57_CALIBRATED_") else False
 z["abcd_live_trades"]=z["pattern_economics"].get("AB=CD",{}).get("trades",0)
 z.pop("rows",None);z.pop("shadow_rows",None)
eligible=[]
for f in ["V57_CALIBRATED_L0","V57_CALIBRATED_LEGACY_GRID"]:
 gridok=True if f.endswith("_L0") else grid["pass"]
 if A[f]["commercial_gate"] and A[f]["historical_superiority_gate"] and coh[f]["pass"] and A[f]["abcd_live_trades"]==0 and gridok:
  eligible.append(f)
winner=max(eligible,key=lambda f:(A[f]["net"],A[f]["pf"],A[f]["frequency"])) if eligible else None
front={"version":"HarmonyBot V57","architecture":"REGIME_CALIBRATED_UNIVERSAL_HARMONIC_FAMILY_PORTFOLIO","commercial_minimum":COMM,"historical_superiority_reference":HIST,
"data_snapshot_valid":data_snapshot_valid,"data_snapshot_by_window":snapshot,"variants":A,"calibrated_cohort_attribution":coh,"legacy_grid_vs_l0":grid,
"development_candidate":winner,"status":"DEV3_SUPERIORITY_PASS" if winner else "HOLD_WITH_EVIDENCE","fresh_used":False,"next_stage":"UNTOUCHED_2026_VALIDATION" if winner else "STOP_DEV3_HOLD"}
(out/"V57_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V57_FAMILY_SHADOW_ECONOMICS.json").write_text(json.dumps({f:{"family":A[f]["shadow_family_economics"],"cells":A[f]["shadow_cell_economics"],"books":A[f]["family_books"]} for f in F},indent=2))
(out/"candidate.txt").write_text(winner or "")
(out/"V57_FINAL_DEV3_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V57","decision":"DEV3_SUPERIORITY_PASS" if winner else "HOLD_WITH_EVIDENCE","fresh_used":False},indent=2))
print(json.dumps(front,indent=2))
