#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics,collections
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","mode"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
ap.add_argument("--spread",type=float,default=1.0); ap.add_argument("--data-sha",default="")
a=ap.parse_args()
d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")

rx=re.compile(r"\[V67-BASKET-CLOSED\].*?cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
b=[{"cid":m.group(1),"setup":m.group(2),"pattern":m.group(3),"subtype":m.group(4),"route":m.group(5),"direction":m.group(6),
    "mfe":float(m.group(7)),"mae":float(m.group(8)),"r":float(m.group(9)),"net":float(m.group(10)),"reason":m.group(11)}
   for m in rx.finditer(t)]
vals=[x["net"] for x in b]; rr=[x["r"] for x in b]
gp=sum(v for v in vals if v>0); gl=abs(sum(v for v in vals if v<0))

sum_rx=re.findall(r"\[V67-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+orphanPendingOrders=(\d+)\s+stopWideningViolations=(\d+).*?gapThroughSurvivors=(\d+)\s+unprotectedSurvivors=(\d+)\s+postFillProtectionFailures=(\d+)\s+actualBasketRiskViolations=(\d+)\s+executionStateViolations=(\d+).*?marginRiskViolations=(\d+)",t)
keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
c={k:0 for k in keys}
if sum_rx:
    for k,z in zip(keys,map(int,sum_rx[-1])): c[k]=z

fn_rx=re.findall(r"\[V67-FAMILY-NATIVE-SUMMARY\].*?parentAbcdSuppressed=(\d+)\s+familyRouteRejected=(\d+)\s+nativeConfirmed=(\d+)\s+nativeExpired=(\d+)\s+gridWeightNormalized=(\d+)",t)
fn={"parent_abcd_suppressed":0,"family_route_rejected":0,"native_confirmed":0,"native_expired":0,"grid_weight_normalized":0}
prevent_rx=re.findall(r"\[V67-RISK-PREVENTION-SUMMARY\].*?preventedRiskRejections=(\d+)",t)
prevented_risk_rejections=int(prevent_rx[-1]) if prevent_rx else 0
if fn_rx:
    z=fn_rx[-1]
    for k,v in zip(fn.keys(),z): fn[k]=int(v)

grid_rx=re.findall(r"\[V67-GRID-PLAN\].*?budget=([-0-9.]+)\s+worst=([-0-9.]+)\s+margin=([-0-9.]+)\s+netRR=([-0-9.]+)",t)
grid=[{"budget":float(x[0]),"worst":float(x[1]),"margin":float(x[2]),"net_rr":float(x[3])} for x in grid_rx]
util=[x["worst"]/x["budget"] for x in grid if x["budget"]>0]

def summarize(key):
    g=collections.defaultdict(list)
    for x in b:g[x[key]].append(x)
    out={}
    for k,q in sorted(g.items()):
        v=[x["net"] for x in q]; pg=sum(x for x in v if x>0); pl=abs(sum(x for x in v if x<0))
        out[k]={"baskets":len(q),"net":sum(v),"pf":pg/pl if pl else (999 if pg else 0),
                "expectancy":sum(v)/len(v),"win_rate":sum(x>0 for x in v)/len(v)}
    return out
family=summarize("pattern"); route=summarize("route")
wins=sorted(x for x in rr if x>0)
def pct(v,p):
    if not v:return 0
    q=(len(v)-1)*p; lo=int(q); hi=min(len(v)-1,lo+1); return v[lo]+(v[hi]-v[lo])*(q-lo)

eq=d.get("equity",{}); unique=len({x["setup"] for x in b})
clean=bool(sum_rx) and all(c[k]==0 for k in keys)
out={
 "version":"HarmonyBot V67","mode":a.mode,"window":a.window,"starting_balance":a.balance,"spread":a.spread,"data_snapshot_sha":a.data_sha,
 "baskets":len(b),"unique_setups":unique,"duplicate_reentries":len(b)-unique,
 "wins":sum(v>0 for v in vals),"losses":sum(v<0 for v in vals),"gross_profit":gp,"gross_loss":gl,
 "pf":gp/gl if gl else (999 if gp else 0),"net":sum(vals),"expectancy":sum(vals)/len(vals) if vals else 0,
 "win_rate":sum(v>0 for v in vals)/len(vals) if vals else 0,"frequency":len(b)/a.years,
 "max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),
 "engineering_clean":clean,"broker_profile_present":"[V67-BROKER-PROFILE]" in t,
 "mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,
 "mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,
 "mean_realized_r":statistics.mean(rr) if rr else 0,
 "p95_winner_r":pct(wins,.95),"max_winner_r":max(wins) if wins else 0,
 "family_performance":family,"route_performance":route,"basket_outcomes":b,
 "avg_grid_risk_utilization":statistics.mean(util) if util else 0,
 "min_grid_net_rr":min([x["net_rr"] for x in grid] or [0]),
 "grid_plans":len(grid),"v67_family_native":fn,"prevented_risk_rejections":prevented_risk_rejections,**c
}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
