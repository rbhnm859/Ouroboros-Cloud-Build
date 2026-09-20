#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","family"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
a=ap.parse_args(); d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")

rx=re.compile(r"\[V41-BASKET-CLOSED\].*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)")
b=[{"mfe":float(m.group(1)),"mae":float(m.group(2)),"r":float(m.group(3)),"net":float(m.group(4))} for m in rx.finditer(t)]
v=[x["net"] for x in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))

pat=(r"\[V41-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+"
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

freq=re.findall(r"\[V41-FREQUENCY-SUMMARY\].*?schedulerDeferred=(\d+)\s+schedulerRecoveredExecutions=(\d+)\s+structuredRecallAdmitted=(\d+)\s+activeDeferred=(\d+).*?routeDeferred=(\d+)\s+routeRecovered=(\d+)",t)
fc={"scheduler_deferred":0,"scheduler_recovered_executions":0,"structured_recall_admitted":0,"active_deferred":0,"route_deferred":0,"route_recovered":0}
if freq:
 z=list(map(int,freq[-1]))
 for k,n in zip(fc,z): fc[k]=n

ex=re.findall(r"\[V41-EXECUTION-SUMMARY\].*?evidenceExecutable=(\d+)\s+survivalWaits=(\d+)\s+opportunityArbitrations=(\d+)\s+riskRenormalizations=(\d+)\s+riskRejects=(\d+)\s+shadowTargets=(\d+)\s+shadowStops=(\d+)\s+shadowUnresolved=(\d+)",t)
ec={"evidence_executable":0,"survival_waits":0,"opportunity_arbitrations":0,"risk_renormalizations":0,"risk_rejects":0,"shadow_targets":0,"shadow_stops":0,"shadow_unresolved":0}
if ex:
 z=list(map(int,ex[-1]))
 for k,n in zip(ec,z): ec[k]=n

attr=re.findall(r"\[V41-ATTRIBUTION-SUMMARY\].*?observed=(\d+)\s+legacyRankFirstReleased=(\d+)\s+followThroughObserved=(\d+)\s+thesisFailureExits=(\d+)",t)
ac={"attribution_observed":0,"legacy_rank_first_released":0,"follow_through_observed":0,"thesis_failure_exits":0}
if attr:
 z=list(map(int,attr[-1]))
 for k,n in zip(ac,z): ac[k]=n

mar=re.findall(r"\[V41-MARGINAL-ALPHA-SUMMARY\].*?coreAdmissions=(\d+)\s+rescueEvaluated=(\d+)\s+rescueAdmissions=(\d+)\s+rescueRejected=(\d+)",t)
mc={"core_admissions":0,"rescue_evaluated":0,"rescue_admissions":0,"rescue_rejected":0}
if mar:
 z=list(map(int,mar[-1]))
 for k,n in zip(mc,z): mc[k]=n

pipe_rx=re.compile(r"\[V41-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+armed=(\d+)\s+basketPlanned=(\d+)\s+leg0=(\d+)\s+leg1=(\d+)\s+leg2=(\d+)\s+leg3=(\d+)\s+basketClosed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
pipeline={}
for q in pipe_rx.finditer(t):
 pipeline[q.group(1)]={"detected":int(q.group(2)),"validated":int(q.group(3)),"routed":int(q.group(4)),"prz":int(q.group(5)),
 "confirming":int(q.group(6)),"armed":int(q.group(7)),"basket_planned":int(q.group(8)),"leg0":int(q.group(9)),
 "leg1":int(q.group(10)),"leg2":int(q.group(11)),"leg3":int(q.group(12)),"basket_closed":int(q.group(13)),
 "executed":int(q.group(14)),"expired":int(q.group(15)),"rejected":int(q.group(16)),"invalidated":int(q.group(17))}

orx=re.compile(r"\[V41-ATTRIBUTION-OUTCOME\].*?cid=(\S+)\s+key=(\S+)\s+lane=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+dir=(\S+)\s+conflict=(\S+)\s+geom=([-0-9.]+)\s+prz=([-0-9.]+)\s+time=([-0-9.]+)\s+pivot=([-0-9.]+)\s+alpha=([-0-9.]+)\s+regime=([-0-9.]+)\s+atrRatio=([-0-9.]+)\s+efficiency=([-0-9.]+)\s+extensionAtr=([-0-9.]+)\s+adxSlope=([-0-9.]+)\s+evidence=([-0-9.]+)\s+follow=([-0-9.]+)\s+routeFit=([-0-9.]+)\s+stress=([-0-9.]+)\s+netRR=([-0-9.]+)\s+attr=([-0-9.]+)\s+rescue=([-0-9.]+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
outcomes=[]
for q in orx.finditer(t):
 outcomes.append({"cid":q.group(1),"key":q.group(2),"lane":q.group(3),"pattern":q.group(4),"route":q.group(5),"direction":q.group(6),"conflict":q.group(7),
 "geometry":float(q.group(8)),"prz":float(q.group(9)),"time_symmetry":float(q.group(10)),"pivot_quality":float(q.group(11)),
 "alpha":float(q.group(12)),"regime":float(q.group(13)),"atr_ratio":float(q.group(14)),"efficiency":float(q.group(15)),
 "extension_atr":float(q.group(16)),"adx_slope":float(q.group(17)),"evidence":float(q.group(18)),"follow":float(q.group(19)),
 "route_fit":float(q.group(20)),"stress":float(q.group(21)),"net_rr":float(q.group(22)),"attribution":float(q.group(23)),
 "rescue_score":float(q.group(24)),"mfe_r":float(q.group(25)),"mae_r":float(q.group(26)),"realized_r":float(q.group(27)),
 "net":float(q.group(28)),"reason":q.group(29)})

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
"broker_profile_present":"[V41-BROKER-PROFILE]" in t,"evidence_events":len(re.findall(r"\[V41-EVIDENCE\]",t)),
"shadow_total":shadow_total,"shadow_target_rate":ec["shadow_targets"]/shadow_total if shadow_total else 0,
"mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,
"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,
"attribution_outcomes":outcomes,"pattern_pipeline":pipeline,**fc,**ec,**ac,**mc,**c}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
