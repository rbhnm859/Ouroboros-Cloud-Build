#!/usr/bin/env python3
import json,pathlib,sys,statistics
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["V46_SCALE_CONTROL","COUNTERFACTUAL_NATIVE_CONFIRM","PROVEN_PLUS_NATIVE_LANES","FULL_V49_COMMERCIAL"]
BASE={"baskets":39,"frequency":26.0,"net":1721.72,"pf":2.1833,"expectancy":44.15,"win_rate":.5128,"max_dd_pct":4.56}
V36={"baskets":77,"frequency":51.3333333333,"net":648.58,"pf":1.2124297856,"expectancy":8.4231,"win_rate":.42857,"max_dd_pct":8.7683}
COMM={"baskets":90,"frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
def find(n): return next(root.rglob(n))
def rd(f,w): return json.load(open(find(f"{f}-{w}.json")))
def pf(v):
 gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))
 return gp/gl if gl else (999.0 if gp else 0.0)
def econ(rows):
 v=[r["net"] for r in rows]; n=len(v)
 return {"trades":n,"net":sum(v),"pf":pf(v),"expectancy":sum(v)/n if n else 0.0,
         "win_rate":sum(x>0 for x in v)/n if n else 0.0}
def agg(f):
 xs=[rd(f,w) for w in "ABC"]; rows=[r for x in xs for r in x.get("basket_outcomes",[])]
 v=[r["net"] for r in rows]; setups={r["setup"] for r in rows}; n=len(rows)
 return {"baskets":n,"frequency":n/1.5,"unique_setups":len(setups),"duplicate_reentries":n-len(setups),
 "net":sum(v),"pf":pf(v),"expectancy":sum(v)/n if n else 0.0,"win_rate":sum(x>0 for x in v)/n if n else 0.0,
 "max_dd_pct":max((x["max_dd_pct"] for x in xs),default=0.0),
 "all_windows_positive":all(x["net"]>0 for x in xs),
 "engineering_clean":all(x["engineering_clean"] for x in xs),
 "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 and x["unprotected_survivors"]==0 for x in xs),
 "windows":{w:rd(f,w) for w in "ABC"},"rows":rows}
A={f:agg(f) for f in F}; c=A["V46_SCALE_CONTROL"]
c["baseline_reproduction_pass"]=(c["baskets"]==39 and c["unique_setups"]==39 and abs(c["net"]-BASE["net"])<=.10 and
 abs(c["pf"]-BASE["pf"])<=.002 and abs(c["expectancy"]-BASE["expectancy"])<=.02 and
 abs(c["win_rate"]-BASE["win_rate"])<=.001 and abs(c["max_dd_pct"]-BASE["max_dd_pct"])<=.02 and c["engineering_clean"] and c["risk_clean"])
base_sets={w:{r["setup"] for r in rd("V46_SCALE_CONTROL",w).get("basket_outcomes",[])} for w in "ABC"}
for f in F[1:]:
 by={}; rr=[]
 for w in "ABC":
  q=[r for r in rd(f,w).get("basket_outcomes",[]) if r["setup"] not in base_sets[w]]
  rr+=q; by[w]=econ(q)
 v=[r["net"] for r in rr]
 A[f]["marginal"]={"trades":len(rr),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v) if v else 0.0,
                    "win_rate":sum(x>0 for x in v)/len(v) if v else 0.0,"windows":by}
 A[f]["marginal"]["pass"]=len(rr)>0 and sum(v)>0 and all(by[w]["net"]>=0 for w in "ABC")
for f in F:
 z=A[f]
 z["v36_dominance"]=(z["baskets"]>77 and z["frequency"]>V36["frequency"] and z["net"]>V36["net"] and z["pf"]>V36["pf"] and
                      z["expectancy"]>V36["expectancy"] and z["win_rate"]>V36["win_rate"] and z["max_dd_pct"]<V36["max_dd_pct"] and
                      z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"])
 eligible=f in ("PROVEN_PLUS_NATIVE_LANES","FULL_V49_COMMERCIAL")
 z["commercial_gate"]=(eligible and c["baseline_reproduction_pass"] and z["baskets"]>=COMM["baskets"] and z["frequency"]>=COMM["frequency"] and
   z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and
   z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and
   z["unique_setups"]==z["baskets"] and z.get("marginal",{}).get("pass",False))
 rows=z.pop("rows")
 g={}
 for r in rows: g.setdefault(r.get("pattern","?"),[]).append(r)
 z["pattern_economics"]={p:econ(v) for p,v in g.items()}

# Pure counterfactual observation cohort: no Alpha mutation.
obs=[rd("COUNTERFACTUAL_NATIVE_CONFIRM",w) for w in "ABC"]
events=[e for x in obs for e in x.get("events",[])]
cf=[q for x in obs for q in x.get("counterfactual",[])]
bars=[q for x in obs for q in x.get("confirm_bars",[])]
# Keep one terminal record per independent setup.
cf_by={}
for q in cf:
 key=q.get("setup") or q.get("cid")
 prev=cf_by.get(key)
 if prev is None or q.get("bars",0)>=prev.get("bars",0): cf_by[key]=q
cf=list(cf_by.values())

meta={}
stage={}
for e in events:
 key=e.get("setup") or e.get("cid")
 meta[key]={"pattern":e.get("pattern"),"route":e.get("route"),"scale":e.get("scale"),"subtype":e.get("subtype")}
 st=stage.setdefault(key,set()); st.add(e.get("state")); st.add(e.get("reason",""))
def terminal_class(q): return q.get("classification","UNRESOLVED")
groups={}
keys=set(meta)|set(cf_by)
for key in keys:
 m=meta.get(key,{})
 q=cf_by.get(key)
 if q:
  gk=(q["pattern"],q["route"],q["scale"])
 else:
  gk=(m.get("pattern","?"),m.get("route","?"),m.get("scale",-1))
 g=groups.setdefault(gk,{"setups":set(),"detected":0,"qualified":0,"prz":0,"touched":0,"confirming":0,"evidence_seen":0,
   "counterfactual_positive":0,"counterfactual_negative":0,"counterfactual_ambiguous":0,"counterfactual_unresolved":0,
   "native_pass":0,"armed":0,"executed":0,"expired":0,"invalidated":0,"closed":0,"mfe":[],"mae":[],"shadow_r":[]})
 if key in g["setups"]: continue
 g["setups"].add(key)
 ss=stage.get(key,set())
 g["detected"]+=int("DETECTED" in ss)
 g["qualified"]+=int("VALIDATED" in ss)
 g["prz"]+=int("WAIT_PRZ" in ss)
 g["touched"]+=int("CONFIRMING" in ss)
 g["confirming"]+=int("CONFIRMING" in ss)
 g["armed"]+=int("ARMED" in ss)
 g["executed"]+=int("EXECUTED" in ss)
 g["expired"]+=int("EXPIRED" in ss)
 g["invalidated"]+=int("INVALIDATED" in ss)
 if q:
  seen=any(q.get(k,"-")!="-" for k in ["directional_utc","reclaim_utc","bos1_utc","bos2_utc","rejection_utc","failed_extension_utc","sweep_utc","displacement_utc"])
  g["evidence_seen"]+=int(seen); g["native_pass"]+=int(q.get("native_pass",False))
  cl=terminal_class(q)
  if cl=="POSITIVE_2R_BEFORE_SL": g["counterfactual_positive"]+=1; g["shadow_r"].append(2.0)
  elif cl=="NEGATIVE_SL_BEFORE_2R": g["counterfactual_negative"]+=1; g["shadow_r"].append(-1.0)
  elif cl=="AMBIGUOUS_SAME_BAR": g["counterfactual_ambiguous"]+=1
  else: g["counterfactual_unresolved"]+=1
  g["mfe"].append(q.get("mfe_r",0.0)); g["mae"].append(q.get("mae_r",0.0))

# Map actual closed outcomes in observation group back to scale via setup metadata.
obs_closed=[r for x in obs for r in x.get("basket_outcomes",[])]
for r in obs_closed:
 key=r.get("setup"); m=meta.get(key)
 if not m: continue
 gk=(m["pattern"],m["route"],m["scale"])
 if gk in groups: groups[gk]["closed"]+=1

funnel={}
for (p,rte,scale),g in sorted(groups.items(),key=lambda x:(x[0][0],x[0][1],x[0][2])):
 resolved=g["counterfactual_positive"]+g["counterfactual_negative"]; rv=g.pop("shadow_r")
 confirming=g["confirming"]; armed=g["armed"]
 funnel[f"{p}|{rte}|{scale}"]={
  "pattern":p,"route":rte,"pivot_scale":scale,"independent_setups":len(g.pop("setups")),
  **{k:v for k,v in g.items() if k not in ("mfe","mae")},
  "confirming_to_armed_rate":armed/confirming if confirming else 0.0,
  "armed_to_executed_rate":g["executed"]/armed if armed else 0.0,
  "shadow_resolved":resolved,
  "rejected_shadow_pf_r":pf(rv),"rejected_shadow_wr":g["counterfactual_positive"]/resolved if resolved else 0.0,
  "rejected_shadow_expectancy_r":sum(rv)/len(rv) if rv else 0.0,
  "shadow_mean_mfe_r":statistics.mean(g["mfe"]) if g["mfe"] else 0.0,
  "shadow_mean_mae_r":statistics.mean(g["mae"]) if g["mae"] else 0.0,
  "family_opportunity_loss_positive_setups":g["counterfactual_positive"],
  "trades_lost_per_year_proxy":g["counterfactual_positive"]/1.5
 }

family_cf={}
for q in cf:
 p=q["pattern"]; z=family_cf.setdefault(p,{"setups":0,"positive":0,"negative":0,"ambiguous":0,"unresolved":0,"native_pass":0,"mfe":[],"mae":[]})
 z["setups"]+=1; z["native_pass"]+=int(q.get("native_pass",False)); z["mfe"].append(q["mfe_r"]); z["mae"].append(q["mae_r"])
 cl=q["classification"]
 if cl=="POSITIVE_2R_BEFORE_SL": z["positive"]+=1
 elif cl=="NEGATIVE_SL_BEFORE_2R": z["negative"]+=1
 elif cl=="AMBIGUOUS_SAME_BAR": z["ambiguous"]+=1
 else: z["unresolved"]+=1
for p,z in family_cf.items():
 res=z["positive"]+z["negative"]; rv=[2.0]*z["positive"]+[-1.0]*z["negative"]
 z["resolved"]=res; z["shadow_pf_r"]=pf(rv); z["shadow_wr"]=z["positive"]/res if res else 0.0
 z["shadow_expectancy_r"]=sum(rv)/len(rv) if rv else 0.0
 z["mean_mfe_r"]=statistics.mean(z.pop("mfe")) if z["setups"] else 0.0
 z["mean_mae_r"]=statistics.mean(z.pop("mae")) if z["setups"] else 0.0
 z["positive_opportunity_per_year"]=z["positive"]/1.5

eligible=[f for f in ("PROVEN_PLUS_NATIVE_LANES","FULL_V49_COMMERCIAL") if A[f]["commercial_gate"]]
winner=max(eligible,key=lambda f:(A[f]["net"],A[f]["pf"],A[f]["frequency"])) if eligible else None
forensics={"version":"HarmonyBot V49","source":"COUNTERFACTUAL_NATIVE_CONFIRM pure observation","evidence_window_completed_m1":12,
 "classification_rule":"positive iff 2R completed-M1 timestamp strictly before SL; negative iff SL strictly before 2R; same-bar ambiguous",
 "family_summary":family_cf,"pattern_route_scale":funnel,
 "root_cause_evidence":{"v48_rigid_ordering_code_confirmed":True,"v48_native_window_bars":4,
 "v49_order_independent_window_bars":12,"counterfactual_records":len(cf),
 "non_incumbent_positive_setups":sum(z["positive"] for p,z in family_cf.items() if p not in ("AB=CD","Shark"))}}
front={"version":"HarmonyBot V49","architecture":"HARMONIC_FAMILY_CONFIRMATION_KERNEL","baseline":BASE,"v36":V36,
 "commercial_minimum":COMM,"baseline_reproduction_pass":c["baseline_reproduction_pass"],"families":A,
 "development_candidate":winner,"status":"COMMERCIAL_FREEZE_CANDIDATE_DEV_PASS" if winner else "HOLD_WITH_EVIDENCE","fresh_used":False}
(out/"V49_COUNTERFACTUAL_CONFIRMATION_FORENSICS.json").write_text(json.dumps(forensics,indent=2))
(out/"V49_PATTERN_ROUTE_SCALE_FUNNEL.json").write_text(json.dumps(funnel,indent=2))
(out/"V49_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"candidate.txt").write_text(winner or "")
(out/"V49_FINAL_COMMERCIAL_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V49",
 "decision":"COMMERCIAL_FREEZE_CANDIDATE_PASS" if winner else "HOLD_WITH_EVIDENCE","stage":"DEV","fresh_used":False},indent=2))
print(json.dumps(front,indent=2))
