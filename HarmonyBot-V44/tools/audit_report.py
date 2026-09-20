#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","family"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
a=ap.parse_args(); d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")

rx=re.compile(r"\[V44-BASKET-CLOSED\].*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)")
b=[{"mfe":float(m.group(1)),"mae":float(m.group(2)),"r":float(m.group(3)),"net":float(m.group(4))} for m in rx.finditer(t)]
v=[x["net"] for x in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))

pat=(r"\[V44-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+"
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

def last_counts(pattern,names):
 q=re.findall(pattern,t); z={k:0 for k in names}
 if q:
  vals=list(map(int,q[-1]))
  for k,vv in zip(names,vals): z[k]=vv
 return z
fc=last_counts(r"\[V44-FREQUENCY-SUMMARY\].*?schedulerDeferred=(\d+)\s+schedulerRecoveredExecutions=(\d+)\s+structuredRecallAdmitted=(\d+)\s+activeDeferred=(\d+).*?routeDeferred=(\d+)\s+routeRecovered=(\d+)",
 ["scheduler_deferred","scheduler_recovered_executions","structured_recall_admitted","active_deferred","route_deferred","route_recovered"])
ec=last_counts(r"\[V44-EXECUTION-SUMMARY\].*?evidenceExecutable=(\d+)\s+survivalWaits=(\d+)\s+opportunityArbitrations=(\d+)\s+riskRenormalizations=(\d+)\s+riskRejects=(\d+)\s+shadowTargets=(\d+)\s+shadowStops=(\d+)\s+shadowUnresolved=(\d+)",
 ["evidence_executable","survival_waits","opportunity_arbitrations","risk_renormalizations","risk_rejects","shadow_targets","shadow_stops","shadow_unresolved"])
pc=last_counts(r"\[V44-PROJECTED-D-SUMMARY\].*?generated=(\d+)\s+clusterRejected=(\d+)",["projected_d_generated","projected_d_cluster_rejected"])

pipe_rx=re.compile(r"\[V44-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+armed=(\d+)\s+basketPlanned=(\d+)\s+leg0=(\d+)\s+leg1=(\d+)\s+leg2=(\d+)\s+leg3=(\d+)\s+basketClosed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
pipeline={}
for q in pipe_rx.finditer(t):
 pipeline[q.group(1)]={"detected":int(q.group(2)),"validated":int(q.group(3)),"routed":int(q.group(4)),"prz":int(q.group(5)),
 "confirming":int(q.group(6)),"armed":int(q.group(7)),"basket_planned":int(q.group(8)),"leg0":int(q.group(9)),
 "leg1":int(q.group(10)),"leg2":int(q.group(11)),"leg3":int(q.group(12)),"basket_closed":int(q.group(13)),
 "executed":int(q.group(14)),"expired":int(q.group(15)),"rejected":int(q.group(16)),"invalidated":int(q.group(17))}

orx=re.compile(r"\[V44-ATTRIBUTION-OUTCOME\].*?cid=(\S+)\s+key=(\S+)\s+lane=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+dir=(\S+)\s+conflict=(\S+)\s+geom=([-0-9.]+)\s+prz=([-0-9.]+)\s+time=([-0-9.]+)\s+pivot=([-0-9.]+)\s+alpha=([-0-9.]+)\s+regime=([-0-9.]+)\s+atrRatio=([-0-9.]+)\s+efficiency=([-0-9.]+)\s+extensionAtr=([-0-9.]+)\s+adxSlope=([-0-9.]+)\s+evidence=([-0-9.]+)\s+follow=([-0-9.]+)\s+routeFit=([-0-9.]+)\s+stress=([-0-9.]+)\s+netRR=([-0-9.]+)\s+attr=([-0-9.]+)\s+rescue=([-0-9.]+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)\s+htfContext=([-0-9.]+)\s+temporal=([-0-9.]+)\s+crossRegime=([-0-9.]+)\s+alphaDensity=([-0-9.]+)\s+regimeClass=(\S+)\s+hypotheses=(.*)$",re.M)
outcomes=[]
for q in orx.finditer(t):
 outcomes.append({"cid":q.group(1),"key":q.group(2),"lane":q.group(3),"pattern":q.group(4),"route":q.group(5),"direction":q.group(6),"conflict":q.group(7),
 "geometry":float(q.group(8)),"prz":float(q.group(9)),"time_symmetry":float(q.group(10)),"pivot_quality":float(q.group(11)),
 "alpha":float(q.group(12)),"regime":float(q.group(13)),"atr_ratio":float(q.group(14)),"efficiency":float(q.group(15)),
 "extension_atr":float(q.group(16)),"adx_slope":float(q.group(17)),"evidence":float(q.group(18)),"follow":float(q.group(19)),
 "route_fit":float(q.group(20)),"stress":float(q.group(21)),"net_rr":float(q.group(22)),"attribution":float(q.group(23)),
 "rescue_score":float(q.group(24)),"mfe_r":float(q.group(25)),"mae_r":float(q.group(26)),"realized_r":float(q.group(27)),
 "net":float(q.group(28)),"reason":q.group(29),"htf_context":float(q.group(30)),"temporal":float(q.group(31)),
 "cross_regime":float(q.group(32)),"alpha_density":float(q.group(33)),"regime_class":q.group(34),"hypotheses":q.group(35).strip()})

evrx=re.compile(r"\[V44-EVENT\]\s+cid=(\S+)\s+pattern=(.*?)\s+tf=(\S+)\s+dir=(\S+)\s+state=(\S+)\s+route=(\S+)\s+conflict=(\S+)\s+reason=(.*)$",re.M)
attrition={}
for q in evrx.finditer(t):
 reason=q.group(8).strip()
 if reason.startswith(("REJECTED:","EXPIRED:","INVALIDATED:")) or "DEFERRED" in reason or "SCHEDULER" in reason or "REJECT" in reason:
  k=q.group(2)+"|"+q.group(6)+"|"+reason
  attrition[k]=attrition.get(k,0)+1

opp=[]
opr=re.compile(r"\[V44-OPPORTUNITY-LOSS\]\s+cid=(\S+)\s+winner=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+rank=([-0-9.]+)\s+winnerRank=([-0-9.]+)")
for q in opr.finditer(t):
 opp.append({"cid":q.group(1),"winner":q.group(2),"pattern":q.group(3),"route":q.group(4),"rank":float(q.group(5)),"winner_rank":float(q.group(6))})

eq=d.get("equity",{})
clean_keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
"gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
summary_present=bool(m); clean=summary_present and all(c[k]==0 for k in clean_keys)
out={"family":a.family,"window":a.window,"starting_balance":a.balance,"baskets":len(b),
"wins":sum(x>0 for x in v),"losses":sum(x<0 for x in v),"gross_profit":gp,"gross_loss":gl,
"pf":gp/gl if gl else (999 if gp else 0),"net":sum(v),"expectancy":sum(v)/len(v) if v else 0,
"frequency":len(b)/a.years,"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),
"engineering_clean":clean,"summary_present":summary_present,"basket_activity_present":len(b)>0,
"broker_profile_present":"[V44-BROKER-PROFILE]" in t,
"mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,
"attribution_outcomes":outcomes,"pattern_pipeline":pipeline,"pattern_attrition":attrition,"opportunity_loss_events":opp,
**fc,**ec,**pc,**c}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
