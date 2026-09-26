#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics,collections
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","mode"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True); ap.add_argument("--spread",type=float,default=1.0)
a=ap.parse_args(); d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")
rx=re.compile(r"\[V67-BASKET-CLOSED\].*?cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
b=[{"cid":m.group(1),"setup":m.group(2),"pattern":m.group(3),"subtype":m.group(4),"route":m.group(5),"direction":m.group(6),"mfe":float(m.group(7)),"mae":float(m.group(8)),"r":float(m.group(9)),"net":float(m.group(10)),"reason":m.group(11)} for m in rx.finditer(t)]
vals=[x["net"] for x in b]; gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
pat=(r"\[V67-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+orphanPendingOrders=(\d+)\s+stopWideningViolations=(\d+)\s+gapThroughInvalidations=(\d+)\s+gapThroughSurvivors=(\d+)\s+unprotectedSurvivors=(\d+)\s+postFillProtectionFailures=(\d+)\s+actualBasketRiskViolations=(\d+)\s+executionStateViolations=(\d+)\s+virtualGridFills=(\d+)\s+microModeBaskets=(\d+)\s+capitalRejectedBaskets=(\d+)\s+marginRiskViolations=(\d+)")
m=re.findall(pat,t)
keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_invalidations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","virtual_grid_fills","micro_mode_baskets","capital_rejected_baskets","margin_risk_violations"]
c={k:0 for k in keys}
if m:
 for k,z in zip(keys,map(int,m[-1])): c[k]=z
sem=re.findall(r"\[V67-COMMERCIAL-SEMANTICS\].*?preventedRiskRejections=(\d+)\s+actualBasketRiskViolations=(\d+)\s+familyRouteRejected=(\d+)\s+abcdStandaloneSuppressed=(\d+)\s+familyCompletionRejected=(\d+)",t)
semv={"prevented_risk_rejections":0,"family_route_rejected":0,"abcd_standalone_suppressed":0,"family_completion_rejected":0}
if sem:
 z=sem[-1]; semv={"prevented_risk_rejections":int(z[0]),"family_route_rejected":int(z[2]),"abcd_standalone_suppressed":int(z[3]),"family_completion_rejected":int(z[4])}
def group(field):
 g=collections.defaultdict(list)
 for x in b:g[x[field]].append(x)
 out={}
 for k,q in g.items():
  v=[x["net"] for x in q]; gpp=sum(x for x in v if x>0); gll=abs(sum(x for x in v if x<0))
  out[k]={"trades":len(q),"net":sum(v),"pf":gpp/gll if gll else (999 if gpp else 0),"expectancy":sum(v)/len(v),"win_rate":sum(x>0 for x in v)/len(v)}
 return out
family=group("pattern"); route=group("route")
family_route={}
g=collections.defaultdict(list)
for x in b:g[(x["pattern"],x["route"])].append(x)
for (p,r),q in g.items():
 v=[x["net"] for x in q]; gpp=sum(x for x in v if x>0); gll=abs(sum(x for x in v if x<0))
 family_route[p+"|"+r]={"trades":len(q),"net":sum(v),"pf":gpp/gll if gll else (999 if gpp else 0),"expectancy":sum(v)/len(v),"win_rate":sum(x>0 for x in v)/len(v)}
pipe_rx=re.compile(r"\[V67-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+nativeTemporalPass=(\d+)\s+armed=(\d+)\s+slotBlocked=(\d+)\s+parked=(\d+)\s+revalidated=(\d+)\s+revalidationRejected=(\d+)\s+basketPlanned=(\d+)\s+leg0=(\d+)\s+leg1=(\d+)\s+leg2=(\d+)\s+leg3=(\d+)\s+basketClosed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
pipeline={}
for q in pipe_rx.finditer(t):
 names=["detected","validated","routed","prz","confirming","native_temporal_pass","armed","slot_blocked","parked","revalidated","revalidation_rejected","basket_planned","leg0","leg1","leg2","leg3","basket_closed","executed","expired","rejected","invalidated"]
 pipeline[q.group(1)]={k:v for k,v in zip(names,map(int,q.groups()[1:]))}
clean_keys=["execution_errors","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
clean=bool(m) and all(c[k]==0 for k in clean_keys)
eq=d.get("equity",{}); wins=sorted(x["r"] for x in b if x["r"]>0)
def pct(v,p):
 if not v:return 0
 z=(len(v)-1)*p; lo=int(z); hi=min(len(v)-1,lo+1); return v[lo]+(v[hi]-v[lo])*(z-lo)
out={"version":"HarmonyBot V67","mode":a.mode,"window":a.window,"starting_balance":a.balance,"spread":a.spread,"baskets":len(b),"unique_setups":len({x["setup"] for x in b}),"duplicate_reentries":len(b)-len({x["setup"] for x in b}),"wins":sum(x>0 for x in vals),"losses":sum(x<0 for x in vals),"gross_profit":gp,"gross_loss":gl,"pf":gp/gl if gl else (999 if gp else 0),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,"win_rate":sum(x>0 for x in vals)/len(vals) if vals else 0,"frequency":len(b)/a.years,"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),"engineering_clean":clean,"summary_present":bool(m),"mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,"p95_winner_r":pct(wins,.95),"max_winner_r":max(wins) if wins else 0,"family_performance":family,"route_performance":route,"family_route_performance":family_route,"pattern_pipeline":pipeline,"basket_outcomes":b,**semv,**c}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
