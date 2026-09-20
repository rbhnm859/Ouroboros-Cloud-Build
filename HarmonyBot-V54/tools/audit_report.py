#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","family"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True); ap.add_argument("--data-sha",default="")
a=ap.parse_args(); d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")

rx=re.compile(r"\[V54-BASKET-CLOSED\].*?cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
b=[]
for m in rx.finditer(t):
 b.append({"cid":m.group(1),"setup":m.group(2),"pattern":m.group(3),"subtype":m.group(4),"route":m.group(5),"direction":m.group(6),
           "mfe":float(m.group(7)),"mae":float(m.group(8)),"r":float(m.group(9)),"net":float(m.group(10)),"reason":m.group(11)})
v=[x["net"] for x in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))

pat=(r"\[V54-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+"
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

thr=re.findall(r"\[V54-THROUGHPUT-SUMMARY\].*?slotBlocked=(\d+)\s+parked=(\d+)\s+revalidated=(\d+)\s+revalidationRejected=(\d+)\s+recoveredExecutions=(\d+)\s+nativeTemporalPass=(\d+)\s+hardLifetimeExpired=(\d+)\s+decayRejected=(\d+)\s+avgSlotWaitMin=([-0-9.]+)\s+medianSlotWaitMin=([-0-9.]+)\s+p90SlotWaitMin=([-0-9.]+)\s+avgBasketOccupancyMin=([-0-9.]+)\s+missedPositive=(\d+)\s+avoidedNegative=(\d+)",t)
tn=["slot_blocked","parked","revalidated","revalidation_rejected","parked_recovered_executions","native_temporal_pass","hard_lifetime_expired","decay_rejected","avg_slot_wait_min","median_slot_wait_min","p90_slot_wait_min","avg_basket_occupancy_min","missed_positive_setups","avoided_negative_setups"]
tv={k:0 for k in tn}
if thr:
 vals=list(thr[-1])
 for k,z in zip(tn,vals):
  tv[k]=float(z) if k in ["avg_slot_wait_min","median_slot_wait_min","p90_slot_wait_min","avg_basket_occupancy_min"] else int(z)

pipe_rx=re.compile(r"\[V54-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+nativeTemporalPass=(\d+)\s+armed=(\d+)\s+slotBlocked=(\d+)\s+parked=(\d+)\s+revalidated=(\d+)\s+revalidationRejected=(\d+)\s+basketPlanned=(\d+)\s+leg0=(\d+)\s+leg1=(\d+)\s+leg2=(\d+)\s+leg3=(\d+)\s+basketClosed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
pipeline={}
for q in pipe_rx.finditer(t):
 vals=list(map(int,q.groups()[1:]))
 names=["detected","validated","routed","prz","confirming","native_temporal_pass","armed","slot_blocked","parked","revalidated","revalidation_rejected","basket_planned","leg0","leg1","leg2","leg3","basket_closed","executed","expired","rejected","invalidated"]
 pipeline[q.group(1)]={k:v for k,v in zip(names,vals)}

evrx=re.compile(r"\[V54-EVENT\]\s+cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+scale=(\d+)\s+tf=(\S+)\s+dir=(\S+)\s+state=(\S+)\s+route=(\S+)\s+conflict=(\S+)\s+waitMin=([-0-9.]+)\s+reason=(.*)$",re.M)
events=[]
for q in evrx.finditer(t):
 events.append({"cid":q.group(1),"setup":q.group(2),"pattern":q.group(3),"subtype":q.group(4),"scale":int(q.group(5)),
                "tf":q.group(6),"direction":q.group(7),"state":q.group(8),"route":q.group(9),"conflict":q.group(10),
                "wait_min":float(q.group(11)),"reason":q.group(12).strip()})

oprx=re.compile(r"\[V54-OPPORTUNITY-LOSS\]\s+cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+scale=(\d+)\s+reason=(\S+)\s+shadowMfeR=([-0-9.]+)\s+shadowMaeR=([-0-9.]+)\s+missedPositive=(True|False)\s+avoidedNegative=(True|False)")
opp=[]
for q in oprx.finditer(t):
 opp.append({"cid":q.group(1),"setup":q.group(2),"pattern":q.group(3),"route":q.group(4),"scale":int(q.group(5)),
             "reason":q.group(6),"shadow_mfe_r":float(q.group(7)),"shadow_mae_r":float(q.group(8)),
             "missed_positive":q.group(9)=="True","avoided_negative":q.group(10)=="True"})

sorx=re.compile(r"\[V54-SLOT-OCCUPANCY\].*?pattern=(.*?)\s+route=(\S+)\s+occupancyMinutes=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)")
slots=[{"pattern":q.group(1),"route":q.group(2),"occupancy_minutes":float(q.group(3)),"realized_r":float(q.group(4)),"net":float(q.group(5))} for q in sorx.finditer(t)]

clean_keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors",
"unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
summary_present=bool(m); clean=summary_present and all(c[k]==0 for k in clean_keys)
eq=d.get("equity",{}); unique=len({x["setup"] for x in b})
out={"family":a.family,"window":a.window,"starting_balance":a.balance,"baskets":len(b),"unique_setups":unique,"duplicate_reentries":len(b)-unique,
"wins":sum(x>0 for x in v),"losses":sum(x<0 for x in v),"gross_profit":gp,"gross_loss":gl,"pf":gp/gl if gl else (999 if gp else 0),
"net":sum(v),"expectancy":sum(v)/len(v) if v else 0,"win_rate":sum(x>0 for x in v)/len(v) if v else 0,"frequency":len(b)/a.years,
"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),"engineering_clean":clean,"summary_present":summary_present,
"broker_profile_present":"[V54-BROKER-PROFILE]" in t,"data_snapshot_sha":a.data_sha.strip(),"mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,
"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,"basket_outcomes":b,"pattern_pipeline":pipeline,
"events":events,"opportunity_loss":opp,"slot_occupancy":slots,**tv,**c}
anchor_rx=re.compile(r"\[V54-ENTRY-ANCHOR-FORENSICS\]\s+cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+scale=(\d+)\s+completion=([-0-9.]+)\s+confirm=([-0-9.]+)\s+retest=([-0-9.]+)\s+completionMfeR=([-0-9.]+)\s+completionMaeR=([-0-9.]+)\s+confirmMfeR=([-0-9.]+)\s+confirmMaeR=([-0-9.]+)\s+retestMfeR=([-0-9.]+)\s+retestMaeR=([-0-9.]+)")
anchors=[]
for q in anchor_rx.finditer(t):
 anchors.append({"cid":q.group(1),"setup":q.group(2),"pattern":q.group(3),"route":q.group(4),"scale":int(q.group(5)),
 "completion_price":float(q.group(6)),"confirm_price":float(q.group(7)),"retest_price":float(q.group(8)),
 "completion_mfe_r":float(q.group(9)),"completion_mae_r":float(q.group(10)),"confirm_mfe_r":float(q.group(11)),"confirm_mae_r":float(q.group(12)),
 "retest_mfe_r":float(q.group(13)),"retest_mae_r":float(q.group(14))})
out["entry_anchor_forensics"]=anchors
truth_rx=re.compile(r"\[V54-DETECTOR-TRUTH\]\s+pattern=(.*?)\s+stage=(\S+)\s+count=(\d+)")
truth={}
for q in truth_rx.finditer(t):
 truth.setdefault(q.group(1),{})[q.group(2)]=int(q.group(3))
out["detector_truth"]=truth
conv_rx=re.compile(r"\[V54-CONVERSION-TRUTH\]\s+pattern=(.*?)\s+stage=(\S+)\s+count=(\d+)")
conv={}
for q in conv_rx.finditer(t): conv.setdefault(q.group(1),{})[q.group(2)]=int(q.group(3))
out["conversion_truth"]=conv
gmeta_rx=re.compile(r"\[V54-BASKET-CLOSED\].*?cid=(\S+).*?lane=(\S+)\s+econQ=([-0-9.]+).*?plannedLegs=(\d+)\s+filledLegs=(\d+).*?entryImprovePips=([-0-9.]+)")
gmeta={q.group(1):{"alpha_lane":q.group(2),"economic_quality":float(q.group(3)),"planned_legs":int(q.group(4)),"filled_legs":int(q.group(5)),"entry_improve_pips":float(q.group(6))} for q in gmeta_rx.finditer(t)}
for row in out["basket_outcomes"]: row.update(gmeta.get(row["cid"],{"alpha_lane":"LEGACY","economic_quality":0.0,"planned_legs":1,"filled_legs":1,"entry_improve_pips":0.0}))
out["grid_execution_enabled"]="[V54-GRID-CAUSAL-MODE] enabled=True" in t
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))