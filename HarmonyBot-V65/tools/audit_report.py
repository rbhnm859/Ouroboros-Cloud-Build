#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics,collections
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","mode"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
ap.add_argument("--spread",type=float,default=1.0); ap.add_argument("--data-sha",default="")
a=ap.parse_args(); d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")

basket_rx=re.compile(r"\[V51-BASKET-CLOSED\].*?cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
b=[{"cid":m.group(1),"setup":m.group(2),"pattern":m.group(3),"subtype":m.group(4),"route":m.group(5),"direction":m.group(6),
    "mfe":float(m.group(7)),"mae":float(m.group(8)),"r":float(m.group(9)),"net":float(m.group(10)),"reason":m.group(11)}
   for m in basket_rx.finditer(t)]
vals=[x["net"] for x in b]; rr=[x["r"] for x in b]; gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))

sum_rx=re.compile(r"\[V65-RISK-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+orphanPendingOrders=(\d+)\s+stopWideningViolations=(\d+)\s+gapThroughInvalidations=(\d+)\s+gapThroughSurvivors=(\d+)\s+unprotectedSurvivors=(\d+)\s+postFillProtectionFailures=(\d+)\s+actualBasketRiskViolations=(\d+)\s+executionStateViolations=(\d+)\s+virtualGridFills=(\d+)\s+microModeBaskets=(\d+)\s+capitalRejectedBaskets=(\d+)\s+marginRiskViolations=(\d+)")
sm=sum_rx.findall(t)
keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_invalidations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","virtual_grid_fills","micro_mode_baskets","capital_rejected_baskets","margin_risk_violations"]
c={k:0 for k in keys}
if sm:
    for k,z in zip(keys,map(int,sm[-1])): c[k]=z

econ_rx=re.compile(r"\[V65-ECONOMIC-ATTRIBUTION\].*?basket=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+capture=([-0-9.]+)\s+timeToMfeMin=([-0-9.]+)\s+timeToMaeMin=([-0-9.]+)")
econ=[{"basket":m.group(1),"setup":m.group(2),"pattern":m.group(3),"route":m.group(4),"mfe":float(m.group(5)),"mae":float(m.group(6)),
       "r":float(m.group(7)),"capture":float(m.group(8)),"time_to_mfe":float(m.group(9)),"time_to_mae":float(m.group(10))}
      for m in econ_rx.finditer(t)]

leg_rx=re.compile(r"\[V65-LEG-ECON\].*?basket=(\S+)\s+setup=(\S+)\s+leg=L(\d+)\s+fraction=([-0-9.]+)\s+weight=([-0-9.]+)\s+runner=(\S+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)")
legs=[{"basket":m.group(1),"setup":m.group(2),"leg":int(m.group(3)),"fraction":float(m.group(4)),"weight":float(m.group(5)),
       "runner":m.group(6).lower()=="true","mfe":float(m.group(7)),"mae":float(m.group(8)),"r":float(m.group(9)),"net":float(m.group(10))}
      for m in leg_rx.finditer(t)]
lg=collections.defaultdict(list)
for x in legs: lg["L%d|f%.3f|runner=%s"%(x["leg"],x["fraction"],x["runner"])].append(x)
leg_economics={k:{"n":len(q),"net":sum(x["net"] for x in q),"mean_r":statistics.mean(x["r"] for x in q),
                  "mean_mfe_r":statistics.mean(x["mfe"] for x in q),"mean_mae_r":statistics.mean(x["mae"] for x in q)}
               for k,q in lg.items()}

prod_rx=re.findall(r"\[V65-PRODUCT-SUMMARY\].*?mode=(\S+)\s+thesisCompleted=(\d+)\s+thesisWindowRejected=(\d+)\s+thesisRouteProofRejected=(\d+)\s+runnerAssigned=(\d+)\s+runnerFilled=(\d+)\s+runnerClosed=(\d+)\s+runnerSurvivedCanonical=(\d+)\s+conditionalArmed=(\d+)\s+conditionalRejected=(\d+)",t)
product={"mode":a.mode,"thesis_completed":0,"thesis_window_rejected":0,"thesis_route_proof_rejected":0,"runner_assigned":0,"runner_filled":0,"runner_closed":0,"runner_survived_canonical":0,"conditional_armed":0,"conditional_rejected":0}
if prod_rx:
    z=prod_rx[-1]
    ks=list(product); vals2=[z[0]]+list(map(int,z[1:]))
    product=dict(zip(ks,vals2))

def summarize(key):
    g=collections.defaultdict(list)
    for x in b:g[x[key]].append(x)
    return {k:{"baskets":len(q),"net":sum(x["net"] for x in q),"mean_r":statistics.mean(x["r"] for x in q),
               "win_rate":sum(x["net"]>0 for x in q)/len(q),"mean_mfe_r":statistics.mean(x["mfe"] for x in q),"mean_mae_r":statistics.mean(x["mae"] for x in q)}
            for k,q in sorted(g.items())}

wins_r=sorted(x for x in rr if x>0)
def pct(v,p):
    if not v:return 0
    q=(len(v)-1)*p; lo=int(q); hi=min(len(v)-1,lo+1); return v[lo]+(v[hi]-v[lo])*(q-lo)
clean=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
eq=d.get("equity",{}); unique=len({x["setup"] for x in b}); summary=bool(sm)
out={"version":"HarmonyBot V65","mode":a.mode,"window":a.window,"starting_balance":a.balance,"spread":a.spread,"data_snapshot_sha":a.data_sha,
 "baskets":len(b),"unique_setups":unique,"duplicate_reentries":len(b)-unique,
 "wins":sum(x>0 for x in vals),"losses":sum(x<0 for x in vals),"gross_profit":gp,"gross_loss":gl,
 "pf":gp/gl if gl else (999 if gp else 0),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,
 "win_rate":sum(x>0 for x in vals)/len(vals) if vals else 0,"frequency":len(b)/a.years,
 "max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),
 "engineering_clean":summary and all(c[k]==0 for k in clean),"summary_present":summary,"broker_profile_present":"[V51-BROKER-PROFILE]" in t,
 "mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,
 "mean_realized_r":statistics.mean(rr) if rr else 0,"p95_winner_r":pct(wins_r,.95),"max_winner_r":max(wins_r) if wins_r else 0,
 "mean_capture_ratio":statistics.mean([x["capture"] for x in econ]) if econ else 0,
 "product_execution":product,"leg_economics":leg_economics,"family_performance":summarize("pattern"),"route_performance":summarize("route"),
 "basket_outcomes":b,**c}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
