#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","family"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
a=ap.parse_args(); d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")

rx=re.compile(r"\[V45-BASKET-CLOSED\].*?cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
b=[]
for m in rx.finditer(t):
 b.append({"cid":m.group(1),"setup":m.group(2),"pattern":m.group(3),"subtype":m.group(4),"route":m.group(5),"direction":m.group(6),
           "mfe":float(m.group(7)),"mae":float(m.group(8)),"r":float(m.group(9)),"net":float(m.group(10)),"reason":m.group(11)})
v=[x["net"] for x in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))

pat=(r"\[V45-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+"
 r"orphanPendingOrders=(\d+)\s+stopWideningViolations=(\d+)\s+gapThroughInvalidations=(\d+)\s+gapThroughSurvivors=(\d+)\s+"
 r"unprotectedSurvivors=(\d+)\s+postFillProtectionFailures=(\d+)\s+actualBasketRiskViolations=(\d+)\s+executionStateViolations=(\d+)\s+"
 r"virtualGridFills=(\d+)\s+microModeBaskets=(\d+)\s+capitalRejectedBaskets=(\d+)\s+marginRiskViolations=(\d+)")
m=re.findall(pat,t)
keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_invalidations",
"gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations",
"virtual_grid_fills","micro_mode_baskets","capital_rejected_baskets","margin_risk_violations"]
c={k:0 for k in keys}
if m:
 for k,z in zip(keys,map(int,m[-1])): c[k]=z

im=re.findall(r"\[V45-INDEPENDENT-SETUP-SUMMARY\].*?duplicateSuppressed=(\d+)\s+uniqueExecuted=(\d+)\s+rescueAdmissions=(\d+)\s+transitionProofRejected=(\d+)\s+independentScaleCandidates=(\d+)",t)
ind={"duplicate_suppressed":0,"unique_executed_counter":0,"m1_rescue_admissions":0,"transition_proof_rejected":0,"independent_scale_candidates":0}
if im:
 for k,z in zip(ind.keys(),map(int,im[-1])): ind[k]=z

pipe_rx=re.compile(r"\[V45-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+armed=(\d+)\s+basketPlanned=(\d+)\s+leg0=(\d+)\s+leg1=(\d+)\s+leg2=(\d+)\s+leg3=(\d+)\s+basketClosed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
pipeline={}
for q in pipe_rx.finditer(t):
 pipeline[q.group(1)]={"detected":int(q.group(2)),"validated":int(q.group(3)),"routed":int(q.group(4)),"prz":int(q.group(5)),
 "confirming":int(q.group(6)),"armed":int(q.group(7)),"basket_planned":int(q.group(8)),"leg0":int(q.group(9)),
 "leg1":int(q.group(10)),"leg2":int(q.group(11)),"leg3":int(q.group(12)),"basket_closed":int(q.group(13)),
 "executed":int(q.group(14)),"expired":int(q.group(15)),"rejected":int(q.group(16)),"invalidated":int(q.group(17))}

clean_keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
"gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
summary_present=bool(m); clean=summary_present and all(c[k]==0 for k in clean_keys)
eq=d.get("equity",{})
unique_setups=len({x["setup"] for x in b})
duplicate_reentries=len(b)-unique_setups
out={"family":a.family,"window":a.window,"starting_balance":a.balance,"baskets":len(b),"unique_setups":unique_setups,
"duplicate_reentries":duplicate_reentries,"wins":sum(x>0 for x in v),"losses":sum(x<0 for x in v),"gross_profit":gp,"gross_loss":gl,
"pf":gp/gl if gl else (999 if gp else 0),"net":sum(v),"expectancy":sum(v)/len(v) if v else 0,
"win_rate":sum(x>0 for x in v)/len(v) if v else 0,"frequency":len(b)/a.years,
"unique_frequency":unique_setups/a.years,"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),
"engineering_clean":clean,"summary_present":summary_present,"broker_profile_present":"[V45-BROKER-PROFILE]" in t,
"mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,
"basket_outcomes":b,"pattern_pipeline":pipeline,**ind,**c}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
