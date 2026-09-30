#!/usr/bin/env python3
import json,pathlib,sys,collections,statistics,math
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V47/merged")
out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "HarmonyBot-V47/final"); out.mkdir(parents=True,exist_ok=True)
fams=["V46_SCALE_CONTROL","QUEUE_RECOVERY","NATIVE_M1_EXPANSION","FULL_V47_COMMERCIAL"]
control="V46_SCALE_CONTROL"
V46={"baskets":39,"frequency":26.0,"net":1721.72,"pf":2.1833,"expectancy":44.15,"win_rate":0.5128,"max_dd_pct":4.56}
V36={"baskets":77,"frequency":51.333333333333336,"net":648.58,"pf":1.2124297856312334,
     "expectancy":8.423116883116883,"win_rate":0.42857142857142855,"max_dd_pct":8.768267223382058}
COMM={"baskets":90,"frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":0.50,"max_dd_pct":6.0}
STRETCH={"baskets":120,"frequency":80.0,"net":2500.0,"pf":2.2,"expectancy":20.0,"win_rate":0.50,"max_dd_pct":6.0}

def locate(name):
 xs=list(root.rglob(name))
 if not xs: raise SystemExit("missing "+name)
 return xs[0]
def read(f,w): return json.load(open(locate(f"{f}-{w}.json")))
def pf_of(vals):
 gp=sum(v for v in vals if v>0); gl=abs(sum(v for v in vals if v<0))
 return gp/gl if gl else (999 if gp else 0)
def agg(f):
 xs=[read(f,w) for w in "ABC"]
 rows=[r for x in xs for r in x.get("basket_outcomes",[])]
 vals=[r["net"] for r in rows]; n=len(rows); gp=sum(v for v in vals if v>0); gl=abs(sum(v for v in vals if v<0))
 setups={r["setup"] for r in rows}
 rr=[r.get("r",0) for r in rows]
 z={"baskets":n,"unique_setups":len(setups),"duplicate_reentries":n-len(setups),
    "frequency":n/1.5,"unique_frequency":len(setups)/1.5,"net":sum(vals),"pf":gp/gl if gl else (999 if gp else 0),
    "expectancy":sum(vals)/n if n else 0,"win_rate":sum(v>0 for v in vals)/n if n else 0,
    "realized_rr_mean":statistics.mean(rr) if rr else 0,
    "max_dd_pct":max(x["max_dd_pct"] for x in xs),
    "all_windows_positive":all(x["net"]>0 for x in xs),"all_windows_have_trades":all(x["baskets"]>0 for x in xs),
    "engineering_clean":all(x["engineering_clean"] for x in xs),
    "risk_clean":all(x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 and x["unprotected_survivors"]==0 for x in xs),
    "slot_blocked":sum(x.get("slot_blocked",0) for x in xs),"parked":sum(x.get("parked",0) for x in xs),
    "revalidated":sum(x.get("revalidated",0) for x in xs),"revalidation_rejected":sum(x.get("revalidation_rejected",0) for x in xs),
    "parked_recovered_executions":sum(x.get("parked_recovered_executions",0) for x in xs),
    "native_temporal_pass":sum(x.get("native_temporal_pass",0) for x in xs),
    "hard_lifetime_expired":sum(x.get("hard_lifetime_expired",0) for x in xs),
    "missed_positive_setups":sum(x.get("missed_positive_setups",0) for x in xs),
    "avoided_negative_setups":sum(x.get("avoided_negative_setups",0) for x in xs),
    "avg_slot_wait_min_weighted":0,"avg_basket_occupancy_min_weighted":0,
    "windows":{w:read(f,w) for w in "ABC"},"rows":rows}
 weights=[max(1,x.get("parked_recovered_executions",0)) for x in xs]
 z["avg_slot_wait_min_weighted"]=sum(x.get("avg_slot_wait_min",0)*w for x,w in zip(xs,weights))/sum(weights) if sum(weights) else 0
 bw=[max(1,x.get("baskets",0)) for x in xs]
 z["avg_basket_occupancy_min_weighted"]=sum(x.get("avg_basket_occupancy_min",0)*w for x,w in zip(xs,bw))/sum(bw) if sum(bw) else 0
 return z
A={f:agg(f) for f in fams}

# Hard baseline replay contract.
c=A[control]
c["baseline_reproduction"]={
 "basket_delta":c["baskets"]-V46["baskets"],"net_delta":c["net"]-V46["net"],"pf_delta":c["pf"]-V46["pf"],
 "expectancy_delta":c["expectancy"]-V46["expectancy"],"wr_delta":c["win_rate"]-V46["win_rate"],
 "dd_delta":c["max_dd_pct"]-V46["max_dd_pct"],
 "pass":c["baskets"]==V46["baskets"] and abs(c["net"]-V46["net"])<=0.20 and abs(c["pf"]-V46["pf"])<=0.002 and
        abs(c["expectancy"]-V46["expectancy"])<=0.10 and abs(c["win_rate"]-V46["win_rate"])<=0.002 and
        abs(c["max_dd_pct"]-V46["max_dd_pct"])<=0.05 and c["duplicate_reentries"]==0 and c["engineering_clean"] and c["risk_clean"]
}

control_sets={w:{r["setup"] for r in read(control,w).get("basket_outcomes",[])} for w in "ABC"}
def marginal(f):
 by={}; added=[]
 for w in "ABC":
  rows=[r for r in read(f,w).get("basket_outcomes",[]) if r["setup"] not in control_sets[w]]
  vals=[r["net"] for r in rows]; added.extend(rows)
  by[w]={"trades":len(rows),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals)}
 vals=[r["net"] for r in added]
 z={"trades":len(added),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"pf":pf_of(vals),
    "windows":by,"all_windows_non_negative":all(by[w]["net"]>=0 for w in "ABC")}
 z["pass"]=z["trades"]>0 and z["net"]>0 and z["expectancy"]>0 and z["pf"]>=1.20 and z["all_windows_non_negative"]
 return z

for f in fams:
 A[f]["marginal_vs_control"]=None if f==control else marginal(f)
 A[f]["v36_all_metric_dominance"]=(
   f!=control and A[f]["baskets"]>V36["baskets"] and A[f]["frequency"]>V36["frequency"] and A[f]["net"]>V36["net"] and
   A[f]["pf"]>V36["pf"] and A[f]["expectancy"]>V36["expectancy"] and A[f]["win_rate"]>V36["win_rate"] and
   A[f]["max_dd_pct"]<V36["max_dd_pct"] and A[f]["all_windows_positive"] and A[f]["duplicate_reentries"]==0 and
   A[f]["engineering_clean"] and A[f]["risk_clean"])
 marg=A[f]["marginal_vs_control"]
 A[f]["commercial_freeze_candidate_gate"]=(
   c["baseline_reproduction"]["pass"] and f!=control and A[f]["v36_all_metric_dominance"] and
   A[f]["baskets"]>=COMM["baskets"] and A[f]["frequency"]>=COMM["frequency"] and A[f]["net"]>=COMM["net"] and
   A[f]["pf"]>=COMM["pf"] and A[f]["expectancy"]>=COMM["expectancy"] and A[f]["win_rate"]>=COMM["win_rate"] and
   A[f]["max_dd_pct"]<=COMM["max_dd_pct"] and A[f]["all_windows_positive"] and
   marg is not None and marg["pass"] and A[f]["duplicate_reentries"]==0 and A[f]["engineering_clean"] and A[f]["risk_clean"])
 A[f]["stretch_gate"]=(
   A[f]["baskets"]>=STRETCH["baskets"] and A[f]["frequency"]>=STRETCH["frequency"] and A[f]["net"]>=STRETCH["net"] and
   A[f]["pf"]>=STRETCH["pf"] and A[f]["expectancy"]>=STRETCH["expectancy"] and A[f]["win_rate"]>=STRETCH["win_rate"] and
   A[f]["max_dd_pct"]<=STRETCH["max_dd_pct"])
 A[f]["ultimate_target_status"]={
   "frequency_200":A[f]["frequency"]>=200,"pf_2p5":A[f]["pf"]>=2.5,"wr_65":A[f]["win_rate"]>=.65,
   "realized_rr_2":A[f]["realized_rr_mean"]>=2.0,
   "annual_return_100_simple":(A[f]["net"]/10000.0/1.5)>=1.0,
   "profitable_months_10_of_12":"NOT_EVALUABLE_FROM_CURRENT_REPORT_SCHEMA"
 }

# Pattern x route x scale event funnel.
funnel_report={}
for f in fams:
 groups=collections.defaultdict(lambda:collections.Counter())
 for w in "ABC":
  for e in read(f,w).get("events",[]):
   k=f'{e["pattern"]}|{e["route"]}|S{e["scale"]}'
   reason=e["reason"]; state=e["state"]; g=groups[k]
   if "DETECTED" in reason: g["detected"]+=1
   if "VALIDATED" in reason: g["validated"]+=1
   if "ROUTE_" in reason: g["routed"]+=1
   if "WAIT_PRZ" in reason: g["prz"]+=1
   if "PRZ_RETEST" in reason: g["confirming"]+=1
   if "PATTERN_NATIVE_M1_PASS" in reason: g["native_temporal_pass"]+=1
   if "CONFIRMATION_PASSED_GRID_PREPLANNED" in reason: g["armed"]+=1
   if "SLOT_BLOCKED" in reason: g["slot_blocked"]+=1
   if "PARKED_NO_BROKER_ORDER_NO_RESERVED_RISK" in reason: g["parked"]+=1
   if "REVALIDATION" in reason or "REVALIDATED" in reason: g["revalidated"]+=1
   if "REVALIDATION_FAILED" in reason or "PARKED_REVALIDATION_REJECTED" in reason: g["revalidation_rejected"]+=1
   if "FIB_GRID_LEG0_FILLED" in reason: g["executed"]+=1
   if state=="EXPIRED" or reason.startswith("EXPIRED:"): g["expired"]+=1
   if state=="INVALIDATED" or reason.startswith("INVALIDATED:"): g["invalidated"]+=1
 funnel_report[f]={k:dict(v) for k,v in sorted(groups.items())}
(out/"V47_PATTERN_FUNNEL.json").write_text(json.dumps({"version":"HarmonyBot V47","by_pattern_route_scale":funnel_report},indent=2))

# Slot occupancy report.
slot_report={}
for f in fams:
 slots=[x for w in "ABC" for x in read(f,w).get("slot_occupancy",[])]
 mins=[x["occupancy_minutes"] for x in slots]
 slot_report[f]={"baskets":len(slots),"average_minutes":statistics.mean(mins) if mins else 0,
  "median_minutes":statistics.median(mins) if mins else 0,
  "p90_minutes":sorted(mins)[min(len(mins)-1,max(0,math.ceil(.9*len(mins))-1))] if mins else 0,
  "by_route":{}}
 for route in sorted({x["route"] for x in slots}):
  rr=[x["occupancy_minutes"] for x in slots if x["route"]==route]
  slot_report[f]["by_route"][route]={"n":len(rr),"avg":statistics.mean(rr) if rr else 0}
(out/"V47_SLOT_OCCUPANCY_REPORT.json").write_text(json.dumps({"version":"HarmonyBot V47","families":slot_report},indent=2))

# Queue recovery and opportunity loss.
queue={}
opportunity={}
for f in fams:
 opp=[x for w in "ABC" for x in read(f,w).get("opportunity_loss",[])]
 opportunity[f]={"events":opp,"missed_positive":sum(x["missed_positive"] for x in opp),"avoided_negative":sum(x["avoided_negative"] for x in opp),
                 "mean_shadow_mfe_r":statistics.mean([x["shadow_mfe_r"] for x in opp]) if opp else 0,
                 "mean_shadow_mae_r":statistics.mean([x["shadow_mae_r"] for x in opp]) if opp else 0}
 queue[f]={"slot_blocked":A[f]["slot_blocked"],"parked":A[f]["parked"],"revalidated":A[f]["revalidated"],
           "revalidation_rejected":A[f]["revalidation_rejected"],"recovered_executions":A[f]["parked_recovered_executions"],
           "avg_slot_wait_min":A[f]["avg_slot_wait_min_weighted"],"avg_basket_occupancy_min":A[f]["avg_basket_occupancy_min_weighted"]}
(out/"V47_ARMED_QUEUE_RECOVERY.json").write_text(json.dumps({"version":"HarmonyBot V47","families":queue},indent=2))
(out/"V47_OPPORTUNITY_LOSS_LEDGER.json").write_text(json.dumps({"version":"HarmonyBot V47","families":opportunity},indent=2))

# Pattern/route/scale outcome attribution.
attrib={}
for f in fams:
 rows=A[f]["rows"]; g=collections.defaultdict(list)
 # Scale for executed outcome is recovered from matching EXECUTED/FIB_GRID event by setup.
 smap={}
 for w in "ABC":
  for e in read(f,w).get("events",[]):
   if "FIB_GRID_LEG0_FILLED" in e.get("reason",""): smap[e["setup"]]=e["scale"]
 for r in rows:
  scale=smap.get(r["setup"],0); g[f'{r["pattern"]}|{r["route"]}|S{scale}'].append(r["net"])
 attrib[f]={k:{"trades":len(v),"net":sum(v),"expectancy":sum(v)/len(v),"pf":pf_of(v),"win_rate":sum(x>0 for x in v)/len(v)}
            for k,v in sorted(g.items())}
(out/"V47_PATTERN_ROUTE_SCALE_ATTRIBUTION.json").write_text(json.dumps({"version":"HarmonyBot V47","families":attrib},indent=2))

marginal_report={f:A[f]["marginal_vs_control"] for f in fams if f!=control}
(out/"V47_MARGINAL_FREQUENCY_REPORT.json").write_text(json.dumps({"version":"HarmonyBot V47","control":control,"families":marginal_report},indent=2))
(out/"V47_V36_DOMINANCE.json").write_text(json.dumps({"version":"HarmonyBot V47","benchmark":V36,"families":{f:A[f]["v36_all_metric_dominance"] for f in fams}},indent=2))
(out/"V47_COMMERCIAL_FREEZE_GATE.json").write_text(json.dumps({"version":"HarmonyBot V47","minimum":COMM,"families":{f:A[f]["commercial_freeze_candidate_gate"] for f in fams}},indent=2))

eligible=[(A[f]["net"],A[f]["pf"],A[f]["frequency"],-A[f]["max_dd_pct"],f) for f in fams if A[f]["commercial_freeze_candidate_gate"]]
eligible.sort(reverse=True); winner=eligible[0][-1] if eligible else None

# Strip bulky rows before frontier.
for f in fams: A[f].pop("rows",None)
status="COMMERCIAL_FREEZE_CANDIDATE_PASS" if winner else "HOLD_WITH_EVIDENCE"
frontier={"version":"HarmonyBot V47","architecture":"ALPHA_PRESERVING_THROUGHPUT_SERIAL_OPPORTUNITY",
 "v46_scale_baseline":V46,"v36_benchmark":V36,"commercial_candidate_minimum":COMM,"stretch_minimum":STRETCH,
 "baseline_reproduction_pass":c["baseline_reproduction"]["pass"],"families":A,"development_candidate":winner,
 "status":status,"fresh_used":False,"next_stage":"CAPITAL_COMPATIBILITY" if winner else "STOP_DEV_HOLD"}
(out/"V47_PERFORMANCE_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
(out/"candidate.txt").write_text(winner or "")
(out/"V47_CAPITAL_COMPATIBILITY.json").write_text(json.dumps({"version":"HarmonyBot V47","status":"PENDING" if winner else "NOT_RUN_GATE_BLOCKED","candidate":winner},indent=2))
if not winner:
 (out/"V47_FINAL_COMMERCIAL_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V47","decision":"HOLD_WITH_EVIDENCE",
  "reason":"DEV commercial freeze candidate gate not passed","fresh_used":False},indent=2))
print(json.dumps(frontier,indent=2))
