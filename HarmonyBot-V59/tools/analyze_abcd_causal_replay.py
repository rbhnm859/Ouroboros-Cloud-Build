#!/usr/bin/env python3
import csv, json, pathlib, sys
# Input CSV columns are intentionally version-neutral so V45/V51/V52/V53/V55/V57/V58/V59
# exports can be joined without giving a later version privileged semantics.
inp=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader(inp.open()))
required={"version","underlying_geometry_id","pattern","subtype","pivot_scale","route","detected","entered","mfe_r","mae_r","realized_r","exit_policy"}
if not rows: raise SystemExit("empty causal replay input")
missing=required-set(rows[0])
if missing: raise SystemExit("missing columns: "+",".join(sorted(missing)))
groups={}
for r in rows:
    if r["pattern"]!="AB=CD": continue
    groups.setdefault(r["underlying_geometry_id"],[]).append(r)
effects={"geometry_count":len(groups),"detector_population_changes":0,"entry_changes":0,"exit_sign_changes":0,"route_changes":0,"subtype_changes":0}
for g,xs in groups.items():
    xs=sorted(xs,key=lambda r:r["version"])
    if len({r["detected"] for r in xs})>1: effects["detector_population_changes"]+=1
    if len({r["entered"] for r in xs})>1: effects["entry_changes"]+=1
    if len({(float(r["realized_r"])>0) for r in xs})>1: effects["exit_sign_changes"]+=1
    if len({r["route"] for r in xs})>1: effects["route_changes"]+=1
    if len({r["subtype"] for r in xs})>1: effects["subtype_changes"]+=1
(out/"V59_ABCD_CAUSAL_REPLAY_SUMMARY.json").write_text(json.dumps(effects,indent=2))
print(json.dumps(effects,indent=2))
