#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V42/merged")
out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "HarmonyBot-V42/final"); out.mkdir(parents=True,exist_ok=True)
fams=["V41_REPLAY","CANONICAL_GEOMETRY","PATTERN_NATIVE","FULL_V42"]; control="V41_REPLAY"
V36={"executable_baskets_per_year":51.33,"net":648.58,"expectancy":8.42,"pf":1.2124,"max_dd_pct":8.77}
patterns=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]

def locate(name):
 xs=list(root.rglob(name))
 if not xs: raise SystemExit("missing "+name)
 return xs[0]
def read(f,w): return json.load(open(locate(f"{f}-{w}.json")))
def pf_of(vals):
 gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
 return gp/gl if gl else (999 if gp else 0)
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
  b=keymap(control,w); c=keymap(f,w); added=[x for k,x in c.items() if k not in b]; vals=[x["net"] for x in added]; allx+=added
  by[w]={"added_trades":len(added),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals)}
 vals=[x["net"] for x in allx]
 z={"added_trades":len(allx),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals),
    "all_window_marginal_net_non_negative":all(by[w]["net"]>=0 for w in "ABC"),"windows":by}
 z["frequency_admission_pass"]=z["added_trades"]>0 and z["net"]>0 and z["expectancy"]>0 and z["pf"]>=1.15 and z["all_window_marginal_net_non_negative"]
 return z

for f in fams:
 m=marginal(f) if f!=control else {"added_trades":0,"net":0,"expectancy":0,"pf":0,"all_window_marginal_net_non_negative":True,"frequency_admission_pass":False,"windows":{}}
 A[f]["marginal_vs_v41_replay"]=m
 A[f]["frequency_admission_pass"]=(f==control and A[f]["executable_baskets_per_year"]>=50) or m["frequency_admission_pass"]
 A[f]["alpha_promotion_pass"]=(A[f]["engineering_clean"] and A[f]["risk_clean"] and A[f]["all_windows_have_trades"] and A[f]["all_windows_non_negative"] and
   A[f]["net"]>0 and A[f]["pf"]>=1.25 and A[f]["expectancy"]>0 and A[f]["max_dd_pct"]<=10 and A[f]["executable_baskets_per_year"]>=50 and A[f]["frequency_admission_pass"])
 A[f]["v36_dominance_pass"]=(A[f]["all_windows_non_negative"] and A[f]["executable_baskets_per_year"]>V36["executable_baskets_per_year"] and
   A[f]["net"]>V36["net"] and A[f]["expectancy"]>V36["expectancy"] and A[f]["pf"]>V36["pf"] and A[f]["max_dd_pct"]<=V36["max_dd_pct"])

# Pattern funnel + attrition.
funnel={}; attrition={}
for f in fams:
 fp={}; ap={}
 for w in "ABC":
  x=read(f,w)
  for p,row in x.get("pattern_pipeline",{}).items():
   z=fp.setdefault(p,{k:0 for k in row})
   for k,v in row.items(): z[k]+=v
  for k,v in x.get("pattern_attrition",{}).items(): ap[k]=ap.get(k,0)+v
 funnel[f]=fp; attrition[f]=ap
(out/"V42_PATTERN_FUNNEL.json").write_text(json.dumps({"version":"HarmonyBot V42","families":funnel},indent=2))
(out/"V42_PATTERN_ATTRITION_MATRIX.json").write_text(json.dumps({"version":"HarmonyBot V42","families":attrition},indent=2))

# DEV-only leave-one-window-out evidence. Never used to retune this run.
def vol(x):
 a=x.get("atr_ratio",0); return "LOW" if a<.75 else ("HIGH" if a>1.35 else "NORMAL")
def eff(x):
 e=x.get("efficiency",0); return "LOW" if e<.16 else ("HIGH" if e>=.28 else "MID")
def gk(x): return (x.get("pattern",""),x.get("route",""),vol(x),eff(x),x.get("lane",""))
cv={}
for f in ["PATTERN_NATIVE","FULL_V42"]:
 folds={}
 for hold in "ABC":
  tr=[x for w in "ABC" if w!=hold for x in read(f,w).get("attribution_outcomes",[])]; te=read(f,hold).get("attribution_outcomes",[])
  groups={}
  for x in tr: groups.setdefault(gk(x),[]).append(x)
  good={k for k,xs in groups.items() if len(xs)>=3 and sum(q["net"] for q in xs)>0 and pf_of([q["net"] for q in xs])>=1.15}
  sel=[x for x in te if gk(x) in good]; vals=[x["net"] for x in sel]
  folds[hold]={"train_positive_groups":len(good),"heldout_trades":len(sel),"heldout_net":sum(vals),"heldout_pf":pf_of(vals)}
 cv[f]=folds
(out/"V42_CROSS_VALIDATION_DIAGNOSTIC.json").write_text(json.dumps({"version":"HarmonyBot V42","dev_only":True,"results":cv},indent=2))

eligible=[(A[f]["net"],A[f]["pf"],A[f]["executable_baskets_per_year"],f) for f in fams if A[f]["alpha_promotion_pass"] and A[f]["v36_dominance_pass"]]
eligible.sort(reverse=True); winner=eligible[0][-1] if eligible else None
frontier={"version":"HarmonyBot V42","architecture":"CANONICAL_HARMONIC_GEOMETRY_OPPORTUNITY_PORTFOLIO","v36_benchmark":V36,
 "hard_frequency_rule":"Added cohort must have Net>0, Expectancy>0, PF>=1.15 and DEV-A/B/C marginal Net>=0.",
 "hard_alpha_gate":"A/B/C Net>=0; aggregate Net>0; PF>=1.25; Expectancy>0; DD<=10%; >=50/year; engineering/risk clean.",
 "v36_dominance_gate":"frequency>51.33; Net>648.58; Expectancy>8.42; PF>1.2124; DD<=8.77; A/B/C Net>=0.",
 "families":A,"development_candidate":winner,"status":"DEV_CANDIDATE" if winner else "NO_PROMOTABLE_CANDIDATE","fresh_used":False}
(out/"V42_PERFORMANCE_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
(out/"V42_V36_DOMINANCE.json").write_text(json.dumps({"benchmark":V36,"families":{f:A[f]["v36_dominance_pass"] for f in fams}},indent=2))
(out/"V42_PROMOTION_DECISION.json").write_text(json.dumps({"development_candidate":winner,"status":frontier["status"],"fresh_validation_used":False,
 "next_stage":"CAPITAL_COMPATIBILITY" if winner else "ARCHITECTURE_ATTRIBUTION","negative_net_frequency_expansion":"PROHIBITED"},indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps(frontier,indent=2))
