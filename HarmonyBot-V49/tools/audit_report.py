#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","family"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
a=ap.parse_args(); d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")

rx=re.compile(r"\[V49-BASKET-CLOSED\].*?cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(.*?)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
b=[]
for m in rx.finditer(t):
 b.append({"cid":m.group(1),"setup":m.group(2),"pattern":m.group(3),"subtype":m.group(4),"route":m.group(5),"direction":m.group(6),
           "mfe":float(m.group(7)),"mae":float(m.group(8)),"r":float(m.group(9)),"net":float(m.group(10)),"reason":m.group(11)})
v=[x["net"] for x in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))

pat=(r"\[V49-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+"
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

pipe_rx=re.compile(r"\[V49-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+evidenceSeen=(\d+)\s+nativePass=(\d+)\s+cfPositive=(\d+)\s+cfNegative=(\d+)\s+nativeTemporalPass=(\d+)\s+armed=(\d+)\s+slotBlocked=(\d+)\s+parked=(\d+)\s+revalidated=(\d+)\s+revalidationRejected=(\d+)\s+basketPlanned=(\d+)\s+leg0=(\d+)\s+leg1=(\d+)\s+leg2=(\d+)\s+leg3=(\d+)\s+basketClosed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
pipeline={}
pnames=["detected","validated","routed","prz","confirming","evidence_seen","native_pass","cf_positive","cf_negative","native_temporal_pass","armed","slot_blocked","parked","revalidated","revalidation_rejected","basket_planned","leg0","leg1","leg2","leg3","basket_closed","executed","expired","rejected","invalidated"]
for q in pipe_rx.finditer(t):
 pipeline[q.group(1)]={k:z for k,z in zip(pnames,map(int,q.groups()[1:]))}

evrx=re.compile(r"\[V49-EVENT\]\s+cid=(\S+)\s+setup=(\S*)\s+pattern=(.*?)\s+subtype=(.*?)\s+scale=(\d+)\s+tf=(\S+)\s+dir=(\S+)\s+state=(\S+)\s+route=(\S+)\s+conflict=(\S+)\s+waitMin=([-0-9.]+)\s+reason=(.*)$",re.M)
events=[]
for q in evrx.finditer(t):
 events.append({"cid":q.group(1),"setup":q.group(2),"pattern":q.group(3),"subtype":q.group(4),"scale":int(q.group(5)),
                "tf":q.group(6),"direction":q.group(7),"state":q.group(8),"route":q.group(9),"conflict":q.group(10),
                "wait_min":float(q.group(11)),"reason":q.group(12).strip()})

cf_rx=re.compile(
 r"\[V49-CF\]\s+cid=(\S+)\s+setup=(\S*)\s+pattern=(.*?)\s+subtype=(.*?)\s+route=(\S+)\s+scale=(\d+)\s+dir=(\S+)\s+terminal=(\S+)\s+bars=(\d+)\s+legacyBest=([-0-9.]+)\s+nativePass=(True|False)\s+nativePassUtc=(\S+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+class=(\S+)\s+oneRUtc=(\S+)\s+twoRUtc=(\S+)\s+slUtc=(\S+)\s+target1Utc=(\S+)\s+target2Utc=(\S+)\s+timeTo1RMin=([-0-9.]+)\s+timeTo2RMin=([-0-9.]+)\s+directionalUtc=(\S+)\s+reclaimUtc=(\S+)\s+bos1Utc=(\S+)\s+bos2Utc=(\S+)\s+rejectionUtc=(\S+)\s+failedExtensionUtc=(\S+)\s+sweepUtc=(\S+)\s+displacementUtc=(\S+)\s+closeBackInsideUtc=(\S+)")
cf_start_count=len(re.findall(r"\[V49-CF-START\]",t))
cf=[]
for q in cf_rx.finditer(t):
 g=q.groups()
 cf.append({"cid":g[0],"setup":g[1],"pattern":g[2],"subtype":g[3],"route":g[4],"scale":int(g[5]),"direction":g[6],"terminal":g[7],
 "bars":int(g[8]),"legacy_best":float(g[9]),"native_pass":g[10]=="True","native_pass_utc":g[11],
 "mfe_r":float(g[12]),"mae_r":float(g[13]),"classification":g[14],"one_r_utc":g[15],"two_r_utc":g[16],"sl_utc":g[17],
 "target1_utc":g[18],"target2_utc":g[19],"time_to_1r_min":float(g[20]),"time_to_2r_min":float(g[21]),
 "directional_utc":g[22],"reclaim_utc":g[23],"bos1_utc":g[24],"bos2_utc":g[25],"rejection_utc":g[26],
 "failed_extension_utc":g[27],"sweep_utc":g[28],"displacement_utc":g[29],"close_back_inside_utc":g[30]})

bar_rx=re.compile(r"\[V49-CONFIRM-BAR\]\s+cid=(\S+)\s+setup=(\S*)\s+time=(\S+)\s+pattern=(.*?)\s+subtype=(.*?)\s+route=(\S+)\s+scale=(\d+)\s+dir=(\S+)\s+bar=(\d+)\s+legacy=([-0-9.]+)\s+directional=(True|False)\s+reclaim=(True|False)\s+bos1=(True|False)\s+bos2=(True|False)\s+rejection=(True|False)\s+failedExtension=(True|False)\s+sweep=(True|False)\s+displacement=(True|False)\s+closeBackInside=(True|False)\s+nativePass=(True|False)")
confirm_bars=[]
for q in bar_rx.finditer(t):
 g=q.groups()
 confirm_bars.append({"cid":g[0],"setup":g[1],"time":g[2],"pattern":g[3],"subtype":g[4],"route":g[5],"scale":int(g[6]),"direction":g[7],
 "bar":int(g[8]),"legacy":float(g[9]),"directional":g[10]=="True","reclaim":g[11]=="True","bos1":g[12]=="True","bos2":g[13]=="True",
 "rejection":g[14]=="True","failed_extension":g[15]=="True","sweep":g[16]=="True","displacement":g[17]=="True",
 "close_back_inside":g[18]=="True","native_pass":g[19]=="True"})

grid_rx=re.compile(r"\[V49-GRID-REJECT\]\s+cid=(\S+)\s+setup=(\S*)\s+pattern=(.*?)\s+subtype=(.*?)\s+route=(\S+)\s+scale=(\d+)\s+dir=(\S+)\s+reason=(\S+)\s+detail=(.*)$",re.M)
grid_rejections=[]
for q in grid_rx.finditer(t):
 g=q.groups()
 grid_rejections.append({"cid":g[0],"setup":g[1],"pattern":g[2],"subtype":g[3],"route":g[4],"scale":int(g[5]),"direction":g[6],"reason":g[7],"detail":g[8].strip()})

clean_keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors",
"unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
summary_present=bool(m); clean=summary_present and all(c[k]==0 for k in clean_keys)
eq=d.get("equity",{}); unique=len({x["setup"] for x in b})
out={"family":a.family,"window":a.window,"starting_balance":a.balance,"baskets":len(b),"unique_setups":unique,"duplicate_reentries":len(b)-unique,
"wins":sum(x>0 for x in v),"losses":sum(x<0 for x in v),"gross_profit":gp,"gross_loss":gl,"pf":gp/gl if gl else (999 if gp else 0),
"net":sum(v),"expectancy":sum(v)/len(v) if v else 0,"win_rate":sum(x>0 for x in v)/len(v) if v else 0,"frequency":len(b)/a.years,
"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),"engineering_clean":clean,"summary_present":summary_present,
"broker_profile_present":"[V49-BROKER-PROFILE]" in t,"mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,
"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,"basket_outcomes":b,"pattern_pipeline":pipeline,
"events":events,"counterfactual":cf,"counterfactual_start_count":cf_start_count,"counterfactual_logged_count":len(cf),
"confirm_bars":confirm_bars,"grid_rejections":grid_rejections,**c}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
