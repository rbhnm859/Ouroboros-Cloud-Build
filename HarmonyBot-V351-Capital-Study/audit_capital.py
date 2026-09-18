#!/usr/bin/env python3
import argparse, collections, json, pathlib, re, statistics

ap=argparse.ArgumentParser()
for x in ("report","log","out","window"): ap.add_argument("--"+x,required=True)
ap.add_argument("--balance",type=float,required=True)
ap.add_argument("--years",type=float,default=.5)
a=ap.parse_args()

d=json.load(open(a.report,encoding="utf-8-sig"))
t=pathlib.Path(a.log).read_text(errors="ignore")

def last_match(pattern):
    m=list(re.finditer(pattern,t,re.S))
    return m[-1] if m else None

def stats(xs):
    if not xs: return {"count":0,"mean":None,"median":None,"min":None,"max":None}
    return {"count":len(xs),"mean":statistics.mean(xs),"median":statistics.median(xs),"min":min(xs),"max":max(xs)}

closed=[]
rx_closed=re.compile(r"\[V351-BASKET-CLOSED\].*?initialRisk=([-0-9.]+)\s+worstRisk=([-0-9.]+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)")
for m in rx_closed.finditer(t):
    closed.append({"initial_risk":float(m.group(1)),"worst_risk":float(m.group(2)),"mfe_r":float(m.group(3)),"mae_r":float(m.group(4)),"realized_r":float(m.group(5)),"net":float(m.group(6))})
vals=[x["net"] for x in closed]
gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))

summary_pat=(r"\[V351-SUMMARY\].*?candidates=(\d+)\s+baskets=(\d+)\s+openLedgers=(\d+)\s+executionErrors=(\d+)\s+"
             r"gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+orphanPendingOrders=(\d+)\s+stopWideningViolations=(\d+)\s+"
             r"gapThroughInvalidations=(\d+)\s+gapThroughSurvivors=(\d+)\s+unprotectedSurvivors=(\d+)\s+postFillProtectionFailures=(\d+)\s+"
             r"actualBasketRiskViolations=(\d+)\s+executionStateViolations=(\d+)\s+virtualGridFills=(\d+)\s+microModeBaskets=(\d+)\s+"
             r"capitalRejectedBaskets=(\d+)\s+marginRiskViolations=(\d+)")
sm=last_match(summary_pat)
keys=["total_harmonic_candidates","basket_ledgers","open_ledgers","execution_errors","grid_risk_violations","duplicate_grid_legs",
      "orphan_pending_orders","stop_widening_violations","gap_through_invalidations","gap_through_survivors","unprotected_survivors",
      "post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","virtual_grid_fills","micro_mode_baskets",
      "capital_rejected_baskets","post_fill_margin_risk_violations"]
counters={k:0 for k in keys}
if sm:
    for k,v in zip(keys,map(int,sm.groups())): counters[k]=v

am=last_match(r"\[V351-ALPHA-SUMMARY\].*?qualityRejected=(\d+)\s+regimeRejected=(\d+)\s+confirmationRejected=(\d+)\s+capitalInfeasible=(\d+)\s+alphaPassed=(\d+)")
alpha={"quality_rejected":0,"regime_rejected":0,"confirmation_rejected":0,"capital_infeasible_candidates":0,"alpha_passed":0}
if am:
    for k,v in zip(alpha.keys(),map(int,am.groups())): alpha[k]=v

alpha_candidate_lines=list(re.finditer(r"\[V351-ALPHA-CANDIDATE\].*?capitalFeasible=(True|False).*?minL0Risk=([-0-9.]+)",t))
capital_feasible=sum(1 for m in alpha_candidate_lines if m.group(1).lower()=="true")
min_l0_vals=[float(m.group(2)) for m in alpha_candidate_lines if m.group(1).lower()=="true" and float(m.group(2))>0]
alpha_eligible=capital_feasible+alpha["capital_infeasible_candidates"]

plans=[]
for m in re.finditer(r"\[V351-GRID-PLAN\].*?logicalLegs=(\d+)\s+physicalDepth=(\d+)\s+micro=(True|False).*?budget=([-0-9.]+)\s+worst=([-0-9.]+)\s+margin=([-0-9.]+)\s+netRR=([-0-9.]+)",t):
    logical=int(m.group(1)); physical=int(m.group(2))
    plans.append({"logical":logical,"physical":physical,"virtual":max(0,logical-physical),"micro":m.group(3).lower()=="true",
                  "budget":float(m.group(4)),"worst":float(m.group(5)),"margin":float(m.group(6)),"net_rr":float(m.group(7))})

post=[]
for m in re.finditer(r"\[V351-POST-FILL-AUDIT\].*?actualWorst=([-0-9.]+)\s+budget=([-0-9.]+)\s+protected=true",t):
    aw=float(m.group(1)); b=float(m.group(2)); post.append({"actual_worst":aw,"budget":b,"utilization":aw/b if b>0 else None})

margin_headroom=len(re.findall(r"REJECTED:MARGIN_HEADROOM\b",t))
physical=[p["physical"] for p in plans]; virtual=[p["virtual"] for p in plans]
physical_dist=dict(sorted(collections.Counter(physical).items()))
virtual_dist=dict(sorted(collections.Counter(virtual).items()))

clean_keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
            "gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations",
            "execution_state_violations","post_fill_margin_risk_violations"]
summary_present=sm is not None
engineering_clean=summary_present and all(counters[k]==0 for k in clean_keys)
eq=d.get("equity",{})

out={
  "study":"HarmonyBot V35.1 Capital Compatibility",
  "candidate":"EXHAUSTION_VETO_ONLY",
  "window":a.window,"starting_balance":a.balance,
  "total_harmonic_candidates":counters["total_harmonic_candidates"],
  "alpha_eligible_candidates":alpha_eligible,
  "capital_feasible_candidates":capital_feasible,
  "capital_infeasible_candidates":alpha["capital_infeasible_candidates"],
  "completed_baskets":len(closed),
  "executable_basket_ratio":(len(closed)/capital_feasible if capital_feasible else None),
  "physical_grid_depth":{**stats(physical),"distribution":physical_dist},
  "virtual_grid_depth":{**stats(virtual),"distribution":virtual_dist},
  "minimum_l0_risk":min(min_l0_vals) if min_l0_vals else None,
  "capital_rejected_baskets":counters["capital_rejected_baskets"],
  "margin_rejections":{"scheduler_headroom":margin_headroom,"post_fill":counters["post_fill_margin_risk_violations"],
                       "combined":margin_headroom+counters["post_fill_margin_risk_violations"]},
  "realized_risk":{
      "closed_initial_risk":stats([x["initial_risk"] for x in closed]),
      "closed_planned_worst_risk":stats([x["worst_risk"] for x in closed]),
      "post_fill_actual_worst_risk":stats([x["actual_worst"] for x in post]),
      "post_fill_budget_utilization":stats([x["utilization"] for x in post if x["utilization"] is not None])
  },
  "performance":{"wins":sum(x>0 for x in vals),"losses":sum(x<0 for x in vals),"gross_profit":gp,"gross_loss":gl,
                 "pf":gp/gl if gl else (999 if gp else 0),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,
                 "frequency_per_year":len(closed)/a.years,"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0)},
  "engineering_clean":engineering_clean,"summary_present":summary_present,"broker_profile_present":"[V351-BROKER-PROFILE]" in t,
  "safety_counters":counters,"alpha_counters":alpha
}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
