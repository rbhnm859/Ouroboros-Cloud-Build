#!/usr/bin/env python3
import json, math, pathlib, re, statistics, sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
rx=re.compile(r"\[V57-SHADOW-CLOSED\]\s+cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+regime=(\S+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+holdMin=([-0-9.]+)\s+reason=(\S+)")
rows=[]
for p in root.rglob("*.log"):
    txt=p.read_text(errors="ignore")
    for q in rx.finditer(txt):
        rows.append({"pattern":q.group(3),"route":q.group(4),"regime":q.group(5),"r":float(q.group(8)),"hold":float(q.group(9)),"source":str(p)})
if not rows: raise SystemExit("no V57 shadow outcomes found")
global_vals=[x["r"] for x in rows]
gmean=statistics.mean(global_vals)
gvar=statistics.pvariance(global_vals) if len(global_vals)>1 else 1.0
families={}
for x in rows: families.setdefault(x["pattern"],[]).append(x)
fam_mean={}
for p,xs in families.items():
    vals=[x["r"] for x in xs]
    fam_mean[p]=(sum(vals)+12*gmean)/(len(vals)+12)
cells={}
for x in rows: cells.setdefault((x["pattern"],x["route"],x["regime"]),[]).append(x)
report={"global":{"n":len(rows),"mean_r":gmean,"sd_r":math.sqrt(max(gvar,0))},"families":{},"cells":{},"allowed":[]}
for p,xs in families.items():
    vals=[x["r"] for x in xs]
    report["families"][p]={"n":len(vals),"raw_mean_r":statistics.mean(vals),"shrunk_mean_r":fam_mean[p],"pf_r":(sum(v for v in vals if v>0)/abs(sum(v for v in vals if v<0))) if sum(v for v in vals if v<0)<0 else (999 if sum(v for v in vals if v>0)>0 else 0)}
manifest=[]
for key,xs in sorted(cells.items()):
    p,route,regime=key; vals=[x["r"] for x in xs]; n=len(vals); raw=statistics.mean(vals)
    hold=statistics.mean([x["hold"] for x in xs])
    shrunk=(sum(vals)+8*fam_mean[p]+8*gmean)/(n+16)
    local_var=statistics.pvariance(vals) if n>1 else gvar
    variance=max(local_var,gvar*.25,1e-6)
    se=math.sqrt(variance/max(1,n+16))
    lower=shrunk-1.28*se
    token=p.replace(" ","_")+"|"+route+"|"+regime
    allowed=n>=5 and lower>0 and hold>0 and p!="AB=CD"
    row={"pattern":p,"route":route,"regime":regime,"n":n,"raw_mean_r":raw,"shrunk_mean_r":shrunk,"lower_bound_r":lower,"mean_hold_minutes":hold,"allowed":allowed}
    report["cells"][token]=row
    if allowed:
        report["allowed"].append(token)
        manifest.append(f"{token}={lower:.5f},{hold:.2f},{n}")
(out/"V57_CALIBRATION_REPORT.json").write_text(json.dumps(report,indent=2))
(out/"calibration_manifest.txt").write_text(";".join(manifest))
(out/"V57_CALIBRATION_SUMMARY.json").write_text(json.dumps({"shadow_outcomes":len(rows),"families_observed":sorted(families),"cells":len(cells),"allowed_cells":len(manifest),"abcd_standalone_allowed":False},indent=2))
print(json.dumps({"shadow_outcomes":len(rows),"families":len(families),"cells":len(cells),"allowed":len(manifest),"global_mean_r":gmean},indent=2))
