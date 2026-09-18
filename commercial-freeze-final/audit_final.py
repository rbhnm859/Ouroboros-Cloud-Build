#!/usr/bin/env python3
import argparse,json,pathlib,re,collections
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--report",required=True); ap.add_argument("--log",required=True); ap.add_argument("--out",required=True)
ap.add_argument("--profile",required=True); ap.add_argument("--window",required=True); ap.add_argument("--years",type=float,required=True)
ap.add_argument("--capital",type=float,required=True); ap.add_argument("--data-mode",default="m1")
a=ap.parse_args()

rp=pathlib.Path(a.report); lp=pathlib.Path(a.log)
if not rp.exists():
    pathlib.Path(a.out).write_text(json.dumps({"status":"BACKTEST_FAILED","profile":a.profile,"window":a.window},indent=2))
    raise SystemExit(0)

d=json.load(open(rp,encoding="utf-8-sig")); h=d.get("history",{}).get("items",[]); eq=d.get("equity",{})
t=lp.read_text(errors="ignore") if lp.exists() else ""

groups={}
for x in h:
    key=(str(x.get("label","")),str(x.get("direction","")).lower(),int(x.get("entryTime",0) or 0),round(float(x.get("entryPrice",0) or 0),5))
    g=groups.setdefault(key,{"label":key[0],"direction":key[1],"entryTime":key[2],"entryPrice":key[3],"closeTime":0,"net":0.0,"pips":0.0})
    g["net"]+=float(x.get("net",0) or 0); g["pips"]+=float(x.get("pips",0) or 0)
    g["closeTime"]=max(g["closeTime"],int(x.get("closeTime",0) or 0))
mains=sorted([g for g in groups.values() if g["label"]=="HarmonyBotPro"],key=lambda z:z["entryTime"])

trade_patterns=[m.group(1).strip() for m in re.finditer(r"\[TRADE\]\s+(.+?)\s+(?:Buy|Sell)\s+vol=",t)]
baskets=[]
for i,g in enumerate(mains):
    baskets.append({**g,"pattern":trade_patterns[i] if i<len(trade_patterns) else "Unknown"})

vals=[b["net"] for b in baskets]; W=[x for x in vals if x>0]; L=[x for x in vals if x<0]
gp=sum(W); gl=abs(sum(L)); net=sum(vals); pf=gp/gl if gl else (999.0 if gp else 0.0)
exp=net/len(vals) if vals else 0.0
aw=sum(W)/len(W) if W else 0.0; al=sum(L)/len(L) if L else 0.0
rr=aw/abs(al) if aw>0 and al<0 else None
losses=sorted([abs(x) for x in L],reverse=True); total_loss=sum(losses)
errs=[x for x in t.splitlines() if re.search(r"InvalidRequest|Invalid Volume|Insufficient Margin|unprotected position|unexpected hedge|duplicate main",x,re.I)]

final_events=re.findall(r"\[FINAL-EDGE\]\s+decision=(ALLOW|BLOCK).*?profile=(\d+).*?pattern=(.*?)\s+dir=(Buy|Sell).*?votes=(\d+).*?q=([0-9.]+)(?:\s+reason=([^\s]+))?",t)
final_allowed=sum(1 for x in final_events if x[0]=="ALLOW")
final_blocked=sum(1 for x in final_events if x[0]=="BLOCK")
block_reasons=collections.Counter((x[6] or "UNKNOWN") for x in final_events if x[0]=="BLOCK")

monthly=collections.defaultdict(float); direction=collections.defaultdict(list); pattern=collections.defaultdict(list)
for b in baskets:
    direction[b["direction"]].append(b["net"]); pattern[b["pattern"]].append(b["net"])
    if b["entryTime"]:
        try: monthly[datetime.fromtimestamp(b["entryTime"]/1000.0,tz=timezone.utc).strftime("%Y-%m")]+=b["net"]
        except Exception: pass

def summarize(v):
    w=[x for x in v if x>0]; l=[x for x in v if x<0]; g=sum(w); q=abs(sum(l))
    return {"count":len(v),"net":sum(v),"pf":g/q if q else (999.0 if g else 0.0),"expectancy":sum(v)/len(v) if v else 0.0,
            "win_rate_pct":100*len(w)/len(v) if v else 0.0}

out={
 "status":"OK","profile":a.profile,"window":a.window,"data_mode":a.data_mode,"initial_capital":a.capital,
 "baskets":len(vals),"annualized_frequency":len(vals)/a.years if a.years>0 else 0.0,
 "wins":len(W),"losses":len(L),"gross_profit":gp,"gross_loss":gl,"pf":pf,"net":net,"expectancy":exp,
 "win_rate_pct":100*len(W)/len(vals) if vals else 0.0,"realized_rr":rr,
 "max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),"largest_loss":min(L) if L else 0.0,
 "top3_loss_pct":100*sum(losses[:3])/total_loss if total_loss else 0.0,
 "execution_errors":len(errs),"direction":{k:summarize(v) for k,v in sorted(direction.items())},
 "pattern":{k:summarize(v) for k,v in sorted(pattern.items())},
 "final_edge_seen":len(final_events),"final_edge_allowed":final_allowed,"final_edge_blocked":final_blocked,
 "final_edge_block_reasons":dict(block_reasons),"basket_nets":vals,
 "monthly_net":dict(sorted(monthly.items())),"profitable_months":sum(1 for v in monthly.values() if v>0),"observed_months":len(monthly)
}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
