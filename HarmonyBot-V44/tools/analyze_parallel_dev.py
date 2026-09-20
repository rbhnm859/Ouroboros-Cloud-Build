#!/usr/bin/env python3
import json,pathlib,sys,collections
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V44/merged")
out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "HarmonyBot-V44/final"); out.mkdir(parents=True,exist_ok=True)
fams=["V43_CONTROL","THESIS_ROUTING","PHYSICAL_GRID","FULL_V44"]; control="V43_CONTROL"
V36={"baskets_1p5y":77,"executable_baskets_per_year":51.33,"net":648.58,"expectancy":8.42,"pf":1.2124,"max_dd_pct":8.77}

def locate(name):
 xs=list(root.rglob(name))
 if not xs: raise SystemExit("missing "+name)
 return xs[0]
def read(f,w): return json.load(open(locate(f"{f}-{w}.json")))
def pf_of(vals):
 gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
 return gp/gl if gl else (999 if gp else 0)
def metrics(xs):
 vals=[x["net"] for x in xs]
 return {"trades":len(xs),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,
         "pf":pf_of(vals),"wins":sum(v>0 for v in vals),"losses":sum(v<0 for v in vals)}
def agg(f):
 xs=[read(f,w) for w in "ABC"]; gp=sum(x["gross_profit"] for x in xs); gl=sum(x["gross_loss"] for x in xs)
 n=sum(x["baskets"] for x in xs); net=sum(x["net"] for x in xs); wins=sum(x["wins"] for x in xs)
 return {"baskets":n,"executable_baskets_per_year":n/1.5,"pf":gp/gl if gl else (999 if gp else 0),
 "net":net,"expectancy":net/n if n else 0,"win_rate":wins/n if n else 0,
 "all_windows_non_negative":all(x["net"]>=0 for x in xs),"all_windows_have_trades":all(x["baskets"]>0 for x in xs),
 "max_dd_pct":max(x["max_dd_pct"] for x in xs),"engineering_clean":all(x["engineering_clean"] for x in xs),
 "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
 "windows":{w:read(f,w) for w in "ABC"}}

A={f:agg(f) for f in fams}
def keymap(f,w): return {x["key"]:x for x in read(f,w).get("attribution_outcomes",[]) if x.get("key")}
def marginal(f):
 by={}; allx=[]
 for w in "ABC":
  b=keymap(control,w); c=keymap(f,w)
  added=[x for k,x in c.items() if k not in b]; vals=[x["net"] for x in added]; allx+=added
  by[w]={"added_trades":len(added),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals)}
 vals=[x["net"] for x in allx]
 z={"added_trades":len(allx),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals),
    "all_window_marginal_net_non_negative":all(by[w]["net"]>=0 for w in "ABC"),"windows":by}
 z["frequency_admission_pass"]=z["added_trades"]>0 and z["net"]>0 and z["expectancy"]>0 and z["pf"]>=1.15 and z["all_window_marginal_net_non_negative"]
 return z

for f in fams:
 m=marginal(f) if f!=control else {"added_trades":0,"net":0,"expectancy":0,"pf":0,"all_window_marginal_net_non_negative":True,"frequency_admission_pass":False,"windows":{}}
 A[f]["marginal_vs_v43_control"]=m
 A[f]["frequency_admission_pass"]=m["frequency_admission_pass"] if f!=control else False
 A[f]["absolute_positive_net_gate"]=(A[f]["net"]>0 and A[f]["expectancy"]>0 and A[f]["all_windows_non_negative"])
 A[f]["alpha_gate"]=(A[f]["engineering_clean"] and A[f]["risk_clean"] and A[f]["all_windows_have_trades"] and A[f]["absolute_positive_net_gate"] and
   A[f]["pf"]>=1.25 and A[f]["max_dd_pct"]<=10 and A[f]["executable_baskets_per_year"]>=50)
 A[f]["v36_dominance_pass"]=(A[f]["all_windows_non_negative"] and A[f]["baskets"]>V36["baskets_1p5y"] and
   A[f]["executable_baskets_per_year"]>V36["executable_baskets_per_year"] and A[f]["net"]>V36["net"] and
   A[f]["expectancy"]>V36["expectancy"] and A[f]["pf"]>V36["pf"] and A[f]["max_dd_pct"]<=V36["max_dd_pct"])
 A[f]["promotion_pass"]=(A[f]["alpha_gate"] and A[f]["v36_dominance_pass"] and A[f]["frequency_admission_pass"])

funnel={}; attrition={}; opportunity={}; gridfail={}; gridrecover={}; thesis={}
for f in fams:
 fp={}; ap={}; op=[]; gf={}; gr=[]; th=[]
 for w in "ABC":
  x=read(f,w)
  for p,row in x.get("pattern_pipeline",{}).items():
   z=fp.setdefault(p,{k:0 for k in row})
   for k,v in row.items(): z[k]+=v
  for k,v in x.get("pattern_attrition",{}).items(): ap[k]=ap.get(k,0)+v
  for k,v in x.get("grid_failures",{}).items(): gf[k]=gf.get(k,0)+v
  op.extend(x.get("opportunity_loss_events",[]))
  gr.extend(x.get("grid_recoveries",[]))
  th.extend(x.get("thesis_outcomes",[]))
 funnel[f]=fp; attrition[f]=ap; opportunity[f]=op; gridfail[f]=gf; gridrecover[f]=gr; thesis[f]=th
(out/"V44_PATTERN_FUNNEL.json").write_text(json.dumps({"version":"HarmonyBot V44","families":funnel},indent=2))
(out/"V44_PATTERN_ATTRITION_MATRIX.json").write_text(json.dumps({"version":"HarmonyBot V44","families":attrition},indent=2))
(out/"V44_OPPORTUNITY_LOSS_LEDGER.json").write_text(json.dumps({"version":"HarmonyBot V44","families":opportunity},indent=2))
(out/"V44_GRID_FAILURE_MATRIX.json").write_text(json.dumps({"version":"HarmonyBot V44","families":gridfail,"recoveries":gridrecover},indent=2))

thesis_econ={}
for f,rows in thesis.items():
 g=collections.defaultdict(list)
 for x in rows: g["|".join([x.get("pattern",""),x.get("thesis",""),x.get("relation",""),x.get("regime_class","")])].append(x)
 thesis_econ[f]={k:metrics(v) for k,v in sorted(g.items())}
(out/"V44_THESIS_ECONOMICS.json").write_text(json.dumps({"version":"HarmonyBot V44","families":thesis_econ},indent=2))

cohort={}
for f in fams:
 rows=[x for w in "ABC" for x in read(f,w).get("attribution_outcomes",[])]
 def grouped(keys):
  g=collections.defaultdict(list)
  for x in rows: g["|".join(str(x.get(k,"")) for k in keys)].append(x)
  return {k:metrics(v) for k,v in sorted(g.items())}
 cohort[f]={"pattern":grouped(["pattern"]),"pattern_route":grouped(["pattern","route"]),
            "pattern_route_regime":grouped(["pattern","route","regime_class"]),"route":grouped(["route"])}
(out/"V44_COHORT_ECONOMICS.json").write_text(json.dumps({"version":"HarmonyBot V44","families":cohort},indent=2))

# DEV-only cross-window diagnostic. Not used to tune this run.
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
  groups={}
  for x in tr: groups.setdefault(gk(x),[]).append(x)
  good={k for k,xs in groups.items() if len(xs)>=4 and sum(q["net"] for q in xs)>0 and
        sum(q["net"] for q in xs)/len(xs)>0 and pf_of([q["net"] for q in xs])>=1.15}
  sel=[x for x in te if gk(x) in good]; vals=[x["net"] for x in sel]
  folds[hold]={"train_positive_groups":len(good),"heldout_trades":len(sel),"heldout_net":sum(vals),
               "heldout_expectancy":sum(vals)/len(vals) if vals else 0,"heldout_pf":pf_of(vals)}
 cv[f]=folds
(out/"V44_CROSS_VALIDATION_DIAGNOSTIC.json").write_text(json.dumps({"version":"HarmonyBot V44","dev_only":True,"results":cv},indent=2))

eligible=[(A[f]["net"],A[f]["pf"],A[f]["executable_baskets_per_year"],f) for f in fams if A[f]["promotion_pass"]]
eligible.sort(reverse=True); winner=eligible[0][-1] if eligible else None
frontier={"version":"HarmonyBot V44","architecture":"THESIS_CONSISTENT_ROUTE_PHYSICAL_GRID_PORTFOLIO","v36_benchmark":V36,
 "hard_net_rule":"Aggregate Net>0 and DEV-A/B/C each Net>=0. Negative-net candidates cannot promote.",
 "hard_frequency_rule":"Added cohort vs V43_CONTROL must have trades>0, Net>0, Expectancy>0, PF>=1.15 and A/B/C marginal Net>=0.",
 "alpha_gate":"PF>=1.25; Expectancy>0; DD<=10%; >=50/year; A/B/C non-negative; engineering/risk clean.",
 "v36_dominance_gate":"baskets>77; frequency>51.33/year; Net>648.58; Expectancy>8.42; PF>1.2124; DD<=8.77; A/B/C Net>=0.",
 "families":A,"development_candidate":winner,"status":"DEV_BREAKTHROUGH_CANDIDATE" if winner else "NO_PROMOTABLE_CANDIDATE","fresh_used":False}
(out/"V44_PERFORMANCE_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
(out/"V44_V36_DOMINANCE.json").write_text(json.dumps({"benchmark":V36,"families":{f:A[f]["v36_dominance_pass"] for f in fams}},indent=2))
(out/"V44_PROMOTION_DECISION.json").write_text(json.dumps({"development_candidate":winner,"status":frontier["status"],"fresh_validation_used":False,
 "next_stage":"CAPITAL_COMPATIBILITY" if winner else "ARCHITECTURE_ATTRIBUTION","negative_net_frequency_expansion":"PROHIBITED"},indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps(frontier,indent=2))
