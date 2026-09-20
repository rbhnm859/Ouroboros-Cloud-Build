#!/usr/bin/env python3
import json,pathlib,sys,collections
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V43/merged")
out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "HarmonyBot-V43/final"); out.mkdir(parents=True,exist_ok=True)
fams=["V42_CONTROL","CONDITIONAL_ALPHA","ALPHA_AUCTION","FULL_V43"]; control="V42_CONTROL"
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
  added=[x for k,x in c.items() if k not in b]
  vals=[x["net"] for x in added]; allx+=added
  by[w]={"added_trades":len(added),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals)}
 vals=[x["net"] for x in allx]
 z={"added_trades":len(allx),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals),
    "all_window_marginal_net_non_negative":all(by[w]["net"]>=0 for w in "ABC"),"windows":by}
 z["frequency_admission_pass"]=z["added_trades"]>0 and z["net"]>0 and z["expectancy"]>0 and z["pf"]>=1.15 and z["all_window_marginal_net_non_negative"]
 return z

for f in fams:
 m=marginal(f) if f!=control else {"added_trades":0,"net":0,"expectancy":0,"pf":0,"all_window_marginal_net_non_negative":True,"frequency_admission_pass":False,"windows":{}}
 A[f]["marginal_vs_v42_control"]=m
 A[f]["frequency_admission_pass"]=m["frequency_admission_pass"] if f!=control else False
 A[f]["absolute_positive_net_gate"]=(A[f]["net"]>0 and A[f]["expectancy"]>0 and A[f]["all_windows_non_negative"])
 A[f]["alpha_gate"]=(A[f]["engineering_clean"] and A[f]["risk_clean"] and A[f]["all_windows_have_trades"] and A[f]["absolute_positive_net_gate"] and
   A[f]["pf"]>=1.25 and A[f]["max_dd_pct"]<=10 and A[f]["executable_baskets_per_year"]>=50)
 A[f]["v36_dominance_pass"]=(A[f]["all_windows_non_negative"] and A[f]["baskets"]>V36["baskets_1p5y"] and
   A[f]["executable_baskets_per_year"]>V36["executable_baskets_per_year"] and A[f]["net"]>V36["net"] and
   A[f]["expectancy"]>V36["expectancy"] and A[f]["pf"]>V36["pf"] and A[f]["max_dd_pct"]<=V36["max_dd_pct"])
 A[f]["promotion_pass"]=(A[f]["alpha_gate"] and A[f]["v36_dominance_pass"] and A[f]["frequency_admission_pass"])

# Funnel and terminal-reason attrition.
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
(out/"V43_PATTERN_FUNNEL.json").write_text(json.dumps({"version":"HarmonyBot V43","families":funnel},indent=2))
(out/"V43_PATTERN_ATTRITION_MATRIX.json").write_text(json.dumps({"version":"HarmonyBot V43","families":attrition},indent=2))
(out/"V43_OPPORTUNITY_LOSS_LEDGER.json").write_text(json.dumps({"version":"HarmonyBot V43","families":opportunity},indent=2))

# Cohort economics. Diagnostic only: never use held-out/Fresh for tuning.
cohort={}
for f in fams:
 rows=[x for w in "ABC" for x in read(f,w).get("attribution_outcomes",[])]
 def grouped(keys):
  g=collections.defaultdict(list)
  for x in rows: g["|".join(str(x.get(k,"")) for k in keys)].append(x)
  return {k:metrics(v) for k,v in sorted(g.items())}
 cohort[f]={"pattern":grouped(["pattern"]),
            "pattern_route":grouped(["pattern","route"]),
            "pattern_route_regime":grouped(["pattern","route","regime_class"]),
            "route":grouped(["route"])}
(out/"V43_COHORT_ECONOMICS.json").write_text(json.dumps({"version":"HarmonyBot V43","families":cohort},indent=2))

# Leave-one-window-out Pattern x Route x Regime x volatility x efficiency x lane.
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
  # Minimum 4 observations + positive economics: deliberately conservative and diagnostic-only.
  good={k for k,xs in groups.items() if len(xs)>=4 and sum(q["net"] for q in xs)>0 and
        (sum(q["net"] for q in xs)/len(xs))>0 and pf_of([q["net"] for q in xs])>=1.15}
  sel=[x for x in te if gk(x) in good]; vals=[x["net"] for x in sel]
  folds[hold]={"train_positive_groups":len(good),"heldout_trades":len(sel),"heldout_net":sum(vals),
               "heldout_expectancy":sum(vals)/len(vals) if vals else 0,"heldout_pf":pf_of(vals)}
 cv[f]=folds
(out/"V43_CROSS_VALIDATION_DIAGNOSTIC.json").write_text(json.dumps({"version":"HarmonyBot V43","dev_only":True,"results":cv},indent=2))

eligible=[(A[f]["net"],A[f]["pf"],A[f]["executable_baskets_per_year"],f) for f in fams if A[f]["promotion_pass"]]
eligible.sort(reverse=True); winner=eligible[0][-1] if eligible else None
frontier={"version":"HarmonyBot V43","architecture":"CROSS_REGIME_POSITIVE_ALPHA_HARMONIC_PORTFOLIO","v36_benchmark":V36,
 "hard_net_rule":"Aggregate Net>0 and DEV-A/B/C each Net>=0. Negative-net candidates cannot promote.",
 "hard_frequency_rule":"Relative to V42_CONTROL, added cohort must have trades>0, Net>0, Expectancy>0, PF>=1.15 and DEV-A/B/C marginal Net>=0.",
 "alpha_gate":"PF>=1.25; Expectancy>0; DD<=10%; >=50/year; A/B/C non-negative; engineering/risk clean.",
 "v36_dominance_gate":"baskets>77; frequency>51.33/year; Net>648.58; Expectancy>8.42; PF>1.2124; DD<=8.77; A/B/C Net>=0.",
 "frequency_staircase":[">52/year","75/year","100/year","150/year","maximum robust frequency"],
 "families":A,"development_candidate":winner,"status":"DEV_BREAKTHROUGH_CANDIDATE" if winner else "NO_PROMOTABLE_CANDIDATE",
 "fresh_used":False}
(out/"V43_PERFORMANCE_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
(out/"V43_V36_DOMINANCE.json").write_text(json.dumps({"benchmark":V36,"families":{f:A[f]["v36_dominance_pass"] for f in fams}},indent=2))
(out/"V43_PROMOTION_DECISION.json").write_text(json.dumps({"development_candidate":winner,"status":frontier["status"],"fresh_validation_used":False,
 "next_stage":"CAPITAL_COMPATIBILITY" if winner else "ARCHITECTURE_ATTRIBUTION",
 "negative_net_frequency_expansion":"PROHIBITED","historical_dominance_required":True},indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps(frontier,indent=2))
