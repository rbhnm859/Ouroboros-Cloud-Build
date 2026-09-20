#!/usr/bin/env python3
import json,pathlib,statistics,sys,math
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V42/merged")
out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "HarmonyBot-V42/final")
out.mkdir(parents=True,exist_ok=True)
fams=["LEGACY_REPLAY","V41_FULL_REPLAY","OPPORTUNITY_GRID","FULL_V42"]

def locate(name):
 xs=list(root.rglob(name))
 if not xs: raise SystemExit(f"missing {name}")
 return xs[0]
def read(f,w): return json.load(open(locate(f"{f}-{w}.json")))
def pf_of(vals):
 gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
 return gp/gl if gl else (999 if gp else 0)
def agg(f):
 xs=[read(f,w) for w in "ABC"]
 gp=sum(x["gross_profit"] for x in xs); gl=sum(x["gross_loss"] for x in xs)
 n=sum(x["baskets"] for x in xs); net=sum(x["net"] for x in xs); wins=sum(x["wins"] for x in xs)
 return {"baskets":n,"executable_baskets_per_year":n/1.5,"pf":gp/gl if gl else (999 if gp else 0),
 "net":net,"expectancy":net/n if n else 0,"win_rate":wins/n if n else 0,
 "positive_windows":sum(x["net"]>0 for x in xs),"all_windows_non_negative":all(x["net"]>=0 for x in xs),
 "all_windows_have_trades":all(x["baskets"]>0 for x in xs),"worst_window_pf":min(x["pf"] for x in xs),
 "max_dd_pct":max(x["max_dd_pct"] for x in xs),"engineering_clean":all(x["engineering_clean"] for x in xs),
 "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
 "core_admissions":sum(x.get("core_admissions",0) for x in xs),
 "rescue_evaluated":sum(x.get("rescue_evaluated",0) for x in xs),
 "rescue_admissions":sum(x.get("rescue_admissions",0) for x in xs),
 "rescue_rejected":sum(x.get("rescue_rejected",0) for x in xs),
 "thesis_failure_exits":sum(x.get("thesis_failure_exits",0) for x in xs),
 "grid_plan_attempts":sum(x.get("grid_plan_attempts",0) for x in xs),
 "grid_plan_passes":sum(x.get("grid_plan_passes",0) for x in xs),
 "grid_plan_fails":sum(x.get("grid_plan_fails",0) for x in xs),
 "slot_blocked_candidates":sum(x.get("slot_blocked_candidates",0) for x in xs),
 "slot_recovered_executions":sum(x.get("slot_recovered_executions",0) for x in xs),
 "logical_four_leg_plans":sum(x.get("logical_four_leg_plans",0) for x in xs),
 "pattern_pipeline":{w:read(f,w).get("pattern_pipeline",{}) for w in "ABC"},
 "windows":{w:read(f,w) for w in "ABC"}}

A={f:agg(f) for f in fams}
control="LEGACY_REPLAY"

def keymap(f,w):
 return {x["key"]:x for x in read(f,w).get("attribution_outcomes",[]) if x.get("key")}

def marginal(f):
 total_added=[]
 by_window={}
 for w in "ABC":
  base=keymap(control,w); cand=keymap(f,w)
  added=[x for k,x in cand.items() if k not in base]
  vals=[x["net"] for x in added]
  row={"added_trades":len(added),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,
       "pf":pf_of(vals),"wins":sum(v>0 for v in vals),"losses":sum(v<0 for v in vals),
       "keys":[x["key"] for x in added]}
  by_window[w]=row; total_added.extend(added)
 vals=[x["net"] for x in total_added]
 res={"added_trades":len(total_added),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,
      "pf":pf_of(vals),"wins":sum(v>0 for v in vals),"losses":sum(v<0 for v in vals),
      "all_window_marginal_net_non_negative":all(by_window[w]["net"]>=0 for w in "ABC"),
      "windows":by_window}
 res["frequency_admission_pass"]=(res["added_trades"]>0 and res["net"]>0 and res["expectancy"]>0 and
                                  res["pf"]>=1.15 and res["all_window_marginal_net_non_negative"])
 return res

for f in fams:
 A[f]["marginal_vs_legacy"]=marginal(f) if f!=control else {"added_trades":0,"net":0,"expectancy":0,"pf":0,
  "all_window_marginal_net_non_negative":True,"frequency_admission_pass":False,"windows":{w:{"added_trades":0,"net":0,"expectancy":0,"pf":0} for w in "ABC"}}
 m=A[f]["marginal_vs_legacy"]
 A[f]["frequency_admission_pass"]=(f==control and A[f]["executable_baskets_per_year"]>=50) or m["frequency_admission_pass"]
 A[f]["alpha_promotion_pass"]=(A[f]["engineering_clean"] and A[f]["risk_clean"] and A[f]["all_windows_have_trades"] and
  A[f]["all_windows_non_negative"] and A[f]["net"]>0 and A[f]["pf"]>=1.25 and A[f]["expectancy"]>0 and
  A[f]["max_dd_pct"]<=10 and A[f]["executable_baskets_per_year"]>=50 and A[f]["frequency_admission_pass"])

 A[f]["v36_dominance_pass"]=(A[f]["executable_baskets_per_year"]>51.33 and A[f]["net"]>648.58 and
  A[f]["expectancy"]>8.42 and A[f]["pf"]>1.2124 and A[f]["max_dd_pct"]<=8.77 and A[f]["all_windows_non_negative"])
 A[f]["release_candidate_pass"]=A[f]["alpha_promotion_pass"] and A[f]["v36_dominance_pass"]

# Cross-validation diagnostic only: never used to retune the current V42 run.
def vol_bucket(x):
 a=x.get("atr_ratio",0)
 return "LOW_VOL" if a<.75 else ("HIGH_VOL" if a>1.35 else "NORMAL_VOL")
def eff_bucket(x):
 e=x.get("efficiency",0)
 return "LOW_EFF" if e<.16 else ("HIGH_EFF" if e>=.28 else "MID_EFF")
def groupkey(x): return (x.get("pattern",""),x.get("route",""),vol_bucket(x),eff_bucket(x),x.get("lane",""))
cv={}
for f in ["OPPORTUNITY_GRID","FULL_V42"]
 folds={}
 for hold in "ABC":
  train=[x for w in "ABC" if w!=hold for x in read(f,w).get("attribution_outcomes",[])]
  test=read(f,hold).get("attribution_outcomes",[])
  groups={}
  for x in train: groups.setdefault(groupkey(x),[]).append(x)
  admitted=set()
  for k,xs in groups.items():
   vals=[x["net"] for x in xs]
   if len(xs)>=3 and sum(vals)>0 and sum(vals)/len(vals)>0 and pf_of(vals)>=1.15:
    admitted.add(k)
  selected=[x for x in test if groupkey(x) in admitted]
  vals=[x["net"] for x in selected]
  folds[hold]={"train_positive_groups":len(admitted),"heldout_trades":len(selected),
               "heldout_net":sum(vals),"heldout_expectancy":sum(vals)/len(vals) if vals else 0,
               "heldout_pf":pf_of(vals),"heldout_non_negative":sum(vals)>=0}
 cv[f]={"folds":folds,"all_heldout_non_negative":all(folds[w]["heldout_non_negative"] for w in "ABC"),
        "all_heldout_have_selected_trades":all(folds[w]["heldout_trades"]>0 for w in "ABC")}
(out/"V42_CROSS_VALIDATION_DIAGNOSTIC.json").write_text(json.dumps({
 "version":"HarmonyBot V42","scope":"DEV-only diagnostic; not used to retune current run","method":"leave-one-window-out grouped Pattern x Route x Volatility x Efficiency x Lane",
 "results":cv},indent=2))

# Pattern signal-to-execution funnel aggregation.
pattern_funnel={}
for f in fams:
 aggpipe={}
 for w in "ABC":
  for p,row in read(f,w).get("pattern_pipeline",{}).items():
   z=aggpipe.setdefault(p,{k:0 for k in row})
   for k,v in row.items(): z[k]+=v
 pattern_funnel[f]=aggpipe
(out/"V42_PATTERN_FUNNEL.json").write_text(json.dumps({"version":"HarmonyBot V42","families":pattern_funnel},indent=2))
supported=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
coverage={}
for f in fams:
 rows=pattern_funnel.get(f,{})
 coverage[f]={"supported_patterns":supported,
  "detected_patterns":[p for p in supported if rows.get(p,{}).get("detected",0)>0],
  "armed_patterns":[p for p in supported if rows.get(p,{}).get("armed",0)>0],
  "executed_patterns":[p for p in supported if rows.get(p,{}).get("executed",0)>0],
  "executed_pattern_count":sum(rows.get(p,{}).get("executed",0)>0 for p in supported)}
(out/"V42_PATTERN_EXECUTION_COVERAGE.json").write_text(json.dumps({"version":"HarmonyBot V42",
 "note":"Coverage is observational DEV evidence, not a threshold-tuning gate. Static audit proves all 12 patterns have a legal execution path.",
 "families":coverage},indent=2))

eligible=[(A[f]["net"],A[f]["pf"],A[f]["executable_baskets_per_year"],f) for f in fams if A[f]["release_candidate_pass"]]
eligible.sort(reverse=True)
winner=eligible[0][-1] if eligible else None

frontier={"version":"HarmonyBot V42","architecture":"CROSS_VALIDATED_MARGINAL_ALPHA_PATTERN_PORTFOLIO",
 "evidence_scope":"DEV-A/B/C only; Fresh untouched",
 "hard_frequency_rule":"Any increase in trades must have added cohort Net>0, Expectancy>0, PF>=1.15 and each DEV window marginal Net>=0.",
 "hard_alpha_gate":"A/B/C Net>=0; aggregate Net>0; PF>=1.25; Expectancy>0; DD<=10%; >=50 baskets/year; frequency gate PASS; engineering/risk clean.",
 "v36_dominance_gate":{"baskets_per_year_gt":51.33,"net_gt":648.58,"expectancy_gt":8.42,"pf_gt":1.2124,"max_dd_pct_lte":8.77},
 "families":A,"development_candidate":winner,"status":"DEV_CANDIDATE" if winner else "NO_PROMOTABLE_CANDIDATE"}
(out/"V42_PERFORMANCE_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
decision={"version":"HarmonyBot V42","development_candidate":winner,"status":frontier["status"],"fresh_validation_used":False,
 "next_stage":"CAPITAL_COMPATIBILITY" if winner else "OPPORTUNITY_CONVERSION_DIAGNOSIS",
 "negative_net_frequency_expansion":"PROHIBITED"}
(out/"V42_PROMOTION_DECISION.json").write_text(json.dumps(decision,indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps(frontier,indent=2))
print("CANDIDATE="+(winner or ""))
