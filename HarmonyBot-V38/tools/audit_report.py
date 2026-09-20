#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","family"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
a=ap.parse_args(); d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")
rx=re.compile(r"\[V38-BASKET-CLOSED\].*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)")
b=[{"mfe":float(m.group(1)),"mae":float(m.group(2)),"r":float(m.group(3)),"net":float(m.group(4))} for m in rx.finditer(t)]
v=[x["net"] for x in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))
pat=(r"\[V38-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+"
     r"orphanPendingOrders=(\d+)\s+stopWideningViolations=(\d+)\s+gapThroughInvalidations=(\d+)\s+gapThroughSurvivors=(\d+)\s+"
     r"unprotectedSurvivors=(\d+)\s+postFillProtectionFailures=(\d+)\s+actualBasketRiskViolations=(\d+)\s+executionStateViolations=(\d+)\s+"
     r"virtualGridFills=(\d+)\s+microModeBaskets=(\d+)\s+capitalRejectedBaskets=(\d+)\s+marginRiskViolations=(\d+)")
m=re.findall(pat,t)
keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
"gap_through_invalidations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures",
"actual_basket_risk_violations","execution_state_violations","virtual_grid_fills","micro_mode_baskets","capital_rejected_baskets","margin_risk_violations"]
c={k:0 for k in keys}
if m:
 for k,z in zip(keys,map(int,m[-1])): c[k]=z
freq=re.findall(r"\[V38-FREQUENCY-SUMMARY\].*?schedulerDeferred=(\d+)\s+schedulerRecoveredExecutions=(\d+)\s+structuredRecallAdmitted=(\d+)\s+activeDeferred=(\d+).*?routeDeferred=(\d+)\s+routeRecovered=(\d+)",t)
fc={"scheduler_deferred":0,"scheduler_recovered_executions":0,"structured_recall_admitted":0,"active_deferred":0,"route_deferred":0,"route_recovered":0}
if freq:
 z=list(map(int,freq[-1]))
 for k,n in zip(fc,z): fc[k]=n
ex=re.findall(r"\[V38-EXECUTION-SUMMARY\].*?evidenceExecutable=(\d+)\s+survivalWaits=(\d+)\s+opportunityArbitrations=(\d+)\s+riskRenormalizations=(\d+)\s+riskRejects=(\d+)\s+shadowTargets=(\d+)\s+shadowStops=(\d+)\s+shadowUnresolved=(\d+)",t)
ec={"evidence_executable":0,"survival_waits":0,"opportunity_arbitrations":0,"risk_renormalizations":0,"risk_rejects":0,"shadow_targets":0,"shadow_stops":0,"shadow_unresolved":0}
if ex:
 z=list(map(int,ex[-1]))
 for k,n in zip(ec,z): ec[k]=n
eq=d.get("equity",{})
clean_keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
"gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
summary_present=bool(m); clean=summary_present and all(c[k]==0 for k in clean_keys)
shadow_total=ec["shadow_targets"]+ec["shadow_stops"]+ec["shadow_unresolved"]
out={"family":a.family,"window":a.window,"starting_balance":a.balance,"baskets":len(b),
"wins":sum(x>0 for x in v),"losses":sum(x<0 for x in v),"gross_profit":gp,"gross_loss":gl,
"pf":gp/gl if gl else (999 if gp else 0),"net":sum(v),"expectancy":sum(v)/len(v) if v else 0,
"frequency":len(b)/a.years,"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),
"engineering_clean":clean,"summary_present":summary_present,"basket_activity_present":len(b)>0,
"broker_profile_present":"[V38-BROKER-PROFILE]" in t,
"exhaustion_veto_events":len(re.findall(r"\[V38-ROUTE-VETO\] type=EXHAUSTION_EVIDENCE",t)),
"evidence_events":len(re.findall(r"\[V38-EVIDENCE\]",t)),
"shadow_total":shadow_total,
"shadow_target_rate":ec["shadow_targets"]/shadow_total if shadow_total else 0,
"mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,
"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,**fc,**ec,**c}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
