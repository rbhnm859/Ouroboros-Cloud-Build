#!/usr/bin/env python3
import argparse,json,pathlib,re,collections,statistics
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--report",required=True); ap.add_argument("--log",required=True); ap.add_argument("--out",required=True)
ap.add_argument("--window",required=True); ap.add_argument("--years",type=float,required=True); ap.add_argument("--capital",type=float,required=True); ap.add_argument("--data-mode",default="m1")
a=ap.parse_args()
rp=pathlib.Path(a.report); lp=pathlib.Path(a.log)
if not rp.exists():
    pathlib.Path(a.out).write_text(json.dumps({"status":"BACKTEST_FAILED","window":a.window},indent=2)); raise SystemExit(0)
d=json.load(open(rp,encoding="utf-8-sig")); h=d.get("history",{}).get("items",[]); eq=d.get("equity",{})
t=lp.read_text(errors="ignore") if lp.exists() else ""

groups={}
for x in h:
    key=(str(x.get("label","")),str(x.get("direction","")).lower(),int(x.get("entryTime",0) or 0),round(float(x.get("entryPrice",0) or 0),5))
    g=groups.setdefault(key,{"label":key[0],"direction":key[1],"entryTime":key[2],"closeTime":0,"net":0.0,"pips":0.0})
    g["net"]+=float(x.get("net",0) or 0); g["pips"]+=float(x.get("pips",0) or 0); g["closeTime"]=max(g["closeTime"],int(x.get("closeTime",0) or 0))
mains=sorted([g for g in groups.values() if g["label"]=="HarmonyBotPro"],key=lambda z:z["entryTime"])
pats=re.findall(r"\[TRADE\]\s+([^ ]+)\s+(Buy|Sell)",t)
baskets=[]
for i,g in enumerate(mains):
    pattern=pats[i][0] if i<len(pats) else "Unknown"
    baskets.append({"pattern":pattern,"direction":g["direction"],"entryTime":g["entryTime"],"closeTime":g["closeTime"],"net":g["net"],"pips":g["pips"]})

vals=[b["net"] for b in baskets]; W=[x for x in vals if x>0]; L=[x for x in vals if x<0]
gp=sum(W); gl=abs(sum(L)); net=sum(vals); pf=gp/gl if gl else (999.0 if gp else 0.0); exp=net/len(vals) if vals else 0.0
aw=sum(W)/len(W) if W else 0.0; al=sum(L)/len(L) if L else 0.0; rr=aw/abs(al) if aw>0 and al<0 else None
losses=sorted([abs(x) for x in L],reverse=True); tl=sum(losses)
errs=[x for x in t.splitlines() if re.search(r"InvalidRequest|Invalid Volume|Insufficient Margin|unprotected position|unexpected hedge|duplicate main",x,re.I)]

pattern={}
for p in sorted(set(b["pattern"] for b in baskets)):
    v=[b["net"] for b in baskets if b["pattern"]==p]; ww=[x for x in v if x>0]; ll=[x for x in v if x<0]
    pattern[p]={"count":len(v),"net":sum(v),"pf":sum(ww)/abs(sum(ll)) if ll else (999.0 if ww else 0.0),"expectancy":sum(v)/len(v) if v else 0.0,
                "win_rate_pct":100*len(ww)/len(v) if v else 0.0}

direction={}
for dr in ("buy","sell"):
    v=[b["net"] for b in baskets if b["direction"]==dr]; ww=[x for x in v if x>0]; ll=[x for x in v if x<0]
    direction[dr]={"count":len(v),"net":sum(v),"pf":sum(ww)/abs(sum(ll)) if ll else (999.0 if ww else 0.0),"expectancy":sum(v)/len(v) if v else 0.0}

monthly=collections.defaultdict(float)
for b in baskets:
    if b["entryTime"]:
        try: monthly[datetime.fromtimestamp(b["entryTime"]/1000.0,tz=timezone.utc).strftime("%Y-%m")]+=b["net"]
        except: pass

summary=re.findall(r"\[V30-SUMMARY\].*?portfolioBars=(\d+)\s+portfolioSignals=(\d+)\s+routeRejected=(\d+)\s+selectedBuy=(\d+)\s+selectedSell=(\d+)\s+thesisExits=(\d+)\s+beLocks=(\d+)\s+trailUpdates=(\d+)",t)
v30=list(map(int,summary[-1])) if summary else [0]*8
patdiag={}
for m in re.finditer(r"\[V30-PATTERN\]\s+pattern=(.*?)\s+seen=(\d+)\s+selected=(\d+)",t):
    patdiag[m.group(1)]={"seen":int(m.group(2)),"selected":int(m.group(3))}
routes=collections.Counter(m.group(1) for m in re.finditer(r"\[V30-ROUTE\].*?route=([^ ]+)",t))
life=[]
for m in re.finditer(r"\[V30-LIFECYCLE\].*?currentR=([-0-9.]+)\s+peakR=([-0-9.]+)\s+ageMin=([0-9.]+)",t):
    life.append((float(m.group(1)),float(m.group(2)),float(m.group(3))))

out={
 "status":"OK","version":"HarmonyBot V30.0 Regime-Routed Harmonic Portfolio Engine","window":a.window,"data_mode":a.data_mode,"initial_capital":a.capital,
 "baskets":len(vals),"annualized_frequency":len(vals)/a.years if a.years else 0.0,"wins":len(W),"losses":len(L),"gross_profit":gp,"gross_loss":gl,
 "pf":pf,"net":net,"expectancy":exp,"win_rate_pct":100*len(W)/len(vals) if vals else 0.0,"realized_rr":rr,
 "max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),"execution_errors":len(errs),
 "largest_loss":min(L) if L else 0.0,"top3_loss_pct":100*sum(losses[:3])/tl if tl else 0.0,
 "pattern":pattern,"direction":direction,"monthly_net":dict(sorted(monthly.items())),"profitable_months":sum(v>0 for v in monthly.values()),"observed_months":len(monthly),
 "v30":{"portfolio_bars":v30[0],"portfolio_signals":v30[1],"route_rejected":v30[2],"selected_buy":v30[3],"selected_sell":v30[4],
        "thesis_exits":v30[5],"breakeven_locks":v30[6],"trail_updates":v30[7],"pattern_portfolio":patdiag,"routes":dict(routes),
        "lifecycle_samples":len(life),"max_observed_peak_r":max([x[1] for x in life],default=0.0)},
 "basket_nets":vals
}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
