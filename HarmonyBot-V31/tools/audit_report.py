#!/usr/bin/env python3
import argparse,json,pathlib,re,collections,statistics
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--report",required=True); ap.add_argument("--log",required=True); ap.add_argument("--out",required=True)
ap.add_argument("--window",required=True); ap.add_argument("--years",type=float,required=True); ap.add_argument("--capital",type=float,required=True)
a=ap.parse_args()
rp=pathlib.Path(a.report); lp=pathlib.Path(a.log)
if not rp.exists():
    pathlib.Path(a.out).write_text(json.dumps({"status":"BACKTEST_FAILED","window":a.window},indent=2)); raise SystemExit(0)
d=json.load(open(rp,encoding="utf-8-sig")); h=d.get("history",{}).get("items",[]); eq=d.get("equity",{})
t=lp.read_text(errors="ignore") if lp.exists() else ""

trades=[x for x in h if str(x.get("label","")).startswith("HB31")]
nets=[float(x.get("net",0) or 0) for x in trades]
wins=[x for x in nets if x>0]; losses=[x for x in nets if x<0]
gp=sum(wins); gl=abs(sum(losses)); net=sum(nets); pf=gp/gl if gl else (999.0 if gp else 0.0)
exp=net/len(nets) if nets else 0.0
aw=sum(wins)/len(wins) if wins else 0.0; al=sum(losses)/len(losses) if losses else 0.0
rr=aw/abs(al) if aw>0 and al<0 else None

close_rx=re.compile(r"\[V31-CLOSED\]\s+cid=([^\s]+)\s+pos=(\d+)\s+pattern=(.*?)\s+route=([A-Z_]+)\s+dir=(Buy|Sell)\s+exit=([^\s]+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)")
closed=[]
for m in close_rx.finditer(t):
    closed.append({"cid":m.group(1),"pos":int(m.group(2)),"pattern":m.group(3).strip(),"route":m.group(4),"direction":m.group(5),
                   "exit":m.group(6),"mfe_r":float(m.group(7)),"mae_r":float(m.group(8)),"realized_r":float(m.group(9)),"net":float(m.group(10))})

pipe={}
pipe_rx=re.compile(r"\[V31-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+armed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
for m in pipe_rx.finditer(t):
    pipe[m.group(1).strip()]={"detected":int(m.group(2)),"validated":int(m.group(3)),"routed":int(m.group(4)),"prz_waiting":int(m.group(5)),
       "confirming":int(m.group(6)),"armed":int(m.group(7)),"executed":int(m.group(8)),"expired":int(m.group(9)),"rejected":int(m.group(10)),"invalidated":int(m.group(11))}

events=collections.Counter()
for m in re.finditer(r"\[V31-EVENT\].*?pattern=(.*?)\s+tf=.*?dir=.*?state=.*?route=([A-Z_]+)\s+conflict=([A-Z_]+)\s+reason=([^\r\n]+)",t):
    pattern=m.group(1).strip(); route=m.group(2); conflict=m.group(3); reason=m.group(4).strip()
    events[(pattern,route,conflict,reason)]+=1

def stats(xs):
    v=[float(x["net"]) for x in xs]; w=[x for x in v if x>0]; l=[x for x in v if x<0]
    g=sum(w); q=abs(sum(l))
    return {"count":len(v),"net":sum(v),"pf":g/q if q else (999.0 if g else 0.0),"expectancy":sum(v)/len(v) if v else 0.0,
            "win_rate_pct":100*len(w)/len(v) if v else 0.0,
            "mean_mfe_r":statistics.mean([x["mfe_r"] for x in xs]) if xs else 0.0,
            "mean_mae_r":statistics.mean([x["mae_r"] for x in xs]) if xs else 0.0,
            "mean_realized_r":statistics.mean([x["realized_r"] for x in xs]) if xs else 0.0}

pattern={p:stats([x for x in closed if x["pattern"]==p]) for p in sorted(set(x["pattern"] for x in closed))}
direction={q:stats([x for x in closed if x["direction"]==q]) for q in ("Buy","Sell")}
route={q:stats([x for x in closed if x["route"]==q]) for q in sorted(set(x["route"] for x in closed))}
exit_reason=collections.Counter(x["exit"] for x in closed)

months=collections.defaultdict(float); hours=collections.defaultdict(lambda:{"count":0,"net":0.0})
for x in trades:
    ts=int(x.get("entryTime",0) or 0); n=float(x.get("net",0) or 0)
    if ts:
        dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc)
        months[dt.strftime("%Y-%m")]+=n
        z=hours[str(dt.hour)]; z["count"]+=1; z["net"]+=n

exec_err=len(re.findall(r"\[V31-EXCEPTION-|ORDER_ERROR|InvalidRequest|Invalid Volume|Insufficient Margin",t,re.I))
summary=re.findall(r"\[V31-SUMMARY\].*?executionErrors=(\d+)",t)
if summary: exec_err=max(exec_err,int(summary[-1]))

runtime_started="[V31-START]" in t
fatal_lines=[x for x in t.splitlines() if "[V31-FATAL]" in x or "[V31-WARMUP-ERROR]" in x]
pipeline_detected=sum(z.get("detected",0) for z in pipe.values())

out={
 "status":"OK","version":"HarmonyBot V31.0","window":a.window,"initial_capital":a.capital,
 "runtime_started":runtime_started,"fatal_lines":fatal_lines,"pipeline_detected":pipeline_detected,
 "baskets":len(nets),"annualized_frequency":len(nets)/a.years if a.years else 0.0,"wins":len(wins),"losses":len(losses),
 "gross_profit":gp,"gross_loss":gl,"pf":pf,"net":net,"expectancy":exp,"win_rate_pct":100*len(wins)/len(nets) if nets else 0.0,
 "realized_rr_money":rr,"max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),"execution_errors":exec_err,
 "pattern":pattern,"direction":direction,"route":route,"exit_reason":dict(exit_reason),"pipeline":pipe,
 "pipeline_event_matrix":[{"pattern":k[0],"route":k[1],"conflict":k[2],"reason":k[3],"count":v} for k,v in events.items()],
 "monthly_net":dict(sorted(months.items())),"session_hour_utc":dict(hours),
 "profitable_months":sum(v>0 for v in months.values()),"observed_months":len(months),
 "closed_telemetry_count":len(closed),
 "mean_mfe_r":statistics.mean([x["mfe_r"] for x in closed]) if closed else 0.0,
 "mean_mae_r":statistics.mean([x["mae_r"] for x in closed]) if closed else 0.0,
 "mean_realized_r":statistics.mean([x["realized_r"] for x in closed]) if closed else 0.0,
 "basket_nets":nets
}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
pathlib.Path(a.out).with_name("PIPELINE_CONVERSION_MATRIX-"+a.window+".json").write_text(json.dumps(pipe,indent=2))
print(json.dumps(out,indent=2))
