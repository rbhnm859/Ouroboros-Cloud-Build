#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics,collections
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","variant"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
ap.add_argument("--spread",type=float,default=1.0); ap.add_argument("--data-sha",default="")
a=ap.parse_args(); d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")
basket_rx=re.compile(r"\[V51-BASKET-CLOSED\].*?cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
b=[{"cid":m.group(1),"setup":m.group(2),"pattern":m.group(3),"subtype":m.group(4),"route":m.group(5),"direction":m.group(6),"mfe":float(m.group(7)),"mae":float(m.group(8)),"r":float(m.group(9)),"net":float(m.group(10)),"reason":m.group(11)} for m in basket_rx.finditer(t)]
vals=[x["net"] for x in b]; gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
sum_rx=re.compile(r"\[V51-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+orphanPendingOrders=(\d+)\s+stopWideningViolations=(\d+)\s+gapThroughInvalidations=(\d+)\s+gapThroughSurvivors=(\d+)\s+unprotectedSurvivors=(\d+)\s+postFillProtectionFailures=(\d+)\s+actualBasketRiskViolations=(\d+)\s+executionStateViolations=(\d+)\s+virtualGridFills=(\d+)\s+microModeBaskets=(\d+)\s+capitalRejectedBaskets=(\d+)\s+marginRiskViolations=(\d+)")
sm=sum_rx.findall(t)
keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_invalidations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","virtual_grid_fills","micro_mode_baskets","capital_rejected_baskets","margin_risk_violations"]
c={k:0 for k in keys}
if sm:
 for k,z in zip(keys,map(int,sm[-1])): c[k]=z
pipe_rx=re.compile(r"\[V51-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+nativeTemporalPass=(\d+)\s+armed=(\d+)\s+slotBlocked=(\d+)\s+parked=(\d+)\s+revalidated=(\d+)\s+revalidationRejected=(\d+)\s+basketPlanned=(\d+)\s+leg0=(\d+)\s+leg1=(\d+)\s+leg2=(\d+)\s+leg3=(\d+)\s+basketClosed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
pnames=["detected","validated","routed","prz","confirming","native_temporal_pass","armed","slot_blocked","parked","revalidated","revalidation_rejected","basket_planned","leg0","leg1","leg2","leg3","basket_closed","executed","expired","rejected","invalidated"]
pipeline={}
for m in pipe_rx.finditer(t): pipeline[m.group(1)]={k:v for k,v in zip(pnames,map(int,m.groups()[1:]))}
econ_rx=re.compile(r"\[V63-ECONOMIC-ATTRIBUTION\].*?basket=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+capture=([-0-9.]+)\s+timeToMfeMin=([-0-9.]+)\s+timeToMaeMin=([-0-9.]+)")
econ=[{"basket":m.group(1),"setup":m.group(2),"pattern":m.group(3),"route":m.group(4),"mfe":float(m.group(5)),"mae":float(m.group(6)),"r":float(m.group(7)),"capture":float(m.group(8)),"time_to_mfe":float(m.group(9)),"time_to_mae":float(m.group(10))} for m in econ_rx.finditer(t)]
leg_rx=re.compile(r"\[V63-LEG-ECON\].*?basket=(\S+)\s+setup=(\S+)\s+leg=L(\d+)\s+fraction=([-0-9.]+)\s+weight=([-0-9.]+)\s+runner=(\S+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)")
legs=[{"basket":m.group(1),"setup":m.group(2),"leg":int(m.group(3)),"fraction":float(m.group(4)),"weight":float(m.group(5)),"runner":m.group(6).lower()=="true","mfe":float(m.group(7)),"mae":float(m.group(8)),"r":float(m.group(9)),"net":float(m.group(10))} for m in leg_rx.finditer(t)]
g={}
for x in legs:g.setdefault("L%d|f%.3f|runner=%s"%(x["leg"],x["fraction"],x["runner"]),[]).append(x)
leg_economics={k:{"n":len(q),"net":sum(x["net"] for x in q),"mean_r":statistics.mean(x["r"] for x in q),"mean_mfe":statistics.mean(x["mfe"] for x in q),"mean_mae":statistics.mean(x["mae"] for x in q)} for k,q in g.items()}
rej=collections.Counter(); pas=collections.Counter()
for m in re.finditer(r"\[V63-GATE-REJECT\].*?stage=(\S+)\s+reason=(\S+)",t):rej[m.group(1)]+=1
for m in re.finditer(r"\[V63-GATE-PASS\].*?stage=(\S+)\s+reason=(\S+)",t):pas[m.group(1)]+=1
gate_telemetry={k:{"pass":pas[k],"reject":rej[k],"rate":pas[k]/(pas[k]+rej[k]) if pas[k]+rej[k] else None} for k in sorted(set(pas)|set(rej))}
last={}
for m in re.finditer(r"\[V51-EVENT\].*?cid=(\S+).*?reason=REJECTED:(\S+)",t):last[m.group(1)]=m.group(2)
frx=re.compile(r"\[V51-ENTRY-ANCHOR-FORENSICS\]\s+cid=(\S+)\s+setup=(\S+)\s+pattern=(\S+).*?completionMfeR=([-0-9.]+)\s+completionMaeR=([-0-9.]+)")
coh=collections.defaultdict(list)
for m in frx.finditer(t):
 if m.group(1) in last:coh[last[m.group(1)]].append((float(m.group(4)),float(m.group(5))))
rejected_cohort_quality={r:{"n":len(q),"mean_shadow_mfe_r":statistics.mean(z[0] for z in q),"mean_shadow_mae_r":statistics.mean(z[1] for z in q),"share_mfe_ge_1r":sum(z[0]>=1 for z in q)/len(q)} for r,q in coh.items() if q}
v63rx=re.findall(r"\[V63-SUMMARY\].*?cohortRecovered=(\d+)\s+occupancyReleased=(\d+)\s+runnerAssigned=(\d+)\s+runnerFilled=(\d+)\s+runnerClosed=(\d+)\s+runnerSurvivedCanonical=(\d+)\s+conditionalArmed=(\d+)\s+conditionalRejected=(\d+)",t)
v63={"cohort_recovered":0,"occupancy_released":0,"runner_assigned":0,"runner_filled":0,"runner_closed":0,"runner_survived_canonical":0,"conditional_armed":0,"conditional_rejected":0}
if v63rx:
 for k,z in zip(v63,map(int,v63rx[-1])):v63[k]=z
cell_rx=re.compile(r"\[V63-CELL-OUTCOME\]\s+setup=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+regime=(\S+)\s+policy=(\S+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)")
cells=[{"setup":m.group(1),"pattern":m.group(2),"route":m.group(3),"regime":m.group(4),"policy":m.group(5),"r":float(m.group(6)),"net":float(m.group(7)),"mfe":float(m.group(8)),"mae":float(m.group(9))} for m in cell_rx.finditer(t)]
clean=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
eq=d.get("equity",{}); unique=len({x["setup"] for x in b}); summary=bool(sm)
out={"variant":a.variant,"window":a.window,"starting_balance":a.balance,"spread":a.spread,"data_snapshot_sha":a.data_sha,
"baskets":len(b),"unique_setups":unique,"duplicate_reentries":len(b)-unique,"wins":sum(x>0 for x in vals),"losses":sum(x<0 for x in vals),
"gross_profit":gp,"gross_loss":gl,"pf":gp/gl if gl else (999 if gp else 0),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,
"win_rate":sum(x>0 for x in vals)/len(vals) if vals else 0,"frequency":len(b)/a.years,"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),
"engineering_clean":summary and all(c[k]==0 for k in clean),"summary_present":summary,"broker_profile_present":"[V51-BROKER-PROFILE]" in t,
"mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,
"mean_capture_ratio":statistics.mean([x["capture"] for x in econ]) if econ else 0,"economic_attribution":econ,"leg_economics":leg_economics,
"gate_telemetry":gate_telemetry,"rejected_cohort_quality":rejected_cohort_quality,"v63_telemetry":v63,"basket_outcomes":b,"pattern_pipeline":pipeline,"cell_outcomes":cells,**c}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
