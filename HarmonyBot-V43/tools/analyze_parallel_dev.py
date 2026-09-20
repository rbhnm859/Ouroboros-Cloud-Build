#!/usr/bin/env python3
import json,pathlib,sys
from collections import defaultdict
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
families=["V42_REPLAY","ROUTE_WATCH","STRUCTURAL_LIFETIME","FULL_V43"]; windows=["A","B","C"]
rows=[]
for p in root.rglob("*.json"):
    try:
        x=json.load(open(p,encoding="utf-8-sig"))
        if isinstance(x,dict) and x.get("family") in families and x.get("window") in windows: rows.append(x)
    except Exception: pass
by={(r["family"],r["window"]):r for r in rows}
def pf(gp,gl): return gp/gl if gl>0 else (999.0 if gp>0 else 0.0)
def amap(r):
    return {o["key"]:o for o in (r or {}).get("attribution_outcomes",[]) if o.get("key")}
def aggregate(f):
    rs=[by.get((f,w)) for w in windows]; valid=[r for r in rs if r]
    baskets=sum(int(r.get("baskets",0) or 0) for r in valid)
    gp=sum(float(r.get("gross_profit",0) or 0) for r in valid); gl=sum(float(r.get("gross_loss",0) or 0) for r in valid)
    net=sum(float(r.get("net",0) or 0) for r in valid)
    return {"family":f,"windows":{w:by.get((f,w)) for w in windows},"windows_present":len(valid),"baskets":baskets,
      "executable_baskets_per_year":baskets/1.5,"gross_profit":gp,"gross_loss":gl,"pf":pf(gp,gl),"net":net,
      "expectancy":net/baskets if baskets else 0,
      "max_dd_pct":max([float(r.get("max_dd_pct",999) or 999) for r in valid] or [999]),
      "engineering_clean":len(valid)==3 and all(bool(r.get("engineering_clean")) for r in valid),
      "execution_errors":sum(int(r.get("execution_errors",0) or 0) for r in valid),
      "actual_basket_risk_violations":sum(int(r.get("actual_basket_risk_violations",0) or 0) for r in valid),
      "margin_risk_violations":sum(int(r.get("margin_risk_violations",0) or 0) for r in valid),
      "window_nets":{w:(float(by[(f,w)].get("net",0) or 0) if (f,w) in by else None) for w in windows},
      "structural_flow":{k:sum(int(r.get(k,0) or 0) for r in valid) for k in
        ["route_watch_admitted","route_watch_recovered","route_refreshes","session_lifetime_expired","thesis_consumed_expired","pattern_native_evidence_observed"]},
      "conversion":{k:sum(int(r.get(k,0) or 0) for r in valid) for k in
        ["conversion_admissions","conversion_grid_deferred","conversion_capital_deferred","conversion_executable","scheduler_fallback_attempts","scheduler_fallback_executions"]}}
base={w:amap(by.get(("V42_REPLAY",w))) for w in windows}
def marginal(f):
    added=[]; removed=[]; wn={}; rw={}; addn={}; remn={}
    for w in windows:
        t=amap(by.get((f,w))); b=base[w]
        a=[o for k,o in t.items() if k not in b]; rem=[o for k,o in b.items() if k not in t]
        av=[float(o.get("net",0) or 0) for o in a]; rv=[float(o.get("net",0) or 0) for o in rem]
        added += av; removed += rv; wn[w]=sum(av); rw[w]=sum(rv); addn[w]=len(av); remn[w]=len(rv)
    gp=sum(x for x in added if x>0); gl=abs(sum(x for x in added if x<0))
    trade_delta=len(added)-len(removed)
    x={"added_trades":len(added),"removed_trades":len(removed),"net_trade_count_delta":trade_delta,
       "marginal_net":sum(added),"marginal_expectancy":sum(added)/len(added) if added else 0,"marginal_pf":pf(gp,gl),
       "dev_window_marginal_net":wn,"dev_window_removed_baseline_net":rw,"dev_window_added_trades":addn,"dev_window_removed_trades":remn,
       "opportunity_cost_adjusted_added_minus_removed_net":sum(added)-sum(removed)}
    x["frequency_admission_gate"]=(x["added_trades"]>0 and x["net_trade_count_delta"]>0 and x["marginal_net"]>0 and
      x["marginal_expectancy"]>0 and x["marginal_pf"]>=1.15 and all(wn[w]>=0 for w in windows))
    x["status"]="FREQUENCY_ADMISSION_PASS" if x["frequency_admission_gate"] else "FREQUENCY_EXPANSION_REJECTED"
    return x
aggs={f:aggregate(f) for f in families}
margs={f:(marginal(f) if f!="V42_REPLAY" else {"added_trades":0,"removed_trades":0,"net_trade_count_delta":0,
 "marginal_net":0,"marginal_expectancy":0,"marginal_pf":0,"dev_window_marginal_net":{w:0 for w in windows},
 "frequency_admission_gate":False,"status":"CONTROL"}) for f in families}
V36={"baskets_per_year":51.33,"net":648.58,"expectancy":8.42,"pf":1.2124,"max_dd_pct":8.77}
def alpha(a,m):
    return a["windows_present"]==3 and all((a["windows"][w] or {}).get("baskets",0)>0 and float((a["windows"][w] or {}).get("net",0) or 0)>=0 for w in windows) and       a["net"]>0 and a["pf"]>=1.25 and a["expectancy"]>0 and a["max_dd_pct"]<=10 and a["executable_baskets_per_year"]>=50 and       m["frequency_admission_gate"] and a["engineering_clean"] and a["execution_errors"]==0 and       a["actual_basket_risk_violations"]==0 and a["margin_risk_violations"]==0
def dominance(a):
    c={"frequency_gt_v36":a["executable_baskets_per_year"]>V36["baskets_per_year"],"net_gt_v36":a["net"]>V36["net"],
       "expectancy_gt_v36":a["expectancy"]>V36["expectancy"],"pf_gt_v36":a["pf"]>V36["pf"],
       "dd_le_v36":a["max_dd_pct"]<=V36["max_dd_pct"],
       "all_windows_nonnegative":all(a["window_nets"].get(w) is not None and a["window_nets"][w]>=0 for w in windows)}
    return {"baseline":V36,"checks":c,"pass":all(c.values())}
front=[]
for f in families:
    a=aggs[f]; m=margs[f]; a["marginal"]=m; a["alpha_promotion_gate"]=alpha(a,m) if f!="V42_REPLAY" else False
    a["v36_dominance"]=dominance(a); a["promotable"]=bool(a["alpha_promotion_gate"] and a["v36_dominance"]["pass"] and a["net"]>0); front.append(a)
eligible=[x for x in front if x["promotable"]]; winner=None
if eligible:
    eligible.sort(key=lambda x:(min(x["window_nets"].values()),x["net"],x["expectancy"],x["executable_baskets_per_year"],x["pf"]),reverse=True)
    winner=eligible[0]["family"]
funnel={}
for f in families:
    z=defaultdict(lambda:defaultdict(int))
    for w in windows:
        for pat,q in ((by.get((f,w)) or {}).get("pattern_pipeline") or {}).items():
            for k,v in q.items(): z[pat][k]+=int(v or 0)
    funnel[f]={p:dict(q) for p,q in z.items()}
struct={f:{w:{k:(by.get((f,w)) or {}).get(k,0) for k in
 ["route_watch_admitted","route_watch_recovered","route_refreshes","session_lifetime_expired","thesis_consumed_expired",
  "pattern_native_evidence_observed","conversion_admissions","conversion_executable","baskets","net","pf","expectancy","max_dd_pct"]}
 for w in windows} for f in families}
def vol(x): x=float(x or 0); return "LOW" if x<.80 else ("NORMAL" if x<=1.20 else "HIGH")
def eff(x): x=float(x or 0); return "LOW" if x<.18 else ("MID" if x<.28 else "HIGH")
loo={}
for f in families:
    cells=defaultdict(lambda:defaultdict(list))
    for w in windows:
        for o in (by.get((f,w)) or {}).get("attribution_outcomes",[]) or []:
            k="|".join([str(o.get("pattern","?")),str(o.get("route","?")),vol(o.get("atr_ratio")),eff(o.get("efficiency")),str(o.get("lane","?"))])
            cells[k][w].append(float(o.get("net",0) or 0))
    loo[f]={}
    for k,wm in cells.items():
        loo[f][k]={hw:{"train_trades":len([x for w in windows if w!=hw for x in wm.get(w,[])]),
                        "train_net":sum(x for w in windows if w!=hw for x in wm.get(w,[])),
                        "test_trades":len(wm.get(hw,[])),"test_net":sum(wm.get(hw,[]))} for hw in windows}
decision={"version":"HarmonyBot V43","development_candidate":winner,"status":"DEV_DOMINANCE_CANDIDATE" if winner else "NO_PROMOTABLE_CANDIDATE",
 "next_stage":"CAPITAL_COMPATIBILITY" if winner else "STRUCTURAL_ROUTING_DIAGNOSIS","fresh_validation_used":False,
 "negative_net_frequency_expansion":"PROHIBITED","v36_champion_must_be_beaten":True}
(out/"V43_PERFORMANCE_FRONTIER.json").write_text(json.dumps({"families":front,"winner":winner},indent=2))
(out/"V43_PROMOTION_DECISION.json").write_text(json.dumps(decision,indent=2))
(out/"V43_STRUCTURAL_ROUTE_MATRIX.json").write_text(json.dumps(struct,indent=2))
(out/"V43_PATTERN_SIGNAL_TO_EXECUTION_FUNNEL.json").write_text(json.dumps(funnel,indent=2))
(out/"V43_LOO_ATTRIBUTION.json").write_text(json.dumps({"dev_only_no_posthoc_tuning":True,"families":loo},indent=2))
(out/"V43_V36_DOMINANCE.json").write_text(json.dumps({f:dominance(aggs[f]) for f in families},indent=2))
(out/"candidate.txt").write_text(winner or "")
print(json.dumps({"winner":winner,"frontier":[{"family":x["family"],"baskets_per_year":x["executable_baskets_per_year"],"net":x["net"],
 "pf":x["pf"],"expectancy":x["expectancy"],"dd":x["max_dd_pct"],"marginal":x["marginal"],"alpha_gate":x["alpha_promotion_gate"],
 "v36_dominance":x["v36_dominance"]["pass"],"promotable":x["promotable"],"structural_flow":x["structural_flow"]} for x in front]},indent=2))
