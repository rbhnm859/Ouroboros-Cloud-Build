#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics
ap=argparse.ArgumentParser()
for k in ("report","log","out","window","family"): ap.add_argument("--"+k,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
a=ap.parse_args()
d=json.load(open(a.report,encoding="utf-8-sig"))
t=pathlib.Path(a.log).read_text(errors="ignore")
rx=re.compile(r"\[V67-BASKET-CLOSED\].*?cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
rows=[]
for m in rx.finditer(t):
    rows.append(dict(cid=m.group(1),setup=m.group(2),pattern=m.group(3),subtype=m.group(4),route=m.group(5),direction=m.group(6),
                     mfe=float(m.group(7)),mae=float(m.group(8)),r=float(m.group(9)),net=float(m.group(10)),reason=m.group(11)))
v=[x["net"] for x in rows]; gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
summary=re.findall(r"\[V67-SUMMARY\].*?executionErrors=(\d+).*?gridRiskViolations=(\d+).*?duplicateGridLegs=(\d+).*?orphanPendingOrders=(\d+).*?stopWideningViolations=(\d+).*?gapThroughSurvivors=(\d+).*?unprotectedSurvivors=(\d+).*?postFillProtectionFailures=(\d+).*?actualBasketRiskViolations=(\d+).*?executionStateViolations=(\d+).*?marginRiskViolations=(\d+)",t)
names=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
clean={k:0 for k in names}
if summary:
    for k,z in zip(names,map(int,summary[-1])): clean[k]=z
engineering=bool(summary) and all(clean[k]==0 for k in names)
thr=re.findall(r"\[V67-THROUGHPUT-SUMMARY\].*?slotBlocked=(\d+).*?parked=(\d+).*?recoveredExecutions=(\d+).*?avgSlotWaitMin=([-0-9.]+).*?avgBasketOccupancyMin=([-0-9.]+).*?missedPositive=(\d+).*?avoidedNegative=(\d+)",t)
throughput={"slot_blocked":0,"parked":0,"recovered_executions":0,"avg_slot_wait_min":0.0,"avg_basket_occupancy_min":0.0,"missed_positive":0,"avoided_negative":0}
if thr:
    q=thr[-1]; throughput.update(slot_blocked=int(q[0]),parked=int(q[1]),recovered_executions=int(q[2]),avg_slot_wait_min=float(q[3]),avg_basket_occupancy_min=float(q[4]),missed_positive=int(q[5]),avoided_negative=int(q[6]))
eq=d.get("equity",{})
out={
 "variant":a.family,"window":a.window,"years":a.years,"starting_balance":a.balance,
 "baskets":len(rows),"unique_setups":len({x["setup"] for x in rows}),
 "net":sum(v),"gross_profit":gp,"gross_loss":gl,"pf":gp/gl if gl else (999 if gp else 0),
 "expectancy":sum(v)/len(v) if v else 0,"win_rate":sum(x>0 for x in v)/len(v) if v else 0,
 "frequency":len(rows)/a.years if a.years else 0,
 "max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),
 "engineering_clean":engineering,"summary_present":bool(summary),"broker_profile_present":"[V67-BROKER-PROFILE]" in t,
 "mean_mfe_r":statistics.mean([x["mfe"] for x in rows]) if rows else 0,
 "mean_mae_r":statistics.mean([x["mae"] for x in rows]) if rows else 0,
 "basket_outcomes":rows,**throughput,**clean
}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
