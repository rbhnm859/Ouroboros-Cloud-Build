#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics
ap=argparse.ArgumentParser()
for x in ("report","log","out","window"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); a=ap.parse_args()
d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")
rx=re.compile(r"\[V33-BASKET-CLOSED\].*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)")
b=[{"mfe":float(m.group(1)),"mae":float(m.group(2)),"r":float(m.group(3)),"net":float(m.group(4))} for m in rx.finditer(t)]
v=[x["net"] for x in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))
summ=re.findall(r"\[V33-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+orphanPendingOrders=(\d+)\s+stopWideningViolations=(\d+)",t)
errs=gv=dup=orph=wide=0
if summ: errs,gv,dup,orph,wide=map(int,summ[-1])
reasons={}
for m in re.finditer(r"\[V33-EXECUTION-ERROR\]\s+code=([^\s]+)",t): reasons[m.group(1)]=reasons.get(m.group(1),0)+1
eq=d.get("equity",{})
out={"window":a.window,"baskets":len(b),"pf":gp/gl if gl else (999 if gp else 0),"net":sum(v),"expectancy":sum(v)/len(v) if v else 0,
"frequency":len(b)/a.years,"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),"execution_errors":errs,
"execution_error_reasons":reasons,"grid_risk_violations":gv,"duplicate_grid_legs":dup,"orphan_pending_orders":orph,"stop_widening_violations":wide,
"mean_mae_r":statistics.mean([x["mae"] for x in b]) if b else 0,"mean_mfe_r":statistics.mean([x["mfe"] for x in b]) if b else 0}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
