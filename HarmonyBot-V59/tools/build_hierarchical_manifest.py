#!/usr/bin/env python3
import json, math, pathlib, re, statistics, sys

root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
FAMILY_MIN_N=24
CELL_MIN_N=8
Z=1.645  # stricter than V58's 1.28 one-sided bound

shadow_rx=re.compile(r"\[V59-SHADOW-CLOSED\]\s+cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+regime=(\S+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+holdMin=([-0-9.]+)\s+reason=(\S+)")
cap_rx=re.compile(r"\[V59-CAPTURE-CLOSED\]\s+cid=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+regime=(\S+)\s+baselineR=([-0-9.]+)\s+protect75R=([-0-9.]+)\s+be1R=([-0-9.]+)\s+trail125R=([-0-9.]+)\s+timeDecayR=([-0-9.]+)\s+hybridR=([-0-9.]+)\s+mfeR=([-0-9.]+)\s+captureRatio=([-0-9.]+)")
rows=[]
for p in sorted(root.rglob("*.log")):
    txt=p.read_text(errors="ignore"); source=p.name
    research_only=set()
    for line in txt.splitlines():
        if "V59_RESEARCH_CONTINUE_PATTERN_QUALITY" in line or "V59_RESEARCH_CONTINUE_ROUTER_NO_TRADE" in line:
            m=re.search(r"cid=(\S+)",line)
            if m: research_only.add(m.group(1))
    shadows={q.group(1):{"cid":q.group(1),"pattern":q.group(3),"route":q.group(4),"regime":q.group(5),"baseline":float(q.group(8)),"hold":float(q.group(9)),"mfe":float(q.group(6)),"mae":float(q.group(7)),"source":source,"research_only":q.group(1) in research_only} for q in shadow_rx.finditer(txt)}
    for q in cap_rx.finditer(txt):
        cid=q.group(1)
        if cid not in shadows: continue
        x=shadows[cid]
        x.update({"hybrid":float(q.group(10)),"protect75":float(q.group(6)),"be1":float(q.group(7)),"trail125":float(q.group(8)),"time_decay":float(q.group(9))})
        rows.append(x)
if not rows: raise SystemExit("no V59 capture outcomes found")

def mean(xs): return sum(xs)/len(xs) if xs else 0.0
def pf(xs):
    gp=sum(x for x in xs if x>0); gl=abs(sum(x for x in xs if x<0))
    return gp/gl if gl else (999.0 if gp else 0.0)
def variance(xs, fallback):
    return statistics.pvariance(xs) if len(xs)>1 else fallback
def posterior(vals, prior_mean, prior_n, global_var):
    n=len(vals)
    m=(sum(vals)+prior_n*prior_mean)/(n+prior_n)
    v=max(variance(vals,global_var),global_var*.25,1e-6)
    se=math.sqrt(v/max(1,n+prior_n))
    return m, m-Z*se

research_rows=[x for x in rows if x["research_only"]]
capital_rows=[x for x in rows if not x["research_only"]]
global_vals=[x["hybrid"] for x in capital_rows]
gmean=mean(global_vals)
gvar=statistics.pvariance(global_vals) if len(global_vals)>1 else (statistics.pvariance([x["hybrid"] for x in rows]) if len(rows)>1 else 1.0)

families={}
for x in capital_rows: families.setdefault(x["pattern"],[]).append(x)

family_stats={}
for p,xs in families.items():
    vals=[x["hybrid"] for x in xs]
    fam_mean,fam_lower=posterior(vals,gmean,12,gvar)
    family_stats[p]={
        "n":len(xs),
        "raw_mean_r":mean(vals),
        "posterior_mean_r":fam_mean,
        "lower_bound_r":fam_lower,
        "pf_r":pf(vals),
        "eligible_support":len(xs)>=FAMILY_MIN_N,
    }

cells={}
for x in capital_rows: cells.setdefault((x["pattern"],x["route"],x["regime"]),[]).append(x)

report={"version":"HarmonyBot V59","method":"hierarchical_partial_pooling_fail_closed","z":Z,"family_min_n":FAMILY_MIN_N,"cell_min_n":CELL_MIN_N,
        "global":{"n":len(global_vals),"mean_r":gmean,"variance":gvar},"families":family_stats,"cells":{},"allowed":[]}
manifest=[]

for (p,route,regime),xs in sorted(cells.items()):
    hv=[x["hybrid"] for x in xs]; bv=[x["baseline"] for x in xs]
    fam=family_stats[p]
    post_mean,lower=posterior(hv,fam["posterior_mean_r"],8,gvar)
    sources={x["source"] for x in xs}
    controls=[y for y in capital_rows if y["source"] in sources and y["route"]==route and y["regime"]==regime and y["pattern"]!=p]
    cv=[y["hybrid"] for y in controls]
    if cv:
        ctrl=mean(cv)
        delta=[v-ctrl for v in hv]
        inc_mean,inc_lower=posterior(delta,0.0,8,gvar)
    else:
        ctrl=0.0; inc_mean=-999.0; inc_lower=-999.0
    hold=mean([x["hold"] for x in xs])
    token=p.replace(" ","_")+"|"+route+"|"+regime
    allowed=(len(xs)>=CELL_MIN_N and fam["n"]>=FAMILY_MIN_N and fam["lower_bound_r"]>0 and
             lower>0 and inc_lower>0 and mean(hv)>=mean(bv) and hold>0 and p!="AB=CD")
    row={"pattern":p,"route":route,"regime":regime,"n":len(xs),"family_n":fam["n"],
         "baseline_mean_r":mean(bv),"hybrid_mean_r":mean(hv),"posterior_mean_r":post_mean,
         "lower_bound_r":lower,"family_lower_bound_r":fam["lower_bound_r"],
         "matched_control_n":len(cv),"matched_control_mean_r":ctrl,
         "incremental_posterior_mean_r":inc_mean,"incremental_lower_bound_r":inc_lower,
         "hybrid_pf_r":pf(hv),"mean_hold_minutes":hold,"allowed":allowed}
    report["cells"][token]=row
    if allowed:
        report["allowed"].append(token)
        manifest.append(f"{token}={lower:.5f},{hold:.2f},{len(xs)}")

(out/"V59_HIERARCHICAL_CALIBRATION_REPORT.json").write_text(json.dumps(report,indent=2))
(out/"calibration_manifest.txt").write_text(";".join(manifest))
summary={"capture_outcomes":len(rows),"research_only_outcomes":len(research_rows),"capital_eligible_outcomes":len(capital_rows),
         "families_observed":sorted(families),"family_support_ge24":sum(v["n"]>=FAMILY_MIN_N for v in family_stats.values()),
         "cells":len(cells),"allowed_cells":len(manifest),"abcd_standalone_allowed":False,
         "fresh_used":False,"decision":"PROCEED_DEV" if manifest else "HOLD_WITH_EVIDENCE"}
(out/"V59_HIERARCHICAL_SUMMARY.json").write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
