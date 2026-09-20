#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V43/merged")
out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "HarmonyBot-V43/final")
out.mkdir(parents=True,exist_ok=True)

fams=["V42_REPLAY","DISCOVERY_ONLY","EXECUTION_RECOVERY","FULL_V43"]
control="V42_REPLAY"
windows="ABC"
supported=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]

def locate(name):
 xs=list(root.rglob(name))
 if not xs: raise SystemExit("missing "+name)
 return xs[0]

def read(f,w):
 return json.load(open(locate(f"{f}-{w}.json")))

def pf(vals):
 gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
 return gp/gl if gl else (999 if gp else 0)

def agg(f):
 xs=[read(f,w) for w in windows]
 gp=sum(x["gross_profit"] for x in xs); gl=sum(x["gross_loss"] for x in xs)
 n=sum(x["baskets"] for x in xs); net=sum(x["net"] for x in xs); wins=sum(x["wins"] for x in xs)
 grid_reasons={}
 discovery={p:{"attempts":0,"raw_matches":0,"selected":0} for p in supported}
 scales={}
 for x in xs:
  for k,v in x.get("grid_failure_reasons",{}).items(): grid_reasons[k]=grid_reasons.get(k,0)+v
  for p,row in x.get("pattern_discovery",{}).items():
   z=discovery.setdefault(p,{"attempts":0,"raw_matches":0,"selected":0})
   for k in z: z[k]+=row.get(k,0)
  for k,v in x.get("pattern_discovery_scales",{}).items(): scales[k]=scales.get(k,0)+v
 return {
  "baskets":n,"executable_baskets_per_year":n/1.5,
  "pf":gp/gl if gl else (999 if gp else 0),"net":net,"expectancy":net/n if n else 0,
  "win_rate":wins/n if n else 0,"positive_windows":sum(x["net"]>0 for x in xs),
  "all_windows_non_negative":all(x["net"]>=0 for x in xs),
  "all_windows_have_trades":all(x["baskets"]>0 for x in xs),
  "max_dd_pct":max(x["max_dd_pct"] for x in xs),
  "engineering_clean":all(x["engineering_clean"] for x in xs),
  "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
  "grid_plan_attempts":sum(x.get("grid_plan_attempts",0) for x in xs),
  "grid_plan_passes":sum(x.get("grid_plan_passes",0) for x in xs),
  "grid_plan_fails":sum(x.get("grid_plan_fails",0) for x in xs),
  "grid_failure_reasons":grid_reasons,
  "legacy_span_bypasses":sum(x.get("legacy_span_bypasses",0) for x in xs),
  "prz_synchronous_starts":sum(x.get("prz_synchronous_starts",0) for x in xs),
  "core_admissions":sum(x.get("core_admissions",0) for x in xs),
  "rescue_admissions":sum(x.get("rescue_admissions",0) for x in xs),
  "pattern_discovery":discovery,"pattern_discovery_scales":scales,
  "windows":{w:read(f,w) for w in windows}
 }

def keymap(f,w):
 return {x["key"]:x for x in read(f,w).get("attribution_outcomes",[]) if x.get("key")}

def marginal(f):
 all_added=[]; by_window={}; by_pattern={}
 for w in windows:
  base=keymap(control,w); cand=keymap(f,w)
  added=[x for k,x in cand.items() if k not in base]
  vals=[x["net"] for x in added]
  by_window[w]={"added_trades":len(added),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,
                "pf":pf(vals),"keys":[x["key"] for x in added]}
  all_added.extend([(w,x) for x in added])
  for x in added:
   p=x.get("pattern","UNKNOWN"); by_pattern.setdefault(p,[]).append((w,x))
 vals=[x["net"] for _,x in all_added]
 pattern_rows={}
 for p,rows in by_pattern.items():
  pv=[x["net"] for _,x in rows]
  wr={}
  for w in windows:
   z=[x["net"] for ww,x in rows if ww==w]
   wr[w]={"trades":len(z),"net":sum(z),"pf":pf(z),"expectancy":sum(z)/len(z) if z else 0}
  pattern_rows[p]={"added_trades":len(rows),"net":sum(pv),"expectancy":sum(pv)/len(pv) if pv else 0,"pf":pf(pv),
                   "window_non_negative":all(wr[w]["trades"]==0 or wr[w]["net"]>=0 for w in windows),"windows":wr}
  pattern_rows[p]["pass"]=(pattern_rows[p]["net"]>0 and pattern_rows[p]["expectancy"]>0 and
                           pattern_rows[p]["pf"]>=1.15 and pattern_rows[p]["window_non_negative"])
 result={"added_trades":len(all_added),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf(vals),
         "all_window_marginal_net_non_negative":all(by_window[w]["net"]>=0 for w in windows),
         "windows":by_window,"pattern_cohorts":pattern_rows}
 result["frequency_admission_pass"]=(result["added_trades"]>0 and result["net"]>0 and result["expectancy"]>0 and
                                     result["pf"]>=1.15 and result["all_window_marginal_net_non_negative"])
 result["pattern_marginal_gate_pass"]=(result["added_trades"]>0 and bool(pattern_rows) and
                                       all(r["pass"] for r in pattern_rows.values()))
 return result

def aggregate_pipeline(f):
 aggpipe={}
 for w in windows:
  for p,row in read(f,w).get("pattern_pipeline",{}).items():
   z=aggpipe.setdefault(p,{k:0 for k in row})
   for k,v in row.items(): z[k]+=v
 return aggpipe

A={f:agg(f) for f in fams}
pipelines={f:aggregate_pipeline(f) for f in fams}
base_exec={p for p in supported if pipelines[control].get(p,{}).get("executed",0)>0}

for f in fams:
 m=marginal(f) if f!=control else {"added_trades":0,"net":0,"expectancy":0,"pf":0,
   "all_window_marginal_net_non_negative":True,"frequency_admission_pass":False,
   "pattern_marginal_gate_pass":False,"pattern_cohorts":{},"windows":{w:{"added_trades":0,"net":0,"pf":0,"expectancy":0} for w in windows}}
 A[f]["marginal_vs_v42_replay"]=m
 A[f]["frequency_admission_pass"]=m["frequency_admission_pass"] if f!=control else False
 A[f]["pattern_marginal_gate_pass"]=m["pattern_marginal_gate_pass"] if f!=control else False
 pipe=pipelines[f]
 detected=[p for p in supported if pipe.get(p,{}).get("detected",0)>0]
 armed=[p for p in supported if pipe.get(p,{}).get("armed",0)>0]
 executed=[p for p in supported if pipe.get(p,{}).get("executed",0)>0]
 A[f]["detected_patterns"]=detected
 A[f]["armed_patterns"]=armed
 A[f]["executed_patterns"]=executed
 A[f]["detected_pattern_count"]=len(detected)
 A[f]["executed_pattern_count"]=len(executed)
 A[f]["new_executed_patterns"]=sorted(set(executed)-base_exec)
 A[f]["pattern_contract_coverage"]=12
 A[f]["alpha_promotion_pass"]=(f!=control and A[f]["engineering_clean"] and A[f]["risk_clean"] and
  A[f]["all_windows_have_trades"] and A[f]["all_windows_non_negative"] and A[f]["net"]>0 and A[f]["pf"]>=1.25 and
  A[f]["expectancy"]>0 and A[f]["max_dd_pct"]<=10 and A[f]["executable_baskets_per_year"]>=50 and
  A[f]["frequency_admission_pass"] and A[f]["pattern_marginal_gate_pass"])
 A[f]["v36_dominance_pass"]=(A[f]["executable_baskets_per_year"]>51.33 and A[f]["net"]>648.58 and
  A[f]["expectancy"]>8.42 and A[f]["pf"]>1.2124 and A[f]["max_dd_pct"]<=8.77 and A[f]["all_windows_non_negative"])
 A[f]["release_candidate_pass"]=A[f]["alpha_promotion_pass"] and A[f]["v36_dominance_pass"]

# DEV-only leave-one-window-out diagnostic. Never used to retune this run.
def vol_bucket(x):
 a=x.get("atr_ratio",0); return "LOW" if a<.75 else ("HIGH" if a>1.35 else "NORMAL")
def eff_bucket(x):
 e=x.get("efficiency",0); return "LOW" if e<.16 else ("HIGH" if e>=.28 else "MID")
def gkey(x): return (x.get("pattern",""),x.get("route",""),vol_bucket(x),eff_bucket(x),x.get("lane",""))
cv={}
for f in fams[1:]:
 folds={}
 for hold in windows:
  train=[x for w in windows if w!=hold for x in read(f,w).get("attribution_outcomes",[])]
  test=read(f,hold).get("attribution_outcomes",[])
  groups={}
  for x in train: groups.setdefault(gkey(x),[]).append(x)
  admitted=set()
  for k,xs in groups.items():
   vals=[x["net"] for x in xs]
   if len(xs)>=3 and sum(vals)>0 and pf(vals)>=1.15: admitted.add(k)
  selected=[x for x in test if gkey(x) in admitted]
  vals=[x["net"] for x in selected]
  folds[hold]={"positive_train_groups":len(admitted),"heldout_trades":len(selected),"heldout_net":sum(vals),
               "heldout_expectancy":sum(vals)/len(vals) if vals else 0,"heldout_pf":pf(vals),
               "heldout_non_negative":sum(vals)>=0}
 cv[f]={"folds":folds,"all_heldout_non_negative":all(folds[w]["heldout_non_negative"] for w in windows),
        "all_heldout_have_trades":all(folds[w]["heldout_trades"]>0 for w in windows)}

coverage={}
for f in fams:
 coverage[f]={"supported_patterns":supported,
  "contract_coverage":12,
  "raw_match_patterns":[p for p in supported if A[f]["pattern_discovery"].get(p,{}).get("raw_matches",0)>0],
  "selected_patterns":[p for p in supported if A[f]["pattern_discovery"].get(p,{}).get("selected",0)>0],
  "detected_patterns":A[f]["detected_patterns"],
  "armed_patterns":A[f]["armed_patterns"],
  "executed_patterns":A[f]["executed_patterns"],
  "executed_pattern_count":A[f]["executed_pattern_count"],
  "full_observed_execution_target_met":A[f]["executed_pattern_count"]==12}

eligible=[(A[f]["net"],A[f]["pf"],A[f]["executable_baskets_per_year"],f) for f in fams if A[f]["release_candidate_pass"]]
eligible.sort(reverse=True)
winner=eligible[0][-1] if eligible else None

(out/"V43_PATTERN_FUNNEL.json").write_text(json.dumps({"version":"HarmonyBot V43","families":pipelines},indent=2))
(out/"V43_PATTERN_EXECUTION_COVERAGE.json").write_text(json.dumps({"version":"HarmonyBot V43",
 "rule":"12/12 executable contracts are mandatory; observed execution is never fabricated; added pattern cohorts must be profitable.",
 "families":coverage},indent=2))
(out/"V43_CROSS_VALIDATION_DIAGNOSTIC.json").write_text(json.dumps({"version":"HarmonyBot V43",
 "scope":"DEV-only research evidence; not a current-run tuning input",
 "method":"leave-one-window-out Pattern x Route x Volatility x Efficiency x Lane","results":cv},indent=2))

frontier={"version":"HarmonyBot V43","architecture":"MULTISCALE_HARMONIC_DISCOVERY_POSITIVE_ALPHA_EXECUTION",
 "evidence_scope":"DEV-A/B/C only; Fresh untouched",
 "frequency_gate":"added trades >0; marginal Net/Expectancy >0; PF>=1.15; A/B/C marginal Net>=0",
 "pattern_marginal_gate":"every added pattern cohort Net/Expectancy>0, PF>=1.15 and non-negative in every window where it trades",
 "alpha_gate":"A/B/C Net>=0; aggregate Net>0; PF>=1.25; Expectancy>0; DD<=10%; >=50/year; engineering/risk clean",
 "v36_dominance_gate":{"baskets_per_year_gt":51.33,"net_gt":648.58,"expectancy_gt":8.42,"pf_gt":1.2124,"max_dd_pct_lte":8.77},
 "families":A,"development_candidate":winner,"status":"DEV_CANDIDATE" if winner else "NO_PROMOTABLE_CANDIDATE"}
(out/"V43_PERFORMANCE_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
decision={"version":"HarmonyBot V43","development_candidate":winner,"status":frontier["status"],
 "fresh_validation_used":False,"next_stage":"CAPITAL_COMPATIBILITY" if winner else "DISCOVERY_EXECUTION_ATTRIBUTION",
 "negative_net_frequency_expansion":"PROHIBITED"}
(out/"V43_PROMOTION_DECISION.json").write_text(json.dumps(decision,indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps(frontier,indent=2))
print("CANDIDATE="+(winner or ""))
