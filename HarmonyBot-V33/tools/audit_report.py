#!/usr/bin/env python3
import argparse,json,pathlib,re,collections,statistics
from datetime import datetime,timezone
ap=argparse.ArgumentParser()
for x in ("report","log","out","window"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--capital",type=float,required=True)
a=ap.parse_args(); rp=pathlib.Path(a.report); lp=pathlib.Path(a.log)
if not rp.exists():
    pathlib.Path(a.out).write_text(json.dumps({"status":"BACKTEST_FAILED","window":a.window},indent=2)); raise SystemExit(0)
d=json.load(open(rp,encoding="utf-8-sig")); h=d.get("history",{}).get("items",[]); eq=d.get("equity",{})
t=lp.read_text(errors="ignore") if lp.exists() else ""

brx=re.compile(r"\[V33-BASKET-CLOSED\]\s+basket=(\S+)\s+cid=(\S+)\s+pattern=(.*?)\s+route=([A-Z_]+)\s+dir=(Buy|Sell)\s+plannedLegs=(\d+)\s+filledLegs=(\d+)\s+anchor=([-0-9.Ee]+)\s+avgEntry=([-0-9.Ee]+)\s+entryImprovePips=([-0-9.]+)\s+stop=([-0-9.Ee]+)\s+target=([-0-9.Ee]+)\s+initialRisk=([-0-9.]+)\s+worstRisk=([-0-9.]+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=([^\r\n]+)")
baskets=[]
for m in brx.finditer(t):
    baskets.append({"basket":m.group(1),"cid":m.group(2),"pattern":m.group(3).strip(),"route":m.group(4),"direction":m.group(5),
      "planned_legs":int(m.group(6)),"filled_legs":int(m.group(7)),"anchor":float(m.group(8)),"avg_entry":float(m.group(9)),
      "entry_improvement_pips":float(m.group(10)),"stop":float(m.group(11)),"target":float(m.group(12)),
      "initial_risk":float(m.group(13)),"worst_risk":float(m.group(14)),"mfe_r":float(m.group(15)),"mae_r":float(m.group(16)),
      "realized_r":float(m.group(17)),"net":float(m.group(18)),"reason":m.group(19).strip()})

lrx=re.compile(r"\[V33-LEG-CLOSED\]\s+basket=(\S+)\s+cid=(\S+)\s+leg=L(\d+)\s+pos=(\d+)\s+pattern=(.*?)\s+route=([A-Z_]+)\s+dir=(Buy|Sell)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=([^\r\n]+)")
legs=[]
for m in lrx.finditer(t):
    legs.append({"basket":m.group(1),"cid":m.group(2),"leg":int(m.group(3)),"pos":int(m.group(4)),"pattern":m.group(5).strip(),
      "route":m.group(6),"direction":m.group(7),"mfe_r":float(m.group(8)),"mae_r":float(m.group(9)),
      "realized_r":float(m.group(10)),"net":float(m.group(11)),"reason":m.group(12).strip()})

def stats(xs):
    v=[float(x["net"]) for x in xs]; w=[z for z in v if z>0]; l=[z for z in v if z<0]; gp=sum(w); gl=abs(sum(l))
    return {"count":len(v),"gross_profit":gp,"gross_loss":gl,"net":sum(v),"pf":gp/gl if gl else (999.0 if gp else 0.0),
      "expectancy":sum(v)/len(v) if v else 0.0,"win_rate_pct":100*len(w)/len(v) if v else 0.0,
      "mean_mfe_r":statistics.mean([x["mfe_r"] for x in xs]) if xs else 0.0,
      "mean_mae_r":statistics.mean([x["mae_r"] for x in xs]) if xs else 0.0,
      "mean_realized_r":statistics.mean([x["realized_r"] for x in xs]) if xs else 0.0}

overall=stats(baskets)
l0=[x for x in legs if x["leg"]==0]; single=stats(l0)
cum=peak=dd=0.0
for x in l0:
    cum+=x["net"]; peak=max(peak,cum); dd=max(dd,peak-cum)
single["max_dd_pct"]=100*dd/a.capital if a.capital else 0.0

pipe={}
prx=re.compile(r"\[V33-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+armed=(\d+)\s+basketPlanned=(\d+)\s+leg0=(\d+)\s+leg1=(\d+)\s+leg2=(\d+)\s+leg3=(\d+)\s+basketClosed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
for m in prx.finditer(t):
    ks=["detected","validated","routed","prz_touched","confirming","armed","basket_planned","leg0_executed","leg1_filled","leg2_filled","leg3_filled","basket_closed","executed","expired","rejected","invalidated"]
    pipe[m.group(1).strip()]={k:int(v) for k,v in zip(ks,m.groups()[1:])}

summ=re.findall(r"\[V33-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+orphanPendingOrders=(\d+)\s+stopWideningViolations=(\d+)",t)
errs=gridv=dup=orph=widen=0
if summ: errs,gridv,dup,orph,widen=map(int,summ[-1])
error_reasons=collections.Counter()
for m in re.finditer(r"\[V33-EXECUTION-ERROR\]\s+code=([^\s]+)\s+detail=([^\r\n]*)",t):
    error_reasons[m.group(1)]+=1
if error_reasons:
    errs=max(errs,sum(error_reasons.values()))

admission_risk_rejects=sum(int(x) for x in re.findall(r"admissionRiskRejects=(\d+)",t)[-1:] or [0])
admission_thesis_rejects=sum(int(x) for x in re.findall(r"admissionThesisRejects=(\d+)",t)[-1:] or [0])
frontier_advances=len(re.findall(r"\[V33-BASKET-EVENT\].*?FRONTIER_ADVANCED_",t))
technical_retries=len(re.findall(r"\[V33-BASKET-EVENT\].*?GRID_LEG_TRANSIENT_RETRY_",t))
admission_passes=len(re.findall(r"\[V33-BASKET-EVENT\].*?ADMISSION_PASSED_L",t))

by_pattern={p:stats([x for x in baskets if x["pattern"]==p]) for p in sorted(set(x["pattern"] for x in baskets))}
by_route={p:stats([x for x in baskets if x["route"]==p]) for p in sorted(set(x["route"] for x in baskets))}
by_dir={p:stats([x for x in baskets if x["direction"]==p]) for p in ("Buy","Sell")}
by_fills={str(n):stats([x for x in baskets if x["filled_legs"]==n]) for n in (1,2,3,4)}

# session/month attribution uses first L0 entry per basket from cTrader history, but basket net is counted once.
first={}
for x in h:
    lab=str(x.get("label",""))
    if not lab.startswith("HB33|") or not lab.endswith("|L0"): continue
    parts=lab.split("|")
    if len(parts)>=3: first[parts[1]]=int(x.get("entryTime",0) or 0)
months=collections.defaultdict(float); hours=collections.defaultdict(lambda:{"count":0,"net":0.0})
for b in baskets:
    ts=first.get(b["basket"],0)
    if ts:
        dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc); months[dt.strftime("%Y-%m")]+=b["net"]
        z=hours[str(dt.hour)]; z["count"]+=1; z["net"]+=b["net"]

fill_rates={}
planned=sum(1 for _ in baskets)
for n in range(4):
    denom=sum(1 for b in baskets if b["planned_legs"]>n)
    filled=sum(1 for b in baskets if b["filled_legs"]>n)
    fill_rates["L"+str(n)]=filled/denom if denom else 0.0

out={"status":"OK","version":"HarmonyBot V33.0","window":a.window,"initial_capital":a.capital,
 "runtime_started":"[V33-START]" in t,"pipeline_detected":sum(z.get("detected",0) for z in pipe.values()),
 "baskets":overall["count"],"annualized_frequency":overall["count"]/a.years if a.years else 0.0,
 **overall,"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),
 "execution_errors":errs,"execution_error_reasons":dict(error_reasons),"grid_risk_violations":gridv,"duplicate_grid_legs":dup,"orphan_pending_orders":orph,"stop_widening_violations":widen,
 "risk_lifecycle_attribution":{"admission_risk_rejects":admission_risk_rejects,"admission_thesis_rejects":admission_thesis_rejects,
   "admission_passes":admission_passes,"frontier_advances":frontier_advances,"technical_retries":technical_retries},
 "pattern":by_pattern,"route":by_route,"direction":by_dir,"filled_leg_count":by_fills,"pipeline":pipe,
 "single_entry_equivalent":single,
 "grid_attribution":{"fill_rates":fill_rates,"average_filled_legs":statistics.mean([b["filled_legs"] for b in baskets]) if baskets else 0,
   "average_entry_improvement_pips":statistics.mean([b["entry_improvement_pips"] for b in baskets]) if baskets else 0,
   "average_worst_risk_utilization":statistics.mean([b["worst_risk"]/b["initial_risk"] for b in baskets if b["initial_risk"]>0]) if baskets else 0,
   "actual_basket":overall,"single_entry_equivalent":single},
 "monthly_net":dict(sorted(months.items())),"session_hour_utc":dict(hours),
 "profitable_months":sum(v>0 for v in months.values()),"observed_months":len(months),
 "mean_mfe_r":overall["mean_mfe_r"],"mean_mae_r":overall["mean_mae_r"],"basket_nets":[b["net"] for b in baskets]}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
pathlib.Path(a.out).with_name("PIPELINE_CONVERSION_MATRIX-"+a.window+".json").write_text(json.dumps(pipe,indent=2))
print(json.dumps(out,indent=2))
