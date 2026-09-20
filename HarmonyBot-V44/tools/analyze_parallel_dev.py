#!/usr/bin/env python3
import json,pathlib,sys,collections,math
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V44/merged")
out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "HarmonyBot-V44/final"); out.mkdir(parents=True,exist_ok=True)
fams=["V43_CONTROL","CANONICAL_PROJECTED_D","REGIME_NATIVE_EXECUTION","FULL_V44_COMMERCIAL"]
control="V43_CONTROL"
V36={"baskets_1p5y":77,"executable_baskets_per_year":51.33,"net":648.58,"expectancy":8.42,"pf":1.2124,"max_dd_pct":8.77}
COMMERCIAL={"baskets_1p5y":113,"executable_baskets_per_year":75.0,"net":800.0,"expectancy":10.0,"pf":1.35,"max_dd_pct":8.0}
STRETCH={"executable_baskets_per_year":200.0,"pf":2.5,"win_rate":0.65,"max_dd_pct":10.0}

def locate(name):
 xs=list(root.rglob(name))
 if not xs: raise SystemExit("missing "+name)
 return xs[0]
def read(f,w): return json.load(open(locate(f"{f}-{w}.json")))
def pf_of(vals):
 gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
 return gp/gl if gl else (999 if gp else 0)
def basic_metrics(rows):
 vals=[x["net"] for x in rows]; n=len(vals)
 return {"trades":n,"net":sum(vals),"expectancy":sum(vals)/n if n else 0,"pf":pf_of(vals),
         "wins":sum(v>0 for v in vals),"losses":sum(v<0 for v in vals),"win_rate":sum(v>0 for v in vals)/n if n else 0}
def agg(f):
 xs=[read(f,w) for w in "ABC"]; gp=sum(x["gross_profit"] for x in xs); gl=sum(x["gross_loss"] for x in xs)
 n=sum(x["baskets"] for x in xs); net=sum(x["net"] for x in xs); wins=sum(x["wins"] for x in xs)
 z={"baskets":n,"executable_baskets_per_year":n/1.5,"pf":gp/gl if gl else (999 if gp else 0),
    "net":net,"expectancy":net/n if n else 0,"win_rate":wins/n if n else 0,
    "all_windows_positive":all(x["net"]>0 for x in xs),"all_windows_non_negative":all(x["net"]>=0 for x in xs),
    "all_windows_have_trades":all(x["baskets"]>0 for x in xs),
    "max_dd_pct":max(x["max_dd_pct"] for x in xs),
    "engineering_clean":all(x["engineering_clean"] for x in xs),
    "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
    "projected_d_generated":sum(x.get("projected_d_generated",0) for x in xs),
    "projected_d_cluster_rejected":sum(x.get("projected_d_cluster_rejected",0) for x in xs),
    "windows":{w:read(f,w) for w in "ABC"}}
 z["simple_annualized_return_pct"]=100*net/10000/1.5
 return z

A={f:agg(f) for f in fams}
def keymap(f,w): return {x["key"]:x for x in read(f,w).get("attribution_outcomes",[]) if x.get("key")}
def marginal(f):
 by={}; allx=[]
 for w in "ABC":
  b=keymap(control,w); c=keymap(f,w)
  added=[x for k,x in c.items() if k not in b]; allx+=added
  vals=[x["net"] for x in added]
  by[w]={"added_trades":len(added),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals)}
 vals=[x["net"] for x in allx]
 z={"added_trades":len(allx),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals),
    "all_window_marginal_net_non_negative":all(by[w]["net"]>=0 for w in "ABC"),"windows":by}
 z["frequency_admission_pass"]=z["added_trades"]>0 and z["net"]>0 and z["expectancy"]>0 and z["pf"]>=1.15 and z["all_window_marginal_net_non_negative"]
 return z

for f in fams:
 m=marginal(f) if f!=control else {"added_trades":0,"net":0,"expectancy":0,"pf":0,
  "all_window_marginal_net_non_negative":True,"frequency_admission_pass":False,"windows":{}}
 A[f]["marginal_vs_control"]=m
 A[f]["frequency_admission_pass"]=m["frequency_admission_pass"] if f!=control else False
 A[f]["historical_dominance_pass"]=(
   A[f]["baskets"]>V36["baskets_1p5y"] and
   A[f]["executable_baskets_per_year"]>V36["executable_baskets_per_year"] and
   A[f]["net"]>V36["net"] and A[f]["expectancy"]>V36["expectancy"] and A[f]["pf"]>V36["pf"] and
   A[f]["max_dd_pct"]<V36["max_dd_pct"] and A[f]["all_windows_positive"] and A[f]["engineering_clean"] and A[f]["risk_clean"])

# Funnel, attrition and opportunity ledgers.
funnel={}; attrition={}; opportunity={}
for f in fams:
 fp={}; ap={}; op=[]
 for w in "ABC":
  x=read(f,w)
  for p,row in x.get("pattern_pipeline",{}).items():
   z=fp.setdefault(p,{k:0 for k in row})
   for k,v in row.items(): z[k]+=v
  for k,v in x.get("pattern_attrition",{}).items(): ap[k]=ap.get(k,0)+v
  op.extend(x.get("opportunity_loss_events",[]))
 funnel[f]=fp; attrition[f]=ap; opportunity[f]=op
(out/"V44_PATTERN_FUNNEL.json").write_text(json.dumps({"version":"HarmonyBot V44","families":funnel},indent=2))
(out/"V44_PATTERN_ATTRITION_MATRIX.json").write_text(json.dumps({"version":"HarmonyBot V44","families":attrition},indent=2))
(out/"V44_OPPORTUNITY_LOSS_LEDGER.json").write_text(json.dumps({"version":"HarmonyBot V44","families":opportunity},indent=2))

# Cohort economics + hierarchical shrinkage diagnostic. DEV-only; never changes runtime rules.
cohort={}; shrink={}
PRIOR_STRENGTH=8.0
for f in fams:
 rows=[x for w in "ABC" for x in read(f,w).get("attribution_outcomes",[])]
 global_mean=sum(x["net"] for x in rows)/len(rows) if rows else 0
 def grouped(keys):
  g=collections.defaultdict(list)
  for x in rows: g["|".join(str(x.get(k,"")) for k in keys)].append(x)
  return g
 cg={}
 for label,keys in {
   "pattern":["pattern"],"pattern_route":["pattern","route"],
   "pattern_route_regime":["pattern","route","regime_class"],"route":["route"]}.items():
  g=grouped(keys); outg={}
  for k,v in sorted(g.items()):
   m=basic_metrics(v); n=m["trades"]
   m["shrunk_expectancy"]=(n*m["expectancy"]+PRIOR_STRENGTH*global_mean)/(n+PRIOR_STRENGTH) if n+PRIOR_STRENGTH else 0
   m["prior_strength"]=PRIOR_STRENGTH; outg[k]=m
  cg[label]=outg
 cohort[f]=cg
 shrink[f]={"global_expectancy_prior":global_mean,"pattern_route_regime":cg["pattern_route_regime"]}
(out/"V44_COHORT_ECONOMICS.json").write_text(json.dumps({"version":"HarmonyBot V44","families":cohort},indent=2))
(out/"V44_HIERARCHICAL_ALPHA_DIAGNOSTIC.json").write_text(json.dumps({"version":"HarmonyBot V44","dev_only":True,"families":shrink},indent=2))

def vol(x):
 a=x.get("atr_ratio",0); return "LOW" if a<.75 else ("HIGH" if a>1.35 else "NORMAL")
def eff(x):
 e=x.get("efficiency",0); return "LOW" if e<.16 else ("HIGH" if e>=.28 else "MID")
def gk(x): return (x.get("pattern",""),x.get("route",""),x.get("regime_class",""),vol(x),eff(x),x.get("lane",""))

cv={}
for f in fams[1:]:
 folds={}
 for hold in "ABC":
  tr=[x for w in "ABC" if w!=hold for x in read(f,w).get("attribution_outcomes",[])]
  te=read(f,hold).get("attribution_outcomes",[])
  groups=collections.defaultdict(list)
  for x in tr: groups[gk(x)].append(x)
  global_mean=sum(x["net"] for x in tr)/len(tr) if tr else 0
  good=set()
  for k,xs in groups.items():
   m=basic_metrics(xs); n=m["trades"]
   shr=(n*m["expectancy"]+PRIOR_STRENGTH*global_mean)/(n+PRIOR_STRENGTH)
   if n>=4 and m["net"]>0 and m["pf"]>=1.15 and shr>0: good.add(k)
  sel=[x for x in te if gk(x) in good]; vals=[x["net"] for x in sel]
  folds[hold]={"train_positive_groups":len(good),"heldout_trades":len(sel),"heldout_net":sum(vals),
               "heldout_expectancy":sum(vals)/len(vals) if vals else 0,"heldout_pf":pf_of(vals)}
 cv[f]=folds
 A[f]["loo_robustness_pass"]=all(folds[w]["heldout_trades"]>0 and folds[w]["heldout_net"]>=0 for w in "ABC")
 A[f]["loo_total_trades"]=sum(folds[w]["heldout_trades"] for w in "ABC")
 A[f]["loo_total_net"]=sum(folds[w]["heldout_net"] for w in "ABC")
(out/"V44_CROSS_VALIDATION_DIAGNOSTIC.json").write_text(json.dumps({"version":"HarmonyBot V44","dev_only":True,"results":cv},indent=2))
A[control]["loo_robustness_pass"]=False; A[control]["loo_total_trades"]=0; A[control]["loo_total_net"]=0

for f in fams:
 A[f]["commercial_candidate_gate"]=(
   f!=control and A[f]["historical_dominance_pass"] and A[f]["frequency_admission_pass"] and A[f]["loo_robustness_pass"] and
   A[f]["baskets"]>=COMMERCIAL["baskets_1p5y"] and A[f]["executable_baskets_per_year"]>=COMMERCIAL["executable_baskets_per_year"] and
   A[f]["net"]>=COMMERCIAL["net"] and A[f]["expectancy"]>=COMMERCIAL["expectancy"] and A[f]["pf"]>=COMMERCIAL["pf"] and
   A[f]["max_dd_pct"]<=COMMERCIAL["max_dd_pct"] and A[f]["all_windows_positive"] and A[f]["engineering_clean"] and A[f]["risk_clean"])
 A[f]["stretch_status"]={
   "frequency_200":A[f]["executable_baskets_per_year"]>=STRETCH["executable_baskets_per_year"],
   "pf_2p5":A[f]["pf"]>=STRETCH["pf"],"win_rate_65":A[f]["win_rate"]>=STRETCH["win_rate"],
   "dd_10":A[f]["max_dd_pct"]<=STRETCH["max_dd_pct"],
   "simple_annualized_return_100":A[f]["simple_annualized_return_pct"]>=100
 }

eligible=[(A[f]["net"],A[f]["pf"],A[f]["executable_baskets_per_year"],f) for f in fams if A[f]["commercial_candidate_gate"]]
eligible.sort(reverse=True); winner=eligible[0][-1] if eligible else None

frontier={"version":"HarmonyBot V44","architecture":"CANONICAL_HARMONIC_COMMERCIAL_CONVERGENCE",
 "v36_benchmark":V36,"commercial_candidate_minimum":COMMERCIAL,"stretch_targets":STRETCH,
 "hard_net_rule":"Aggregate Net>0 and DEV-A/B/C each Net>0. Negative-net windows cannot promote.",
 "frequency_rule":"Added cohort vs V43_CONTROL must have trades>0, Net>0, Expectancy>0, PF>=1.15 and A/B/C marginal Net>=0.",
 "fresh_governance":"Fresh is untouched until commercial DEV + capital compatibility + hash freeze pass.",
 "families":A,"development_candidate":winner,
 "status":"COMMERCIAL_FREEZE_CANDIDATE" if winner else "NO_COMMERCIAL_CANDIDATE",
 "fresh_used":False}
(out/"V44_PERFORMANCE_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
(out/"V44_V36_DOMINANCE.json").write_text(json.dumps({"benchmark":V36,"families":{f:A[f]["historical_dominance_pass"] for f in fams}},indent=2))
(out/"V44_COMMERCIAL_CANDIDATE_GATE.json").write_text(json.dumps({"minimum":COMMERCIAL,"families":{f:A[f]["commercial_candidate_gate"] for f in fams}},indent=2))
(out/"V44_PROMOTION_DECISION.json").write_text(json.dumps({"development_candidate":winner,"status":frontier["status"],
 "fresh_validation_used":False,"next_stage":"CAPITAL_COMPATIBILITY" if winner else "ARCHITECTURE_ATTRIBUTION",
 "negative_net_frequency_expansion":"PROHIBITED","historical_dominance_required":True},indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps(frontier,indent=2))
