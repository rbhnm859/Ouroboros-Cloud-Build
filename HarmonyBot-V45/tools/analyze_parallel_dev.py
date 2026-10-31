#!/usr/bin/env python3
import json,pathlib,sys,collections
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V45/merged")
out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "HarmonyBot-V45/final"); out.mkdir(parents=True,exist_ok=True)
fams=["V36_REPLAY","UNIQUE_SETUP_CORE","STABLE_ROUTE_CANONICAL","FULL_V45"]; control="V36_REPLAY"
V36={"baskets":77,"frequency":51.333333333333336,"pf":1.2124297856312334,"net":648.58,"expectancy":8.423116883116883,
     "win_rate":0.42857142857142855,"max_dd_pct":8.768267223382058,"independent_setups":55}
CLEAR={"baskets":90,"frequency":60.0,"pf":1.35,"net":800.0,"expectancy":10.0,"win_rate":0.45,"max_dd_pct":8.0}

def locate(name):
 xs=list(root.rglob(name))
 if not xs: raise SystemExit("missing "+name)
 return xs[0]
def read(f,w): return json.load(open(locate(f"{f}-{w}.json")))
def pf_of(vals):
 gp=sum(v for v in vals if v>0); gl=abs(sum(v for v in vals if v<0))
 return gp/gl if gl else (999 if gp else 0)
def aggregate(f):
 xs=[read(f,w) for w in "ABC"]; vals=[o for x in xs for o in x.get("basket_outcomes",[])]
 n=len(vals); pnl=[x["net"] for x in vals]; gp=sum(v for v in pnl if v>0); gl=abs(sum(v for v in pnl if v<0))
 setups={x["setup"] for x in vals}
 z={"baskets":n,"unique_setups":len(setups),"duplicate_reentries":n-len(setups),"frequency":n/1.5,"unique_frequency":len(setups)/1.5,
    "pf":gp/gl if gl else (999 if gp else 0),"net":sum(pnl),"expectancy":sum(pnl)/n if n else 0,
    "win_rate":sum(v>0 for v in pnl)/n if n else 0,"wins":sum(v>0 for v in pnl),"losses":sum(v<0 for v in pnl),
    "max_dd_pct":max(x["max_dd_pct"] for x in xs),"all_windows_positive":all(x["net"]>0 for x in xs),
    "engineering_clean":all(x["engineering_clean"] for x in xs),
    "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
    "duplicate_suppressed":sum(x.get("duplicate_suppressed",0) for x in xs),
    "m1_rescue_admissions":sum(x.get("m1_rescue_admissions",0) for x in xs),
    "transition_proof_rejected":sum(x.get("transition_proof_rejected",0) for x in xs),
    "independent_scale_candidates":sum(x.get("independent_scale_candidates",0) for x in xs),
    "windows":{w:read(f,w) for w in "ABC"}}
 return z,vals

A={}; O={}
for f in fams: A[f],O[f]=aggregate(f)

# Exact V36 historical replay validation.
c=A[control]
c["replay_match"]={
 "basket_delta":c["baskets"]-V36["baskets"],"net_delta":c["net"]-V36["net"],"pf_delta":c["pf"]-V36["pf"],
 "pass":c["baskets"]==V36["baskets"] and abs(c["net"]-V36["net"])<=0.05 and abs(c["pf"]-V36["pf"])<=0.0005
}

# Independent first-trade economics of V36 replay.
first=[]; seen=set()
for w in "ABC":
 for x in read(control,w).get("basket_outcomes",[]):
  k=(w,x["setup"])
  if k in seen: continue
  seen.add(k); first.append(x)
fpnl=[x["net"] for x in first]
first_metrics={"trades":len(first),"net":sum(fpnl),"expectancy":sum(fpnl)/len(fpnl) if fpnl else 0,
               "pf":pf_of(fpnl),"win_rate":sum(v>0 for v in fpnl)/len(fpnl) if fpnl else 0}
dups=[x for w in "ABC" for x in read(control,w).get("basket_outcomes",[])][len(first):] # overwritten below with exact membership
seen=set(); dup_rows=[]
for w in "ABC":
 for x in read(control,w).get("basket_outcomes",[]):
  k=(w,x["setup"])
  if k in seen: dup_rows.append(x)
  else: seen.add(k)
dpnl=[x["net"] for x in dup_rows]
duplicate_metrics={"trades":len(dup_rows),"net":sum(dpnl),"expectancy":sum(dpnl)/len(dpnl) if dpnl else 0,
                   "pf":pf_of(dpnl),"win_rate":sum(v>0 for v in dpnl)/len(dpnl) if dpnl else 0}

control_setup_by_window={w:{x["setup"] for x in read(control,w).get("basket_outcomes",[])} for w in "ABC"}

def marginal_unique(f):
 by={}; all_added=[]
 for w in "ABC":
  added=[x for x in read(f,w).get("basket_outcomes",[]) if x["setup"] not in control_setup_by_window[w]]
  vals=[x["net"] for x in added]; all_added.extend(added)
  by[w]={"trades":len(added),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals)}
 vals=[x["net"] for x in all_added]
 return {"trades":len(all_added),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals),
         "all_windows_non_negative":all(by[w]["net"]>=0 for w in "ABC"),"windows":by,
         "pass":len(all_added)>0 and sum(vals)>0 and (sum(vals)/len(vals) if vals else 0)>0 and pf_of(vals)>=1.15 and all(by[w]["net"]>=0 for w in "ABC")}

for f in fams:
 A[f]["marginal_new_unique_vs_v36"]=marginal_unique(f) if f!=control else None
 A[f]["historical_all_metric_dominance"]=(
   f!=control and A[f]["baskets"]>V36["baskets"] and A[f]["frequency"]>V36["frequency"] and
   A[f]["pf"]>V36["pf"] and A[f]["net"]>V36["net"] and A[f]["expectancy"]>V36["expectancy"] and
   A[f]["win_rate"]>V36["win_rate"] and A[f]["max_dd_pct"]<V36["max_dd_pct"] and
   A[f]["all_windows_positive"] and A[f]["engineering_clean"] and A[f]["risk_clean"] and
   A[f]["duplicate_reentries"]==0)
 A[f]["clear_breakthrough_gate"]=(
   A[f]["historical_all_metric_dominance"] and A[f]["baskets"]>=CLEAR["baskets"] and A[f]["frequency"]>=CLEAR["frequency"] and
   A[f]["pf"]>=CLEAR["pf"] and A[f]["net"]>=CLEAR["net"] and A[f]["expectancy"]>=CLEAR["expectancy"] and
   A[f]["win_rate"]>=CLEAR["win_rate"] and A[f]["max_dd_pct"]<=CLEAR["max_dd_pct"] and
   A[f]["marginal_new_unique_vs_v36"] is not None and A[f]["marginal_new_unique_vs_v36"]["pass"])

# Pattern / subtype / route economics.
coh={}
for f in fams:
 rows=O[f]
 def g(keys):
  d=collections.defaultdict(list)
  for x in rows: d["|".join(str(x.get(k,"")) for k in keys)].append(x["net"])
  return {k:{"trades":len(v),"net":sum(v),"expectancy":sum(v)/len(v),"pf":pf_of(v),"win_rate":sum(x>0 for x in v)/len(v)}
          for k,v in sorted(d.items())}
 coh[f]={"pattern":g(["pattern"]),"subtype":g(["subtype"]),"route":g(["route"]),"pattern_route":g(["pattern","route"])}
(out/"V45_COHORT_ECONOMICS.json").write_text(json.dumps({"version":"HarmonyBot V45","families":coh},indent=2))

# Funnel aggregation.
funnel={}
for f in fams:
 z={}
 for w in "ABC":
  for p,row in read(f,w).get("pattern_pipeline",{}).items():
   d=z.setdefault(p,{k:0 for k in row})
   for k,v in row.items(): d[k]+=v
 funnel[f]=z
(out/"V45_PATTERN_FUNNEL.json").write_text(json.dumps({"version":"HarmonyBot V45","families":funnel},indent=2))

eligible=[(A[f]["net"],A[f]["pf"],A[f]["frequency"],f) for f in fams if A[f]["clear_breakthrough_gate"]]
eligible.sort(reverse=True); winner=eligible[0][-1] if eligible else None
frontier={"version":"HarmonyBot V45","architecture":"RESTORED_EDGE_INDEPENDENT_SETUP_EXPANSION",
 "v36_benchmark":V36,"clear_breakthrough_minimum":CLEAR,"v36_replay_first_unique":first_metrics,"v36_duplicate_reentry":duplicate_metrics,
 "control_reproduction_pass":c["replay_match"]["pass"],"families":A,"development_candidate":winner,
 "status":"CLEAR_HISTORICAL_BREAKTHROUGH" if winner else "NO_CLEAR_BREAKTHROUGH",
 "fresh_used":False,"next_stage":"CAPITAL_COMPATIBILITY" if winner else "ROLLBACK_OR_REARCHITECTURE_DECISION"}
(out/"V45_PERFORMANCE_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
(out/"V45_V36_FORENSICS.json").write_text(json.dumps({"v36":V36,"first_unique":first_metrics,"duplicate_reentry":duplicate_metrics},indent=2))
(out/"V45_PROMOTION_DECISION.json").write_text(json.dumps({"candidate":winner,"status":frontier["status"],"fresh_used":False,
 "capital_allowed":bool(winner),"if_fail":"DO_NOT_TUNE_FRESH; reconsider architecture or rollback kernel"},indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps(frontier,indent=2))
