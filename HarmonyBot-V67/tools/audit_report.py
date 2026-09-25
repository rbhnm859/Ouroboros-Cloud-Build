#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics,collections
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","mode"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
ap.add_argument("--spread",type=float,default=1.0); ap.add_argument("--family-grid",default="true"); ap.add_argument("--data-sha",default="")
a=ap.parse_args()
d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")

basket_rx=re.compile(r"\[V67-BASKET-CLOSED\].*?cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
b=[{"cid":m.group(1),"setup":m.group(2),"pattern":m.group(3),"subtype":m.group(4),"route":m.group(5),"direction":m.group(6),
    "mfe":float(m.group(7)),"mae":float(m.group(8)),"r":float(m.group(9)),"net":float(m.group(10)),"reason":m.group(11)}
   for m in basket_rx.finditer(t)]
vals=[x["net"] for x in b]; rr=[x["r"] for x in b]; gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))

sum_rx=re.compile(r"\[V67-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+orphanPendingOrders=(\d+)\s+stopWideningViolations=(\d+)\s+gapThroughInvalidations=(\d+)\s+gapThroughSurvivors=(\d+)\s+unprotectedSurvivors=(\d+)\s+postFillProtectionFailures=(\d+)\s+actualBasketRiskViolations=(\d+)\s+executionStateViolations=(\d+)\s+virtualGridFills=(\d+)\s+microModeBaskets=(\d+)\s+capitalRejectedBaskets=(\d+)\s+marginRiskViolations=(\d+)")
sm=sum_rx.findall(t)
keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_invalidations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","virtual_grid_fills","micro_mode_baskets","capital_rejected_baskets","margin_risk_violations"]
c={k:0 for k in keys}
if sm:
    for k,z in zip(keys,map(int,sm[-1])): c[k]=z

pipe_rx=re.compile(r"\[V67-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+nativeTemporalPass=(\d+)\s+armed=(\d+)\s+slotBlocked=(\d+)\s+parked=(\d+)\s+revalidated=(\d+)\s+revalidationRejected=(\d+)\s+basketPlanned=(\d+)\s+leg0=(\d+)\s+leg1=(\d+)\s+leg2=(\d+)\s+leg3=(\d+)\s+basketClosed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
pipeline={}
for q in pipe_rx.finditer(t):
    vals2=list(map(int,q.groups()[1:]))
    names=["detected","validated","routed","prz","confirming","native_temporal_pass","armed","slot_blocked","parked","revalidated","revalidation_rejected","basket_planned","leg0","leg1","leg2","leg3","basket_closed","executed","expired","rejected","invalidated"]
    pipeline[q.group(1)]={k:v for k,v in zip(names,vals2)}

sel_rx=re.compile(r"\[V67-FAMILY-SELECTION\]\s+pattern=(.*?)\s+selected=(\d+)\s+executed=(\d+)")
family_selection={q.group(1):{"selected":int(q.group(2)),"executed":int(q.group(3))} for q in sel_rx.finditer(t)}
arch_rx=re.findall(r"\[V67-FAMILY-ARCH-SUMMARY\].*?broadAbcdShadowRejected=(\d+)\s+familyQualityRejected=(\d+)\s+familyRouteRejected=(\d+)",t)
arch={"broad_abcd_shadow_rejected":0,"family_quality_rejected":0,"family_route_rejected":0}
if arch_rx:
    z=arch_rx[-1]; arch={k:int(v) for k,v in zip(arch.keys(),z)}

truth_rx=re.compile(r"\[V67-DETECTOR-TRUTH\]\s+pattern=(.*?)\s+stage=(\S+)\s+count=(\d+)")
truth={}
for q in truth_rx.finditer(t): truth.setdefault(q.group(1),{})[q.group(2)]=int(q.group(3))

def summarize(key):
    g=collections.defaultdict(list)
    for x in b:g[x[key]].append(x)
    out={}
    for k,q in sorted(g.items()):
        v=[z["net"] for z in q]; gp2=sum(x for x in v if x>0); gl2=abs(sum(x for x in v if x<0))
        out[k]={"baskets":len(q),"net":sum(v),"pf":gp2/gl2 if gl2 else (999 if gp2 else 0),
                "expectancy":sum(v)/len(v) if v else 0,"win_rate":sum(x>0 for x in v)/len(v) if v else 0,
                "mean_r":statistics.mean([z["r"] for z in q]) if q else 0}
    return out
family=summarize("pattern"); route=summarize("route")
wins_r=sorted(x for x in rr if x>0)
def pct(v,p):
    if not v:return 0
    q=(len(v)-1)*p; lo=int(q); hi=min(len(v)-1,lo+1)
    return v[lo]+(v[hi]-v[lo])*(q-lo)

clean_keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
eq=d.get("equity",{}); summary_present=bool(sm)
clean=summary_present and all(c[k]==0 for k in clean_keys)
shares={k:(v["baskets"]/len(b) if b else 0) for k,v in family.items()}
positive_families=[k for k,v in family.items() if v["net"]>0 and v["pf"]>1]
non_abcd_net=sum(x["net"] for x in b if x["pattern"]!="AB=CD")
out={
 "version":"HarmonyBot V67","mode":a.mode,"window":a.window,"starting_balance":a.balance,"spread":a.spread,
 "family_grid":str(a.family_grid).lower()=="true","data_snapshot_sha":a.data_sha,
 "baskets":len(b),"unique_setups":len({x["setup"] for x in b}),"wins":sum(x>0 for x in vals),"losses":sum(x<0 for x in vals),
 "gross_profit":gp,"gross_loss":gl,"pf":gp/gl if gl else (999 if gp else 0),"net":sum(vals),
 "expectancy":sum(vals)/len(vals) if vals else 0,"win_rate":sum(x>0 for x in vals)/len(vals) if vals else 0,
 "frequency":len(b)/a.years,"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),
 "engineering_clean":clean,"summary_present":summary_present,"broker_profile_present":"[V67-BROKER-PROFILE]" in t,
 "mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,
 "mean_realized_r":statistics.mean(rr) if rr else 0,"p95_winner_r":pct(wins_r,.95),"max_winner_r":max(wins_r) if wins_r else 0,
 "family_performance":family,"route_performance":route,"family_share":shares,
 "max_family_share":max(shares.values()) if shares else 0,"positive_families":positive_families,
 "non_abcd_net":non_abcd_net,"pattern_pipeline":pipeline,"family_selection":family_selection,
 "detector_truth":truth,"v67_family_arch":arch,"basket_outcomes":b,**c
}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
