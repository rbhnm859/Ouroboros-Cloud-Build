#!/usr/bin/env python3
import json,pathlib,sys,hashlib,collections,statistics
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
rows=[]
for p in root.rglob("*.json"):
    try:d=json.load(open(p))
    except:continue
    if "basket_outcomes" in d: rows.append(d)

BASE={"V63_CONDITIONAL_EXECUTION","V63_CELL_POLICY_ROUTER","V63_CELL_POLICY_RUNNER"}
def token(s): return str(s or "").strip().replace(" ","_")
def cell_key(pattern,route,regime): return f"{token(pattern)}~{route}~{token(regime)}"

cells=collections.defaultdict(dict); family_policy=collections.defaultdict(dict)
for d in rows:
    if d.get("variant") not in BASE: continue
    w=d.get("window","")
    for x in d.get("cell_outcomes",[]):
        k=(x.get("pattern",""),x.get("route",""),x.get("regime",""),x.get("policy",""))
        setup=x.get("setup","")
        cells[k][setup]=(float(x.get("r",0)),w)
        family_policy[(k[0],k[3])][setup]=float(x.get("r",0))

evidence=[]; candidates=collections.defaultdict(list)
for k,smap in sorted(cells.items()):
    rs=[v[0] for v in smap.values()]; n=len(rs); mean=statistics.mean(rs) if rs else 0
    prior_vals=list(family_policy[(k[0],k[3])].values()); prior=statistics.mean(prior_vals) if prior_vals else 0
    weight=n/(n+8.0); shr=weight*mean+(1-weight)*prior
    by_window=collections.defaultdict(list)
    for r,w in smap.values(): by_window[w].append(r)
    window_mean={w:statistics.mean(v) for w,v in sorted(by_window.items())}
    positive_windows=sum(v>0 for v in window_mean.values())
    on=n>=3 and mean>0 and shr>0 and len(window_mean)>=2 and positive_windows>=2
    row={"pattern":k[0],"route":k[1],"regime":k[2],"policy":k[3],"n":n,"mean_r":mean,
         "family_policy_prior_r":prior,"shrunk_r":shr,"window_mean_r":window_mean,
         "positive_windows":positive_windows,"capital_evidence":"ON" if on else ("SHADOW" if shr>-0.05 else "OFF")}
    evidence.append(row)
    if on: candidates[k[:3]].append(row)

policy_map={}
for cell,opts in candidates.items():
    best=max(opts,key=lambda x:(x["shrunk_r"],x["mean_r"],x["n"]))
    policy_map[cell_key(*cell)]=best["policy"]

def records(variant):
    m={}
    for d in rows:
        if d.get("variant")!=variant: continue
        w=d.get("window","")
        for x in d.get("cell_outcomes",[]):
            m[(w,x.get("setup",""))]=x
    return m

d=records("V63_CELL_POLICY_RUNNER"); e=records("V63_POSITIVE_COHORT_RECOVERY")
recovery=collections.defaultdict(list)
for k,x in e.items():
    if k in d: continue
    recovery[(x.get("pattern",""),x.get("route",""),x.get("regime",""))].append((float(x.get("r",0)),k[0]))
recovery_evidence=[]; recovery_cells=[]
for cell,vals in sorted(recovery.items()):
    rs=[r for r,w in vals]; by=collections.defaultdict(list)
    for r,w in vals: by[w].append(r)
    wm={w:statistics.mean(v) for w,v in sorted(by.items())}; mean=statistics.mean(rs) if rs else 0; pos=sum(v>0 for v in wm.values())
    on=len(rs)>=3 and mean>0 and len(wm)>=2 and pos>=2
    recovery_evidence.append({"pattern":cell[0],"route":cell[1],"regime":cell[2],"n":len(rs),"mean_r":mean,
                              "window_mean_r":wm,"positive_windows":pos,"capital_evidence":"ON" if on else "OFF"})
    if on: recovery_cells.append(cell_key(*cell))

f=records("V63_OCCUPANCY_GOVERNOR")
occupancy=collections.defaultdict(list)
for k,xf in f.items():
    if k not in e: continue
    xe=e[k]; cell=(xf.get("pattern",""),xf.get("route",""),xf.get("regime",""))
    occupancy[cell].append((float(xf.get("r",0))-float(xe.get("r",0)),k[0]))
occupancy_evidence=[]; occupancy_cells=[]
for cell,vals in sorted(occupancy.items()):
    ds=[r for r,w in vals]; by=collections.defaultdict(list)
    for r,w in vals: by[w].append(r)
    wm={w:statistics.mean(v) for w,v in sorted(by.items())}; mean=statistics.mean(ds) if ds else 0; pos=sum(v>0 for v in wm.values())
    on=len(ds)>=3 and mean>0 and len(wm)>=2 and pos>=2
    occupancy_evidence.append({"pattern":cell[0],"route":cell[1],"regime":cell[2],"matched_n":len(ds),
                               "mean_delta_r":mean,"window_mean_delta_r":wm,"positive_windows":pos,
                               "capital_evidence":"ON" if on else "OFF"})
    if on: occupancy_cells.append(cell_key(*cell))

policy_text=";".join(f"{k}#{v}" for k,v in sorted(policy_map.items()))
recovery_text=";".join(sorted(recovery_cells)); occupancy_text=";".join(sorted(occupancy_cells))
frozen={"version":"HarmonyBot V63","calibration_period":"2021-2023 burned",
        "source_policy":"Calibration-generated Family×Route×Regime evidence map","hierarchical_shrinkage_k":8.0,
        "selection_rule":"n>=3, raw mean R>0, shrunk R>0, observed>=2 windows, >=2 positive windows",
        "recovery_rule":"new E-vs-D setups n>=3, mean R>0, observed>=2 windows, >=2 positive windows",
        "occupancy_rule":"F-vs-E matched delta n>=3, mean delta R>0, observed>=2 windows, >=2 positive windows",
        "right_tail_min_ratio":.80,"risk":{"basket_risk_pct":1.0,"min_net_rr":2.0},"fresh_used":False}
payload={"frozen":frozen,"policy_map":policy_map,"recovery_cells":recovery_cells,"occupancy_cells":occupancy_cells}
frozen["config_sha256"]=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
report={"frozen":frozen,"policy_map":policy_map,"recovery_cells":recovery_cells,"occupancy_cells":occupancy_cells,
        "cell_evidence":evidence,"recovery_evidence":recovery_evidence,"occupancy_evidence":occupancy_evidence}
(out/"V63_CALIBRATION_FREEZE.json").write_text(json.dumps(report,indent=2))
(out/"V63_POLICY_MAP.txt").write_text(policy_text)
(out/"V63_RECOVERY_CELLS.txt").write_text(recovery_text)
(out/"V63_OCCUPANCY_CELLS.txt").write_text(occupancy_text)
print(json.dumps({"frozen":frozen,"policy_cells":len(policy_map),"recovery_cells":len(recovery_cells),"occupancy_cells":len(occupancy_cells)},indent=2))
