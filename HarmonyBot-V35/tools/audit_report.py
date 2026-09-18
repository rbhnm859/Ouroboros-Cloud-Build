#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","family"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True)
ap.add_argument("--balance",type=float,required=True)
a=ap.parse_args()
d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")
rx=re.compile(r"\[V35-BASKET-CLOSED\].*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)")
b=[{"mfe":float(m.group(1)),"mae":float(m.group(2)),"r":float(m.group(3)),"net":float(m.group(4))} for m in rx.finditer(t)]
v=[x["net"] for x in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))
pat=(r"\[V35-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+"
     r"orphanPendingOrders=(\d+)\s+stopWideningViolations=(\d+)\s+gapThroughInvalidations=(\d+)\s+gapThroughSurvivors=(\d+)\s+"
     r"unprotectedSurvivors=(\d+)\s+postFillProtectionFailures=(\d+)\s+actualBasketRiskViolations=(\d+)\s+executionStateViolations=(\d+)\s+"
     r"virtualGridFills=(\d+)\s+microModeBaskets=(\d+)\s+capitalRejectedBaskets=(\d+)\s+marginRiskViolations=(\d+)")
m=re.findall(pat,t)
keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
"gap_through_invalidations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures",
"actual_basket_risk_violations","execution_state_violations","virtual_grid_fills","micro_mode_baskets","capital_rejected_baskets","margin_risk_violations"]
c={k:0 for k in keys}
if m:
 for k,z in zip(keys,map(int,m[-1])): c[k]=z
am=re.findall(r"\[V35-ALPHA-SUMMARY\]\s+qualityRejected=(\d+)\s+regimeRejected=(\d+)\s+confirmationRejected=(\d+)\s+capitalInfeasible=(\d+)\s+alphaPassed=(\d+)",t)
alpha={"quality_rejected":0,"regime_rejected":0,"confirmation_rejected":0,"capital_infeasible":0,"alpha_passed":0}
if am:
 for k,z in zip(alpha.keys(),map(int,am[-1])): alpha[k]=z
eq=d.get("equity",{})
clean_keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations",
"gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
summary_present=bool(m); basket_activity_present=len(b)>0
engineering_clean=summary_present and all(c[k]==0 for k in clean_keys)
wins=sum(1 for x in v if x>0); losses=sum(1 for x in v if x<0)
out={"family":a.family,"window":a.window,"starting_balance":a.balance,"baskets":len(b),"wins":wins,"losses":losses,
"win_rate_pct":100*wins/len(v) if v else 0,"gross_profit":gp,"gross_loss":gl,
"pf":gp/gl if gl else (999 if gp else 0),"net":sum(v),"expectancy":sum(v)/len(v) if v else 0,
"frequency":len(b)/a.years,"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),
"summary_present":summary_present,"basket_activity_present":basket_activity_present,
"broker_profile_present":"[V35-BROKER-PROFILE]" in t,"engineering_clean":engineering_clean,
"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,
"mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0,**alpha,**c}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
