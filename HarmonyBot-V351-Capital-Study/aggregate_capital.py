#!/usr/bin/env python3
import collections, json, pathlib, statistics, sys
root=pathlib.Path(sys.argv[1])
outdir=pathlib.Path(sys.argv[2]); outdir.mkdir(parents=True,exist_ok=True)
balances=[100,150,200,300,500,1000]

def load_balance(b):
    fs=sorted(root.rglob(f"capital-{b}-[ABC].json"))
    if len(fs)!=3: raise SystemExit(f"balance {b}: expected 3 window files, found {len(fs)}")
    return [json.load(open(f)) for f in fs]

def dist_merge(xs,key):
    c=collections.Counter()
    for x in xs:
        for k,v in x[key]["distribution"].items(): c[int(k)]+=int(v)
    return dict(sorted(c.items()))

def flatten_plan_stat(xs,key):
    n=sum(x[key]["count"] for x in xs)
    mean=(sum((x[key]["mean"] or 0)*x[key]["count"] for x in xs)/n) if n else None
    mins=[x[key]["min"] for x in xs if x[key]["min"] is not None]
    maxs=[x[key]["max"] for x in xs if x[key]["max"] is not None]
    d=dist_merge(xs,key)
    expanded=[]
    for k,v in d.items(): expanded += [k]*v
    return {"count":n,"mean":mean,"median":statistics.median(expanded) if expanded else None,
            "min":min(mins) if mins else None,"max":max(maxs) if maxs else None,"distribution":d}

def aggregate(b,xs):
    perf=[x["performance"] for x in xs]
    gp=sum(x["gross_profit"] for x in perf); gl=sum(x["gross_loss"] for x in perf)
    baskets=sum(x["completed_baskets"] for x in xs); net=sum(x["net"] for x in perf)
    capfeas=sum(x["capital_feasible_candidates"] for x in xs)
    alphaelig=sum(x["alpha_eligible_candidates"] for x in xs)
    minl0=[x["minimum_l0_risk"] for x in xs if x["minimum_l0_risk"] is not None]
    safety_keys=xs[0]["safety_counters"].keys()
    safety={k:sum(x["safety_counters"][k] for x in xs) for k in safety_keys}
    util=[]; actual=[]; initrisk=[]; worstrisk=[]
    for x in xs:
        for name,target in [("post_fill_budget_utilization",util),("post_fill_actual_worst_risk",actual),("closed_initial_risk",initrisk),("closed_planned_worst_risk",worstrisk)]:
            z=x["realized_risk"][name]
            if z["count"] and z["mean"] is not None: target.append((z["count"],z["mean"],z["min"],z["max"]))
    def combine(v):
        n=sum(x[0] for x in v)
        return {"count":n,"mean":sum(x[0]*x[1] for x in v)/n if n else None,
                "min":min((x[2] for x in v if x[2] is not None),default=None),"max":max((x[3] for x in v if x[3] is not None),default=None)}
    margin_sched=sum(x["margin_rejections"]["scheduler_headroom"] for x in xs)
    margin_post=sum(x["margin_rejections"]["post_fill"] for x in xs)
    return {
      "starting_balance":b,"windows":[x["window"] for x in xs],
      "total_harmonic_candidates":sum(x["total_harmonic_candidates"] for x in xs),
      "alpha_eligible_candidates":alphaelig,
      "capital_feasible_candidates":capfeas,
      "capital_infeasible_candidates":sum(x["capital_infeasible_candidates"] for x in xs),
      "capital_feasible_ratio":capfeas/alphaelig if alphaelig else None,
      "completed_baskets":baskets,"executable_basket_ratio":baskets/capfeas if capfeas else None,
      "physical_grid_depth":flatten_plan_stat(xs,"physical_grid_depth"),
      "virtual_grid_depth":flatten_plan_stat(xs,"virtual_grid_depth"),
      "minimum_l0_risk":min(minl0) if minl0 else None,
      "capital_rejected_baskets":sum(x["capital_rejected_baskets"] for x in xs),
      "margin_rejections":{"scheduler_headroom":margin_sched,"post_fill":margin_post,"combined":margin_sched+margin_post},
      "realized_risk":{"closed_initial_risk":combine(initrisk),"closed_planned_worst_risk":combine(worstrisk),
                       "post_fill_actual_worst_risk":combine(actual),"post_fill_budget_utilization":combine(util)},
      "pf":gp/gl if gl else (999 if gp else 0),"net":net,"expectancy":net/baskets if baskets else 0,
      "max_dd_pct":max(x["max_dd_pct"] for x in perf),"positive_windows":sum(x["net"]>=0 for x in perf),
      "engineering_clean":all(x["engineering_clean"] and x["broker_profile_present"] and x["summary_present"] for x in xs),
      "safety_counters":safety
    }

rows={b:aggregate(b,load_balance(b)) for b in balances}
critical=["grid_risk_violations","actual_basket_risk_violations","execution_state_violations","unprotected_survivors","stop_widening_violations","post_fill_margin_risk_violations"]

def technical(r):
    return r["capital_feasible_candidates"]>0 and r["completed_baskets"]>0 and r["engineering_clean"] and all(r["safety_counters"].get(k,0)==0 for k in critical)

mintech=next((b for b in balances if technical(rows[b])),None)
bench=rows[1000]

def recommended(r):
    if not technical(r): return False
    if bench["capital_feasible_candidates"] and r["capital_feasible_candidates"] < .8*bench["capital_feasible_candidates"]: return False
    if bench["completed_baskets"] and r["completed_baskets"] < .8*bench["completed_baskets"]: return False
    bm=bench["physical_grid_depth"]["mean"]
    rm=r["physical_grid_depth"]["mean"]
    if bm is not None and (rm is None or rm < .8*bm): return False
    if r["margin_rejections"]["scheduler_headroom"] != 0: return False
    u=r["realized_risk"]["post_fill_budget_utilization"]["max"]
    if u is not None and u > 1.0+1e-9: return False
    return True

reco=next((b for b in balances if recommended(rows[b])),None)

decision={
  "version":"HarmonyBot V35.1","study":"CAPITAL_COMPATIBILITY_STUDY","candidate":"EXHAUSTION_VETO_ONLY",
  "evidence_class":"EXPOSED_DEV_ENGINEERING_ONLY","alpha_modified":False,"risk_kernel_modified":False,
  "tested_equities":balances,"by_equity":{str(k):v for k,v in rows.items()},
  "minimum_technical_equity":mintech,"recommended_operating_equity":reco,
  "selection_rules":"locked in CAPITAL_COMPATIBILITY_PROTOCOL.md before results",
  "next_stage":"NEW_FRESH_VALIDATION_DATA_GOVERNANCE" if mintech is not None else "CAPITAL_ARCHITECTURE_INCOMPATIBLE_AT_TESTED_EQUITIES",
  "commercial_validation":False
}
(outdir/"V351_CAPITAL_COMPATIBILITY_DECISION.json").write_text(json.dumps(decision,indent=2))

lines=["# HarmonyBot V35.1 — Capital Compatibility Study", "", "Evidence class: **EXPOSED DEV / ENGINEERING ONLY**. Not Fresh OOS and not commercial validation.", "",
       "| Equity | Alpha eligible | Capital feasible | Completed baskets | Executable ratio | Mean physical depth | Mean virtual depth | Min L0 risk | Capital rejects | Margin rejects | PF | Net | Expectancy | Worst-window DD | Clean |",
       "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|"]
for b in balances:
    r=rows[b]
    def f(x,n=3): return "—" if x is None else f"{x:.{n}f}"
    lines.append(f"| ${b} | {r['alpha_eligible_candidates']} | {r['capital_feasible_candidates']} | {r['completed_baskets']} | {f(r['executable_basket_ratio'])} | {f(r['physical_grid_depth']['mean'],2)} | {f(r['virtual_grid_depth']['mean'],2)} | {f(r['minimum_l0_risk'],2)} | {r['capital_rejected_baskets']} | {r['margin_rejections']['combined']} | {f(r['pf'])} | {r['net']:.2f} | {r['expectancy']:.2f} | {r['max_dd_pct']:.3f}% | {'YES' if r['engineering_clean'] else 'NO'} |")
lines += ["",f"**Minimum Technical Equity (tested points):** {'$'+str(mintech) if mintech is not None else 'Not established'}",
          f"**Recommended Operating Equity (locked engineering criteria):** {'$'+str(reco) if reco is not None else 'Not established'}","",
          "PF/Net/Expectancy above are development evidence only and were not used to select the equity thresholds."]
(outdir/"V351_CAPITAL_COMPATIBILITY_REPORT.md").write_text("\n".join(lines)+"\n")
print(json.dumps(decision,indent=2))
