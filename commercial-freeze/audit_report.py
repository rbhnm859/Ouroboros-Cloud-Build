#!/usr/bin/env python3
import argparse, json, pathlib, re, collections, statistics
from datetime import datetime, timezone

def safe_mean(xs):
    return statistics.mean(xs) if xs else 0.0

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
        g=groups.setdefault(key,{"label":key[0],"direction":key[1],"entryTime":key[2],"entryPrice":key[3],"closeTime":0,"net":0.0,"pips":0.0})
        g["net"]+=float(x.get("net",0) or 0); g["pips"]+=float(x.get("pips",0) or 0)
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

    vals=[b["net"] for b in baskets]; W=[x for x in vals if x>0]; L=[x for x in vals if x<0]
    gp=sum(W); gl=abs(sum(L)); pf=gp/gl if gl else (999.0 if gp else 0.0); net=sum(vals); exp=net/len(vals) if vals else 0.0
    aw=sum(W)/len(W) if W else 0.0; al=sum(L)/len(L) if L else 0.0; rr=aw/abs(al) if aw>0 and al<0 else None
    losses=sorted([abs(x) for x in L],reverse=True); total_loss=sum(losses)
    errs=[x for x in t.splitlines() if re.search(r"InvalidRequest|Invalid Volume|Insufficient Margin|unprotected position|unexpected hedge|duplicate main",x,re.I)]

    adm_rx=re.compile(r"\[ARCH-ADMISSION\]\s+mode=(\d+)\s+decision=([^ ]+)\s+pattern=([^ ]+)\s+dir=([^ ]+)\s+idx=(-?\d+)\s+atr=([0-9.Ee+-]+)\s+baseline=([0-9.Ee+-]+)\s+ratio=([0-9.Ee+-]+)\s+h1=([0-9.Ee+-]+)\s+h4=([0-9.Ee+-]+)\s+m15=([0-9.Ee+-]+)\s+vol=([0-9.Ee+-]+)\s+geometry=([0-9.Ee+-]+)\s+prz=([0-9.Ee+-]+)\s+time=([0-9.Ee+-]+)\s+pivot=([0-9.Ee+-]+)\s+conf=([0-9.Ee+-]+)\s+context=([0-9.Ee+-]+)\s+confirmation=([0-9.Ee+-]+)")
    admissions=[]
    for m in adm_rx.finditer(t):
        admissions.append({
          "mode":int(m.group(1)),"decision":m.group(2),"pattern":m.group(3),"direction":m.group(4),"index":int(m.group(5)),
          "atr":float(m.group(6)),"baseline":float(m.group(7)),"atr_ratio":float(m.group(8)),
          "h1":float(m.group(9)),"h4":float(m.group(10)),"m15":float(m.group(11)),"volatility":float(m.group(12)),
          "geometry":float(m.group(13)),"prz":float(m.group(14)),"time_symmetry":float(m.group(15)),"pivot_quality":float(m.group(16)),
          "confidence":float(m.group(17)),"context":float(m.group(18)),"confirmation":float(m.group(19))
        })

    life_rx=re.compile(r"\[ARCH-LIFECYCLE\]\s+basket=(\d+)\s+pattern=([^ ]+)\s+mfeR=([0-9.Ee+-]+)\s+maeR=([0-9.Ee+-]+)\s+ageMin=([0-9.Ee+-]+)")
    lifecycle={}
    for m in life_rx.finditer(t):
        bid=int(m.group(1)); z=lifecycle.setdefault(bid,{"basket":bid,"pattern":m.group(2),"mfe_r":0.0,"mae_r":0.0,"last_age_min":0.0})
        z["mfe_r"]=max(z["mfe_r"],float(m.group(3))); z["mae_r"]=max(z["mae_r"],float(m.group(4))); z["last_age_min"]=max(z["last_age_min"],float(m.group(5)))
    giveback=len(re.findall(r"\[ARCH-GIVEBACK-EXIT\]",t))

    thesis=re.findall(r"\[V295-THESIS-SUMMARY\].*?invalidations=(\d+)\s+gridProofBlocked=(\d+)",t)
    inv,grid_block=(map(int,thesis[-1]) if thesis else (0,0))
    archsum=re.findall(r"\[ARCH-SUMMARY\].*?mode=(\d+).*?seen=(\d+).*?contextBlocked=(\d+).*?confirmationBlocked=(\d+).*?givebackExits=(\d+).*?lifecycleSamples=(\d+)",t)
    arch_summary=list(map(int,archsum[-1])) if archsum else [0,0,0,0,0,0]

    pattern={}; monthly=collections.defaultdict(float)
    for b in baskets:
        if b["entryTime"]:
            try: monthly[datetime.fromtimestamp(b["entryTime"]/1000.0,tz=timezone.utc).strftime("%Y-%m")]+=b["net"]
            except Exception: pass
    for p in sorted(set(b["pattern"] for b in baskets)):
        v=[b["net"] for b in baskets if b["pattern"]==p]; ww=[x for x in v if x>0]; ll=[x for x in v if x<0]; pg=sum(ww); pl=abs(sum(ll))
        pattern[p]={"count":len(v),"net":sum(v),"pf":pg/pl if pl else (999.0 if pg else 0.0),"expectancy":sum(v)/len(v) if v else 0.0}

    by_decision=collections.Counter(x["decision"] for x in admissions)
    by_pattern=collections.defaultdict(lambda:{"seen":0,"allow":0,"blocked":0,"context":[],"confirmation":[],"atr_ratio":[]})
    for x in admissions:
        z=by_pattern[x["pattern"]]; z["seen"]+=1; z["allow"]+=int(x["decision"]=="ALLOW"); z["blocked"]+=int(x["decision"]!="ALLOW")
        z["context"].append(x["context"]); z["confirmation"].append(x["confirmation"]); z["atr_ratio"].append(x["atr_ratio"])
    admission_pattern={k:{"seen":v["seen"],"allow":v["allow"],"blocked":v["blocked"],"mean_context":safe_mean(v["context"]),"mean_confirmation":safe_mean(v["confirmation"]),"mean_atr_ratio":safe_mean(v["atr_ratio"])} for k,v in by_pattern.items()}

    life=list(lifecycle.values())
    life_pattern={}
    for p in sorted(set(x["pattern"] for x in life)):
        xs=[x for x in life if x["pattern"]==p]
        life_pattern[p]={"count":len(xs),"mean_mfe_r":safe_mean([x["mfe_r"] for x in xs]),"mean_mae_r":safe_mean([x["mae_r"] for x in xs]),"median_mfe_r":statistics.median([x["mfe_r"] for x in xs]) if xs else 0.0,"median_mae_r":statistics.median([x["mae_r"] for x in xs]) if xs else 0.0}

    out={
      "status":"OK","candidate":a.candidate,"window":a.window,"data_mode":a.data_mode,"initial_capital":a.capital,
      "baskets":len(vals),"annualized_frequency":len(vals)/a.years if a.years>0 else 0.0,
      "wins":len(W),"losses":len(L),"gross_profit":gp,"gross_loss":gl,"pf":pf,"net":net,"expectancy":exp,
      "win_rate_pct":100*len(W)/len(vals) if vals else 0.0,"realized_rr":rr,
      "max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),"largest_loss":min(L) if L else 0.0,
      "top1_loss_pct":100*sum(losses[:1])/total_loss if total_loss else 0.0,"top3_loss_pct":100*sum(losses[:3])/total_loss if total_loss else 0.0,
      "top5_loss_pct":100*sum(losses[:5])/total_loss if total_loss else 0.0,"grid_baskets":sum(b["grid_children"]>0 for b in baskets),
      "thesis_invalidations":inv,"grid_proof_blocked":grid_block,"execution_errors":len(errs),"pattern":pattern,
      "basket_nets":vals,"monthly_net":dict(sorted(monthly.items())),"profitable_months":sum(1 for v in monthly.values() if v>0),"observed_months":len(monthly),
      "architecture":{"summary":{"mode":arch_summary[0],"seen":arch_summary[1],"context_blocked":arch_summary[2],"confirmation_blocked":arch_summary[3],"giveback_exits":arch_summary[4],"lifecycle_samples":arch_summary[5]},
        "decision_counts":dict(by_decision),"pattern_admission":admission_pattern,
        "mean_context":safe_mean([x["context"] for x in admissions]),"mean_confirmation":safe_mean([x["confirmation"] for x in admissions]),
        "mean_h1":safe_mean([x["h1"] for x in admissions]),"mean_h4":safe_mean([x["h4"] for x in admissions]),"mean_m15":safe_mean([x["m15"] for x in admissions]),
        "lifecycle_count":len(life),"mean_mfe_r":safe_mean([x["mfe_r"] for x in life]),"mean_mae_r":safe_mean([x["mae_r"] for x in life]),"lifecycle_by_pattern":life_pattern,
        "giveback_exit_count":giveback},
      "telemetry_note":"Architecture telemetry is causal and generated in-run. Lifecycle MFE/MAE values are bucketed maxima captured by the bot, not fabricated from post-hoc price data."
    }
    pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
if __name__=="__main__": main()
