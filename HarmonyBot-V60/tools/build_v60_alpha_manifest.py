#!/usr/bin/env python3
import json,math,pathlib,re,statistics,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
Z=1.645; FAMILY_GEOM_MIN=24; CELL_GEOM_MIN=8
start_rx=re.compile(r"\[V60-SHADOW-START\]\s+cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+regime=(\S+).*?geometry=([-0-9.]+)\s+projectionErrorAtr=([-0-9.]+)\s+prz=([-0-9.]+)\s+regimeScore=([-0-9.]+)\s+confirmation=([-0-9.]+)\s+alphaScore=([-0-9.]+)")
close_rx=re.compile(r"\[V60-SHADOW-CLOSED\]\s+cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+regime=(\S+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+holdMin=([-0-9.]+)")
cap_rx=re.compile(r"\[V60-CAPTURE-CLOSED\]\s+cid=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+regime=(\S+).*?hybridR=([-0-9.]+)\s+convexR=([-0-9.]+)\s+runnerArmed=(\S+)")
rows=[]
research_markers=("V60_RESEARCH_CONTINUE_PATTERN_QUALITY","V60_RESEARCH_CONTINUE_ROUTER_NO_TRADE","V60_ABCD_NESTED_PARENT_CONFLUENCE_ONLY","SECONDARY_SCALE_ABCD_ROUTE_RESEARCH_ONLY")
for p in sorted(root.rglob("*.log")):
    txt=p.read_text(errors="ignore"); source=p.name
    ro=set()
    for line in txt.splitlines():
        if any(k in line for k in research_markers):
            m=re.search(r"cid=(\S+)",line)
            if m: ro.add(m.group(1))
    starts={m.group(1):{"cid":m.group(1),"setup":m.group(2),"pattern":m.group(3),"route":m.group(4),"regime":m.group(5),
        "geometry":float(m.group(6)),"projection_error":float(m.group(7)),"prz":float(m.group(8)),"regime_score":float(m.group(9)),
        "confirmation":float(m.group(10)),"alpha_score":float(m.group(11)),"source":source,"research_only":m.group(1) in ro} for m in start_rx.finditer(txt)}
    closes={m.group(1):{"baseline":float(m.group(8)),"hold":float(m.group(9)),"mfe":float(m.group(6)),"mae":float(m.group(7))} for m in close_rx.finditer(txt)}
    caps={m.group(1):{"hybrid":float(m.group(5)),"convex":float(m.group(6)),"runner":m.group(7).lower()=="true"} for m in cap_rx.finditer(txt)}
    for cid,x in starts.items():
        if cid in closes and cid in caps:
            x.update(closes[cid]); x.update(caps[cid]); rows.append(x)
if not rows: raise SystemExit("no V60 enriched shadow rows found")

def mean(xs): return sum(xs)/len(xs) if xs else 0.0
def pf(xs):
    gp=sum(x for x in xs if x>0); gl=-sum(x for x in xs if x<0)
    return gp/gl if gl>0 else (999.0 if gp>0 else 0.0)
def collapse(xs,key="convex"):
    g={}
    for x in xs: g.setdefault(x["setup"],[]).append(x)
    return [{"setup":k,"r":mean([z[key] for z in v]),"hold":mean([z["hold"] for z in v])} for k,v in g.items()]
def lower(vals):
    if not vals:return -999.0
    m=mean(vals)
    if len(vals)<2:return -999.0
    sd=statistics.pstdev(vals)
    return m-Z*sd/math.sqrt(len(vals))
def window(x):
    n=x["source"].upper()
    return "C1" if "C1" in n else ("C2" if "C2" in n else ("C3" if "C3" in n else "UNK"))

capital=[x for x in rows if not x["research_only"]]
families={}
for x in capital: families.setdefault(x["pattern"],[]).append(x)
cells={}
for x in capital: cells.setdefault((x["pattern"],x["route"],x["regime"]),[]).append(x)

report={"version":"HarmonyBot V60","method":"cluster_aware_temporal_cross_validation","all_rows":len(rows),
        "research_only_rows":len(rows)-len(capital),"capital_rows":len(capital),"unique_capital_geometries":len({x["setup"] for x in capital}),
        "families":{},"cells":{},"allowed":[]}
manifest=[]
for pat,xs in sorted(families.items()):
    u=collapse(xs)
    vals=[z["r"] for z in u]
    holdouts={}
    for w in ("C1","C2","C3"):
        wrows=[x for x in xs if window(x)==w]
        wu=collapse(wrows)
        holdouts[w]={"unique_n":len(wu),"mean_convex_r":mean([z["r"] for z in wu]),"lower_bound_r":lower([z["r"] for z in wu])}
    report["families"][pat]={"rows":len(xs),"unique_geometries":len(u),"mean_convex_r":mean(vals),"pf_r":pf(vals),
        "lower_bound_r":lower(vals),"holdouts":holdouts}

for key,xs in sorted(cells.items()):
    pat,route,regime=key; u=collapse(xs); vals=[z["r"] for z in u]
    controls=[y for y in capital if y["route"]==route and y["regime"]==regime and y["pattern"]!=pat]
    cu=collapse(controls); ctrl=mean([z["r"] for z in cu])
    deltas=[z["r"]-ctrl for z in u]
    fam=report["families"][pat]
    holdout_positive=all(v["unique_n"]>0 and v["mean_convex_r"]>0 for v in fam["holdouts"].values())
    allowed=(pat!="AB=CD" and fam["unique_geometries"]>=FAMILY_GEOM_MIN and len(u)>=CELL_GEOM_MIN and
             fam["lower_bound_r"]>0 and lower(vals)>0 and lower(deltas)>0 and holdout_positive)
    token=pat.replace(" ","_")+"|"+route+"|"+regime
    row={"rows":len(xs),"unique_geometries":len(u),"mean_convex_r":mean(vals),"pf_r":pf(vals),"lower_bound_r":lower(vals),
         "matched_control_unique_n":len(cu),"matched_control_mean_r":ctrl,"incremental_lower_bound_r":lower(deltas),
         "holdout_family_positive":holdout_positive,"allowed":allowed,"mean_hold_minutes":mean([z["hold"] for z in u])}
    report["cells"][token]=row
    if allowed:
        report["allowed"].append(token)
        manifest.append(f"{token}={row['lower_bound_r']:.5f},{row['mean_hold_minutes']:.2f},{len(u)}")

summary={"capture_outcomes":len(rows),"research_only_outcomes":len(rows)-len(capital),"capital_rows":len(capital),
         "unique_capital_geometries":len({x["setup"] for x in capital}),"cells":len(cells),"allowed_cells":len(manifest),
         "abcd_standalone_allowed":False,"fresh_used":False,"decision":"PROCEED_DEV" if manifest else "HOLD_WITH_EVIDENCE"}
(out/"V60_CLUSTER_ALPHA_REPORT.json").write_text(json.dumps(report,indent=2))
(out/"V60_ALPHA_SUMMARY.json").write_text(json.dumps(summary,indent=2))
(out/"calibration_manifest.txt").write_text(";".join(manifest))
print(json.dumps(summary,indent=2))
