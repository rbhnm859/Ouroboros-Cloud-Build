#!/usr/bin/env python3
import json, pathlib, sys, math
from collections import defaultdict

root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
rows=[]
for p in root.rglob("*.json"):
    try:
        x=json.load(open(p,encoding="utf-8-sig"))
        if isinstance(x,dict) and x.get("family") and x.get("window") in ("A","B","C"):
            rows.append(x)
    except Exception:
        pass

families=["LEGACY_REPLAY","CORE_CONVERSION","RESCUE_CONVERSION","FULL_V42"]
windows=["A","B","C"]
by={(r["family"],r["window"]):r for r in rows}

def pf(gp,gl):
    return gp/gl if gl>0 else (999.0 if gp>0 else 0.0)

def aggregate(fam):
    rs=[by.get((fam,w)) for w in windows]
    valid=[r for r in rs if r]
    baskets=sum(r.get("baskets",0) for r in valid)
    gp=sum(float(r.get("gross_profit",0) or 0) for r in valid)
    gl=sum(float(r.get("gross_loss",0) or 0) for r in valid)
    net=sum(float(r.get("net",0) or 0) for r in valid)
    return {
        "family":fam,
        "windows":{w:by.get((fam,w)) for w in windows},
        "windows_present":len(valid),
        "baskets":baskets,
        "executable_baskets_per_year":baskets/1.5,
        "gross_profit":gp,"gross_loss":gl,"pf":pf(gp,gl),
        "net":net,"expectancy":net/baskets if baskets else 0,
        "max_dd_pct":max([float(r.get("max_dd_pct",999) or 999) for r in valid] or [999]),
        "engineering_clean":len(valid)==3 and all(bool(r.get("engineering_clean")) for r in valid),
        "actual_basket_risk_violations":sum(int(r.get("actual_basket_risk_violations",0) or 0) for r in valid),
        "margin_risk_violations":sum(int(r.get("margin_risk_violations",0) or 0) for r in valid),
        "execution_errors":sum(int(r.get("execution_errors",0) or 0) for r in valid),
        "window_nets":{w:(float(by[(fam,w)].get("net",0) or 0) if (fam,w) in by else None) for w in windows},
        "conversion":{
            "admissions":sum(int(r.get("conversion_admissions",0) or 0) for r in valid),
            "grid_deferred":sum(int(r.get("conversion_grid_deferred",0) or 0) for r in valid),
            "capital_deferred":sum(int(r.get("conversion_capital_deferred",0) or 0) for r in valid),
            "executable":sum(int(r.get("conversion_executable",0) or 0) for r in valid),
            "fallback_attempts":sum(int(r.get("scheduler_fallback_attempts",0) or 0) for r in valid),
            "fallback_executions":sum(int(r.get("scheduler_fallback_executions",0) or 0) for r in valid)
        }
    }

def executed_map(r):
    m={}
    for o in (r or {}).get("attribution_outcomes",[]) or []:
        k=o.get("key")
        if not k: continue
        # ATTRIBUTION-OUTCOME is emitted only for realized basket outcomes.
        m[k]=o
    return m

legacy={w:executed_map(by.get(("LEGACY_REPLAY",w))) for w in windows}

def marginal(fam):
    total=[]; wn={}
    for w in windows:
        test=executed_map(by.get((fam,w)))
        added=[o for k,o in test.items() if k not in legacy[w]]
        vals=[float(o.get("net",0) or 0) for o in added]
        wn[w]=sum(vals)
        total.extend(vals)
    gp=sum(x for x in total if x>0); gl=abs(sum(x for x in total if x<0))
    ans={"added_trades":len(total),"marginal_net":sum(total),
         "marginal_expectancy":sum(total)/len(total) if total else 0,
         "marginal_pf":pf(gp,gl),"dev_window_marginal_net":wn}
    ans["frequency_admission_gate"]=(
        ans["added_trades"]>0 and ans["marginal_net"]>0 and ans["marginal_expectancy"]>0 and
        ans["marginal_pf"]>=1.15 and all(wn[w]>=0 for w in windows)
    )
    ans["status"]="FREQUENCY_ADMISSION_PASS" if ans["frequency_admission_gate"] else "FREQUENCY_EXPANSION_REJECTED"
    return ans

aggs={f:aggregate(f) for f in families}
marg={f:(marginal(f) if f!="LEGACY_REPLAY" else {
    "added_trades":0,"marginal_net":0,"marginal_expectancy":0,"marginal_pf":0,
    "dev_window_marginal_net":{w:0 for w in windows},
    "frequency_admission_gate":False,"status":"CONTROL"
}) for f in families}

V36={"baskets_per_year":51.33,"net":648.58,"expectancy":8.42,"pf":1.2124,"max_dd_pct":8.77}

def alpha_gate(a,m):
    return (
      a["windows_present"]==3 and
      all((a["windows"][w] or {}).get("baskets",0)>0 and float((a["windows"][w] or {}).get("net",0) or 0)>=0 for w in windows) and
      a["net"]>0 and a["pf"]>=1.25 and a["expectancy"]>0 and a["max_dd_pct"]<=10 and
      a["executable_baskets_per_year"]>=50 and m["frequency_admission_gate"] and
      a["engineering_clean"] and a["actual_basket_risk_violations"]==0 and a["margin_risk_violations"]==0 and a["execution_errors"]==0
    )

def dominance(a):
    checks={
      "frequency_gt_v36":a["executable_baskets_per_year"]>V36["baskets_per_year"],
      "net_gt_v36":a["net"]>V36["net"],
      "expectancy_gt_v36":a["expectancy"]>V36["expectancy"],
      "pf_gt_v36":a["pf"]>V36["pf"],
      "dd_le_v36":a["max_dd_pct"]<=V36["max_dd_pct"],
      "all_windows_nonnegative":all((a["window_nets"].get(w) is not None and a["window_nets"][w]>=0) for w in windows)
    }
    return {"baseline":V36,"checks":checks,"pass":all(checks.values())}

front=[]
for f in families:
    a=aggs[f]; m=marg[f]; d=dominance(a)
    a["marginal"]=m
    a["alpha_promotion_gate"]=alpha_gate(a,m) if f!="LEGACY_REPLAY" else False
    a["v36_dominance"]=d
    a["promotable"]=bool(a["alpha_promotion_gate"] and d["pass"] and a["net"]>0)
    front.append(a)

eligible=[x for x in front if x["promotable"]]
winner=None
if eligible:
    eligible.sort(key=lambda x:(min(x["window_nets"].values()),x["net"],x["expectancy"],x["executable_baskets_per_year"],x["pf"]),reverse=True)
    winner=eligible[0]["family"]

# Pattern signal-to-execution funnel.
funnel={}
for f in families:
    sums=defaultdict(lambda: defaultdict(int))
    for w in windows:
        r=by.get((f,w)) or {}
        for pat,p in (r.get("pattern_pipeline") or {}).items():
            for k,v in p.items(): sums[pat][k]+=int(v or 0)
    funnel[f]={pat:dict(v) for pat,v in sums.items()}

# Conversion matrix.
conversion={
  f:{w:{k:(by.get((f,w)) or {}).get(k,0) for k in
    ["conversion_admissions","conversion_grid_deferred","conversion_capital_deferred","conversion_executable",
     "scheduler_fallback_attempts","scheduler_fallback_executions","baskets","net","pf","expectancy","max_dd_pct"]}
     for w in windows}
  for f in families
}

# DEV-only Pattern x Route x Volatility x Efficiency x Lane descriptive cross-validation.
def vol_bucket(x):
    x=float(x or 0)
    return "LOW" if x<0.80 else ("NORMAL" if x<=1.20 else "HIGH")
def eff_bucket(x):
    x=float(x or 0)
    return "LOW" if x<0.18 else ("MID" if x<0.28 else "HIGH")
loo={}
for f in families:
    cells=defaultdict(lambda:defaultdict(list))
    for w in windows:
        r=by.get((f,w)) or {}
        for o in r.get("attribution_outcomes",[]) or []:
            key="|".join([str(o.get("pattern","?")),str(o.get("route","?")),vol_bucket(o.get("atr_ratio")),
                          eff_bucket(o.get("efficiency")),str(o.get("lane","?"))])
            cells[key][w].append(float(o.get("net",0) or 0))
    entries={}
    for key,wm in cells.items():
        held={}
        for hw in windows:
            train=[x for w in windows if w!=hw for x in wm.get(w,[])]
            test=wm.get(hw,[])
            held[hw]={
              "train_trades":len(train),"train_net":sum(train),
              "test_trades":len(test),"test_net":sum(test)
            }
        entries[key]=held
    loo[f]=entries

decision={
 "version":"HarmonyBot V42",
 "development_candidate":winner,
 "status":"DEV_DOMINANCE_CANDIDATE" if winner else "NO_PROMOTABLE_CANDIDATE",
 "next_stage":"CAPITAL_COMPATIBILITY" if winner else "OPPORTUNITY_CONVERSION_DIAGNOSIS",
 "fresh_validation_used":False,
 "negative_net_frequency_expansion":"PROHIBITED",
 "v36_champion_must_be_beaten":True
}
pathlib.Path(out/"V42_PERFORMANCE_FRONTIER.json").write_text(json.dumps({"families":front,"winner":winner},indent=2))
pathlib.Path(out/"V42_PROMOTION_DECISION.json").write_text(json.dumps(decision,indent=2))
pathlib.Path(out/"V42_OPPORTUNITY_CONVERSION_MATRIX.json").write_text(json.dumps(conversion,indent=2))
pathlib.Path(out/"V42_PATTERN_SIGNAL_TO_EXECUTION_FUNNEL.json").write_text(json.dumps(funnel,indent=2))
pathlib.Path(out/"V42_LOO_ATTRIBUTION.json").write_text(json.dumps({"dev_only_no_posthoc_tuning":True,"families":loo},indent=2))
pathlib.Path(out/"V42_V36_DOMINANCE.json").write_text(json.dumps({f:aggs[f].get("v36_dominance",dominance(aggs[f])) for f in families},indent=2))
pathlib.Path(out/"candidate.txt").write_text(winner or "")
print(json.dumps({"winner":winner,"frontier":[{"family":x["family"],"baskets_per_year":x["executable_baskets_per_year"],
 "net":x["net"],"pf":x["pf"],"expectancy":x["expectancy"],"dd":x["max_dd_pct"],
 "marginal":x["marginal"],"alpha_gate":x["alpha_promotion_gate"],"v36_dominance":x["v36_dominance"]["pass"],
 "promotable":x["promotable"]} for x in front]},indent=2))
