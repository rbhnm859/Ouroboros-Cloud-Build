#!/usr/bin/env python3
import argparse, json, pathlib, re, collections, statistics

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--report",required=True); ap.add_argument("--log",required=True); ap.add_argument("--out",required=True)
    ap.add_argument("--candidate",required=True); ap.add_argument("--window",required=True); ap.add_argument("--years",type=float,required=True)
    ap.add_argument("--capital",type=float,required=True); ap.add_argument("--data-mode",default="m1")
    a=ap.parse_args()
    rp=pathlib.Path(a.report); lp=pathlib.Path(a.log)
    if not rp.exists():
        pathlib.Path(a.out).write_text(json.dumps({"status":"BACKTEST_FAILED","candidate":a.candidate,"window":a.window},indent=2))
        return
    d=json.load(open(rp,encoding="utf-8-sig")); h=d.get("history",{}).get("items",[]); eq=d.get("equity",{})
    t=lp.read_text(errors="ignore") if lp.exists() else ""
    groups={}
    for x in h:
        key=(str(x.get("label","")),str(x.get("direction","")).lower(),int(x.get("entryTime",0) or 0),round(float(x.get("entryPrice",0) or 0),5))
        g=groups.setdefault(key,{"label":key[0],"direction":key[1],"entryTime":key[2],"entryPrice":key[3],"closeTime":0,"net":0.0,"pips":0.0,"fragments":0})
        g["net"]+=float(x.get("net",0) or 0); g["pips"]+=float(x.get("pips",0) or 0); g["fragments"]+=1
        g["closeTime"]=max(g["closeTime"],int(x.get("closeTime",0) or 0))
    mains=sorted([g for g in groups.values() if g["label"]=="HarmonyBotPro"],key=lambda z:z["entryTime"])
    kids=sorted([g for g in groups.values() if g["label"]=="HarmonyBotPro-G"],key=lambda z:z["entryTime"])
    pats=re.findall(r"\[GRID\]\s+Basket\s+#\d+\s+created\s+\|\s*([^|]+?)\s+\|",t,re.I)
    baskets=[]
    for i,g in enumerate(mains):
        baskets.append({"pattern":pats[i].strip() if i<len(pats) else "Unknown","direction":g["direction"],"entryTime":g["entryTime"],"entryPrice":g["entryPrice"],"closeTime":g["closeTime"],"net":g["net"],"pips":g["pips"],"grid_children":0})
    for ch in kids:
        q=[b for b in baskets if b["direction"]==ch["direction"] and b["entryTime"]<=ch["entryTime"]<=b["closeTime"]]
        if not q: q=[b for b in baskets if b["direction"]==ch["direction"] and 0<=ch["entryTime"]-b["entryTime"]<=4*60*60*1000]
        if q:
            b=max(q,key=lambda z:z["entryTime"]); b["net"]+=ch["net"]; b["pips"]+=ch["pips"]; b["grid_children"]+=1; b["closeTime"]=max(b["closeTime"],ch["closeTime"])
    vals=[b["net"] for b in baskets]; W=[x for x in vals if x>0]; L=[x for x in vals if x<0]; gp=sum(W); gl=abs(sum(L))
    pf=gp/gl if gl else (999.0 if gp else 0.0); net=sum(vals); exp=net/len(vals) if vals else 0.0
    aw=sum(W)/len(W) if W else 0.0; al=sum(L)/len(L) if L else 0.0
    rr=aw/abs(al) if aw>0 and al<0 else None
    losses=sorted([abs(x) for x in L],reverse=True); total_loss=sum(losses)
    errs=[x for x in t.splitlines() if re.search(r"InvalidRequest|Invalid Volume|Insufficient Margin|unprotected position|unexpected hedge|duplicate main",x,re.I)]
    admissions=re.findall(r"\[COMM-ADMISSION\].*?decision=(ALLOW|BLOCK).*?pattern=([^ ]+).*?hour=(\d+).*?atr=([0-9.]+).*?baseline=([0-9.]+).*?ratio=([0-9.]+).*?reason=([^\s]+)",t)
    blocked=sum(1 for x in admissions if x[0]=="BLOCK"); allowed=sum(1 for x in admissions if x[0]=="ALLOW")
    reasons=collections.Counter(x[6] for x in admissions if x[0]=="BLOCK")
    thesis=re.findall(r"\[V295-THESIS-SUMMARY\].*?invalidations=(\d+)\s+gridProofBlocked=(\d+)",t)
    inv,grid_block=(map(int,thesis[-1]) if thesis else (0,0))
    pattern={}
    monthly=collections.defaultdict(float)
    from datetime import datetime, timezone
    for b in baskets:
        if b["entryTime"]:
            try:
                monthly[datetime.fromtimestamp(b["entryTime"]/1000.0,tz=timezone.utc).strftime("%Y-%m")]+=b["net"]
            except Exception:
                pass
    for p in sorted(set(b["pattern"] for b in baskets)):
        v=[b["net"] for b in baskets if b["pattern"]==p]; ww=[x for x in v if x>0]; ll=[x for x in v if x<0]; pg=sum(ww); pl=abs(sum(ll))
        pattern[p]={"count":len(v),"net":sum(v),"pf":pg/pl if pl else (999.0 if pg else 0.0),"expectancy":sum(v)/len(v) if v else 0.0}
    out={
      "status":"OK","candidate":a.candidate,"window":a.window,"data_mode":a.data_mode,"initial_capital":a.capital,
      "baskets":len(vals),"annualized_frequency":len(vals)/a.years if a.years>0 else 0.0,
      "wins":len(W),"losses":len(L),"gross_profit":gp,"gross_loss":gl,"pf":pf,"net":net,"expectancy":exp,
      "win_rate_pct":100*len(W)/len(vals) if vals else 0.0,"realized_rr":rr,
      "max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),"largest_loss":min(L) if L else 0.0,
      "top1_loss_pct":100*sum(losses[:1])/total_loss if total_loss else 0.0,"top3_loss_pct":100*sum(losses[:3])/total_loss if total_loss else 0.0,
      "top5_loss_pct":100*sum(losses[:5])/total_loss if total_loss else 0.0,"grid_baskets":sum(b["grid_children"]>0 for b in baskets),
      "thesis_invalidations":inv,"grid_proof_blocked":grid_block,"admission_seen":len(admissions),"admission_allowed":allowed,
      "admission_blocked":blocked,"admission_block_reasons":dict(reasons),"execution_errors":len(errs),"pattern":pattern,
      "basket_nets":vals,"monthly_net":dict(sorted(monthly.items())),"profitable_months":sum(1 for v in monthly.values() if v>0),"observed_months":len(monthly),"telemetry_note":"Old baseline artifacts lacked complete per-basket MFE/MAE/HTF/PRZ/geometry snapshots. This audit does not fabricate unavailable fields."
    }
    pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
if __name__=="__main__": main()
