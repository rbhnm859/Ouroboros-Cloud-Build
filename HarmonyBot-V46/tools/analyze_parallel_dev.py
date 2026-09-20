#!/usr/bin/env python3
import json,pathlib,sys,collections
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V46/merged")
out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "HarmonyBot-V46/final"); out.mkdir(parents=True,exist_ok=True)
fams=["V36_REPLAY","STABLE_CORE","SCALE_CONVERSION","FULL_V46"]
V36={"baskets":77,"frequency":51.333333333333336,"pf":1.2124297856312334,"net":648.58,"expectancy":8.423116883116883,
     "win_rate":0.42857142857142855,"max_dd_pct":8.768267223382058}
CLEAR={"baskets":90,"frequency":60.0,"pf":1.35,"net":800.0,"expectancy":10.0,"win_rate":0.45,"max_dd_pct":8.0}
def locate(name):
 xs=list(root.rglob(name))
 if not xs: raise SystemExit("missing "+name)
 return xs[0]
def read(f,w): return json.load(open(locate(f"{f}-{w}.json")))
def pf_of(vals):
 gp=sum(v for v in vals if v>0); gl=abs(sum(v for v in vals if v<0))
 return gp/gl if gl else (999 if gp else 0)
def agg(f):
 xs=[read(f,w) for w in "ABC"]; rows=[r for x in xs for r in x.get("basket_outcomes",[])]
 vals=[r["net"] for r in rows]; gp=sum(v for v in vals if v>0); gl=abs(sum(v for v in vals if v<0))
 setups={r["setup"] for r in rows}; n=len(rows)
 return {"baskets":n,"unique_setups":len(setups),"duplicate_reentries":n-len(setups),"frequency":n/1.5,
  "unique_frequency":len(setups)/1.5,"pf":gp/gl if gl else (999 if gp else 0),"net":sum(vals),
  "expectancy":sum(vals)/n if n else 0,"win_rate":sum(v>0 for v in vals)/n if n else 0,
  "max_dd_pct":max(x["max_dd_pct"] for x in xs),"all_windows_positive":all(x["net"]>0 for x in xs),
  "engineering_clean":all(x["engineering_clean"] for x in xs),
  "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
  "duplicate_suppressed":sum(x.get("duplicate_suppressed",0) for x in xs),
  "temporal_rescue_admissions":sum(x.get("temporal_rescue_admissions",0) for x in xs),
  "armed_grace_extended":sum(x.get("armed_grace_extended",0) for x in xs),
  "pre_execution_revalidation_rejected":sum(x.get("pre_execution_revalidation_rejected",0) for x in xs),
  "scale_route_rejected":sum(x.get("scale_route_rejected",0) for x in xs),
  "windows":{w:read(f,w) for w in "ABC"},"rows":rows}
A={f:agg(f) for f in fams}

c=A["V36_REPLAY"]
c["replay_match"]={"pass":c["baskets"]==77 and abs(c["net"]-648.58)<=.05 and abs(c["pf"]-1.2124297856312334)<=.0005,
                   "basket_delta":c["baskets"]-77,"net_delta":c["net"]-648.58,"pf_delta":c["pf"]-1.2124297856312334}

stable_sets={w:{r["setup"] for r in read("STABLE_CORE",w).get("basket_outcomes",[])} for w in "ABC"}
def marginal_vs_stable(f):
 by={}; allrows=[]
 for w in "ABC":
  rr=[r for r in read(f,w).get("basket_outcomes",[]) if r["setup"] not in stable_sets[w]]
  vals=[r["net"] for r in rr]; allrows.extend(rr)
  by[w]={"trades":len(rr),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals)}
 vals=[r["net"] for r in allrows]
 z={"trades":len(allrows),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals),
    "all_windows_non_negative":all(by[w]["net"]>=0 for w in "ABC"),"windows":by}
 z["pass"]=z["trades"]>0 and z["net"]>0 and z["expectancy"]>0 and z["pf"]>=1.15 and z["all_windows_non_negative"]
 return z

for f in fams:
 if f not in ("V36_REPLAY","STABLE_CORE"): A[f]["marginal_vs_stable"]=marginal_vs_stable(f)
 else: A[f]["marginal_vs_stable"]=None
 A[f]["historical_all_metric_dominance"]=(
   f!="V36_REPLAY" and A[f]["baskets"]>V36["baskets"] and A[f]["frequency"]>V36["frequency"] and
   A[f]["pf"]>V36["pf"] and A[f]["net"]>V36["net"] and A[f]["expectancy"]>V36["expectancy"] and
   A[f]["win_rate"]>V36["win_rate"] and A[f]["max_dd_pct"]<V36["max_dd_pct"] and
   A[f]["all_windows_positive"] and A[f]["engineering_clean"] and A[f]["risk_clean"] and A[f]["duplicate_reentries"]==0)
 marg=A[f]["marginal_vs_stable"]
 A[f]["clear_breakthrough_gate"]=(
   A[f]["historical_all_metric_dominance"] and A[f]["baskets"]>=CLEAR["baskets"] and A[f]["frequency"]>=CLEAR["frequency"] and
   A[f]["pf"]>=CLEAR["pf"] and A[f]["net"]>=CLEAR["net"] and A[f]["expectancy"]>=CLEAR["expectancy"] and
   A[f]["win_rate"]>=CLEAR["win_rate"] and A[f]["max_dd_pct"]<=CLEAR["max_dd_pct"] and marg is not None and marg["pass"])

# Cohort economics, without using Fresh.
coh={}
for f in fams:
 rows=A[f]["rows"]
 def grouped(keys):
  g=collections.defaultdict(list)
  for r in rows: g["|".join(str(r.get(k,"")) for k in keys)].append(r["net"])
  return {k:{"trades":len(v),"net":sum(v),"expectancy":sum(v)/len(v),"pf":pf_of(v),"win_rate":sum(x>0 for x in v)/len(v)}
          for k,v in sorted(g.items())}
 coh[f]={"pattern":grouped(["pattern"]),"subtype":grouped(["subtype"]),"route":grouped(["route"]),"pattern_route":grouped(["pattern","route"])}
(out/"V46_COHORT_ECONOMICS.json").write_text(json.dumps({"version":"HarmonyBot V46","families":coh},indent=2))

funnel={}
for f in fams:
 z={}
 for w in "ABC":
  for p,row in read(f,w).get("pattern_pipeline",{}).items():
   q=z.setdefault(p,{k:0 for k in row})
   for k,v in row.items(): q[k]+=v
 funnel[f]=z
(out/"V46_PATTERN_FUNNEL.json").write_text(json.dumps({"version":"HarmonyBot V46","families":funnel},indent=2))

# Remove bulky rows from frontier.
for f in fams: A[f].pop("rows",None)
eligible=[(A[f]["net"],A[f]["pf"],A[f]["frequency"],f) for f in fams if A[f]["clear_breakthrough_gate"]]
eligible.sort(reverse=True); winner=eligible[0][-1] if eligible else None
frontier={"version":"HarmonyBot V46","architecture":"RESTORED_ALPHA_EXECUTION_CONVERSION","v36_benchmark":V36,
 "clear_breakthrough_minimum":CLEAR,"control_reproduction_pass":c["replay_match"]["pass"],"families":A,
 "development_candidate":winner,"status":"CLEAR_HISTORICAL_BREAKTHROUGH" if winner else "NO_CLEAR_BREAKTHROUGH",
 "fresh_used":False,"next_stage":"CAPITAL_COMPATIBILITY" if winner else "ARCHITECTURE_DECISION"}
(out/"V46_PERFORMANCE_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
(out/"V46_PROMOTION_DECISION.json").write_text(json.dumps({"candidate":winner,"status":frontier["status"],
 "fresh_used":False,"capital_allowed":bool(winner),"negative_net_frequency_expansion":"PROHIBITED"},indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps(frontier,indent=2))
