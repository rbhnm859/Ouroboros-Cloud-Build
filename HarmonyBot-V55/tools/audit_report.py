#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","family"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
ap.add_argument("--data-sha",default="")
a=ap.parse_args(); d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")

rx=re.compile(r"\[V55-BASKET-CLOSED\].*?cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+route=(\S+)\s+lane=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
b=[]
for m in rx.finditer(t):
 b.append({"cid":m.group(1),"setup":m.group(2),"pattern":m.group(3),"subtype":m.group(4),"route":m.group(5),"lane":m.group(6),
           "direction":m.group(7),"mfe":float(m.group(8)),"mae":float(m.group(9)),"r":float(m.group(10)),"net":float(m.group(11)),"reason":m.group(12)})
v=[x["net"] for x in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))

pat=(r"\[V55-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+"
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

pipe_rx=re.compile(r"\[V55-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+nativeTemporalPass=(\d+)\s+armed=(\d+)\s+slotBlocked=(\d+)\s+parked=(\d+)\s+revalidated=(\d+)\s+revalidationRejected=(\d+)\s+basketPlanned=(\d+)\s+leg0=(\d+)\s+leg1=(\d+)\s+leg2=(\d+)\s+leg3=(\d+)\s+basketClosed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
pipeline={}
for q in pipe_rx.finditer(t):
 vals=list(map(int,q.groups()[1:])); names=["detected","validated","routed","prz","confirming","native_temporal_pass","armed","slot_blocked","parked","revalidated","revalidation_rejected","basket_planned","leg0","leg1","leg2","leg3","basket_closed","executed","expired","rejected","invalidated"]
 pipeline[q.group(1)]={k:v for k,v in zip(names,vals)}

rs=re.findall(r"\[V55-RESEARCH-SUMMARY\].*?detected=(\d+)\s+przTouched=(\d+)\s+confirmed=(\d+)\s+economicEvaluated=(\d+)\s+terminal=(\d+)\s+expansionAdmitted=(\d+)\s+expansionRejected=(\d+)\s+expansionDeferredForCore=(\d+)\s+coreSignalsDuringExpansionSlot=(\d+)",t)
rnames=["research_detected","research_prz_touched","research_confirmed","research_economic_evaluated","research_terminal","expansion_admitted","expansion_rejected","expansion_deferred_for_core","core_signals_during_expansion_slot"]
rv={k:0 for k in rnames}
if rs:
 for k,z in zip(rnames,map(int,rs[-1])):rv[k]=z

rrx=re.compile(r"\[V55-RESEARCH\]\s+rid=(\S+)\s+hypothesis=(\S+)\s+geometry=(\S+)\s+pattern=(.*?)\s+scale=(\d+)\s+state=(\S+)\s+strictQuality=(True|False)\s+strictRoute=(True|False)\s+strictConfirm=(True|False)\s+coreEquivalent=(True|False)\s+shadowRoute=(\S+)\s+netRR=([-0-9.]+)\s+gridRR=([-0-9.]+)\s+manifest=(True|False)\s+promoted=(True|False)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+outcomeR=([-0-9.]+)\s+reason=(.*)$",re.M)
research=[]
for q in rrx.finditer(t):
 research.append({"rid":q.group(1),"hypothesis":q.group(2),"geometry":q.group(3),"pattern":q.group(4),"scale":int(q.group(5)),"state":q.group(6),
 "strict_quality":q.group(7)=="True","strict_route":q.group(8)=="True","strict_confirm":q.group(9)=="True","core_equivalent":q.group(10)=="True",
 "shadow_route":q.group(11),"net_rr":float(q.group(12)),"grid_rr":float(q.group(13)),"manifest":q.group(14)=="True","promoted":q.group(15)=="True",
 "mfe_r":float(q.group(16)),"mae_r":float(q.group(17)),"outcome_r":float(q.group(18)),"reason":q.group(19).strip()})

drx=re.compile(r"\[V55-RESEARCH-DETECTOR\]\s+pattern=(.*?)\s+stage=(\S+)\s+count=(\d+)")
det={}
for q in drx.finditer(t):det.setdefault(q.group(1),{})[q.group(2)]=int(q.group(3))

clean_keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
summary_present=bool(m); clean=summary_present and all(c[k]==0 for k in clean_keys)
eq=d.get("equity",{}); unique=len({x["setup"] for x in b})
out={"family":a.family,"window":a.window,"data_snapshot_sha":a.data_sha,"starting_balance":a.balance,"baskets":len(b),"unique_setups":unique,"duplicate_reentries":len(b)-unique,
"wins":sum(x>0 for x in v),"losses":sum(x<0 for x in v),"gross_profit":gp,"gross_loss":gl,"pf":gp/gl if gl else (999 if gp else 0),
"net":sum(v),"expectancy":sum(v)/len(v) if v else 0,"win_rate":sum(x>0 for x in v)/len(v) if v else 0,"frequency":len(b)/a.years,
"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),"engineering_clean":clean,"summary_present":summary_present,
"broker_profile_present":"[V55-BROKER-PROFILE]" in t,"mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,
"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,"basket_outcomes":b,"pattern_pipeline":pipeline,"research_events":research,"research_detector_truth":det,**rv,**c}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
