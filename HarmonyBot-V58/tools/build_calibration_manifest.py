#!/usr/bin/env python3
import json,math,pathlib,re,statistics,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
shadow_rx=re.compile(r"\[V58-SHADOW-CLOSED\]\s+cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+regime=(\S+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+holdMin=([-0-9.]+)\s+reason=(\S+)")
cap_rx=re.compile(r"\[V58-CAPTURE-CLOSED\]\s+cid=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+regime=(\S+)\s+baselineR=([-0-9.]+)\s+protect75R=([-0-9.]+)\s+be1R=([-0-9.]+)\s+trail125R=([-0-9.]+)\s+timeDecayR=([-0-9.]+)\s+hybridR=([-0-9.]+)\s+mfeR=([-0-9.]+)\s+captureRatio=([-0-9.]+)")
rows=[]
for p in sorted(root.rglob("*.log")):
    txt=p.read_text(errors="ignore"); source=p.name
    research_only=set()
    for line in txt.splitlines():
        if "V58_RESEARCH_CONTINUE_PATTERN_QUALITY" in line or "V58_RESEARCH_CONTINUE_ROUTER_NO_TRADE" in line:
            m=re.search(r"cid=(\S+)",line)
            if m: research_only.add(m.group(1))
    shadows={q.group(1):{"cid":q.group(1),"pattern":q.group(3),"route":q.group(4),"regime":q.group(5),"baseline":float(q.group(8)),"hold":float(q.group(9)),"mfe":float(q.group(6)),"mae":float(q.group(7)),"source":source,"research_only":q.group(1) in research_only} for q in shadow_rx.finditer(txt)}
    for q in cap_rx.finditer(txt):
        cid=q.group(1)
        if cid not in shadows: continue
        x=shadows[cid]
        x.update({"protect75":float(q.group(6)),"be1":float(q.group(7)),"trail125":float(q.group(8)),"time_decay":float(q.group(9)),"hybrid":float(q.group(10))})
        rows.append(x)
if not rows: raise SystemExit("no V58 capture outcomes found")

def mean(xs): return sum(xs)/len(xs) if xs else 0.0
def pf(xs):
    gp=sum(x for x in xs if x>0); gl=abs(sum(x for x in xs if x<0))
    return gp/gl if gl else (999.0 if gp else 0.0)
def shrink_lower(vals,prior_mean,prior_n,global_var,z=1.28):
    n=len(vals); m=(sum(vals)+prior_n*prior_mean)/(n+prior_n)
    lv=statistics.pvariance(vals) if n>1 else global_var
    v=max(lv,global_var*.25,1e-6); se=math.sqrt(v/max(1,n+prior_n))
    return m,m-z*se

research_rows=[x for x in rows if x["research_only"]]
capital_rows=[x for x in rows if not x["research_only"]]
if not capital_rows:
    capital_rows=[]
global_vals=[x["hybrid"] for x in capital_rows]
gmean=mean(global_vals) if global_vals else 0.0
gvar=statistics.pvariance(global_vals) if len(global_vals)>1 else (statistics.pvariance([x["hybrid"] for x in rows]) if len(rows)>1 else 1.0)
families={}
for x in capital_rows: families.setdefault(x["pattern"],[]).append(x)
all_families={}
for x in rows: all_families.setdefault(x["pattern"],[]).append(x)
family_prior={}
for p,xs in families.items():
    vals=[x["hybrid"] for x in xs]
    family_prior[p]=(sum(vals)+12*gmean)/(len(vals)+12)

cells={}
for x in capital_rows: cells.setdefault((x["pattern"],x["route"],x["regime"]),[]).append(x)
report={"global":{"all_shadow_n":len(rows),"research_only_n":len(research_rows),"capital_eligible_n":len(capital_rows),"hybrid_mean_r":gmean,"hybrid_pf_r":pf(global_vals),"baseline_mean_r":mean([x["baseline"] for x in capital_rows]) if capital_rows else 0.0},"families":{},"research_families":{},"cells":{},"allowed":[]}
for p,xs in families.items():
    hv=[x["hybrid"] for x in xs]; bv=[x["baseline"] for x in xs]
    report["families"][p]={"n":len(xs),"baseline_mean_r":mean(bv),"hybrid_mean_r":mean(hv),"hybrid_delta_r":mean(hv)-mean(bv),"hybrid_pf_r":pf(hv),"mean_mfe_r":mean([x["mfe"] for x in xs]),"mean_hold_minutes":mean([x["hold"] for x in xs])}
for p,xs in all_families.items():
    rs=[x for x in xs if x["research_only"]]
    if rs:
        report["research_families"][p]={"n":len(rs),"baseline_mean_r":mean([x["baseline"] for x in rs]),"hybrid_mean_r":mean([x["hybrid"] for x in rs]),"hybrid_pf_r":pf([x["hybrid"] for x in rs])}

manifest=[]
for key,xs in sorted(cells.items()):
    p,route,regime=key; hv=[x["hybrid"] for x in xs]; bv=[x["baseline"] for x in xs]; n=len(xs)
    shrunk,lower=shrink_lower(hv,family_prior[p],8,gvar)
    controls=[y for y in capital_rows if y["source"] in {x["source"] for x in xs} and y["route"]==route and y["regime"]==regime and y["pattern"]!=p]
    cv=[x["hybrid"] for x in controls]
    if cv:
        delta=[v-mean(cv) for v in hv]
        _,inc_lower=shrink_lower(delta,0.0,8,gvar)
        ctrl_mean=mean(cv)
    else:
        inc_lower=-999; ctrl_mean=0
    hold=mean([x["hold"] for x in xs]); token=p.replace(" ","_")+"|"+route+"|"+regime
    allowed=n>=8 and lower>0 and inc_lower>0 and mean(hv)>=mean(bv) and hold>0 and p!="AB=CD"
    row={"pattern":p,"route":route,"regime":regime,"n":n,"baseline_mean_r":mean(bv),"hybrid_mean_r":mean(hv),"hybrid_delta_r":mean(hv)-mean(bv),
         "shrunk_hybrid_mean_r":shrunk,"lower_bound_r":lower,"matched_control_n":len(cv),"matched_control_mean_r":ctrl_mean,
         "incremental_lower_bound_r":inc_lower,"hybrid_pf_r":pf(hv),"mean_hold_minutes":hold,"allowed":allowed}
    report["cells"][token]=row
    if allowed:
        report["allowed"].append(token); manifest.append(f"{token}={lower:.5f},{hold:.2f},{n}")

(out/"V58_CALIBRATION_REPORT.json").write_text(json.dumps(report,indent=2))
(out/"calibration_manifest.txt").write_text(";".join(manifest))
(out/"V58_MATCHED_CONTROL_REPORT.json").write_text(json.dumps({k:v for k,v in report["cells"].items()},indent=2))
(out/"V58_CALIBRATION_SUMMARY.json").write_text(json.dumps({"capture_outcomes":len(rows),"research_only_outcomes":len(research_rows),"capital_eligible_outcomes":len(capital_rows),"families_observed_all":sorted(all_families),"families_observed_capital":sorted(families),"cells":len(cells),"allowed_cells":len(manifest),"global_baseline_mean_r":mean([x["baseline"] for x in capital_rows]) if capital_rows else 0.0,"global_hybrid_mean_r":gmean,"abcd_standalone_allowed":False,"research_only_excluded_from_capital_manifest":True},indent=2))
print(json.dumps({"capture_outcomes":len(rows),"research_only_outcomes":len(research_rows),"capital_eligible_outcomes":len(capital_rows),"families_capital":len(families),"cells":len(cells),"allowed":len(manifest),"global_baseline_mean_r":mean([x["baseline"] for x in capital_rows]) if capital_rows else 0.0,"global_hybrid_mean_r":gmean},indent=2))
