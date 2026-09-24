#!/usr/bin/env python3
import json,pathlib,sys,collections
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True); rows=[]
for p in root.rglob("*.json"):
 try:d=json.load(open(p))
 except Exception:continue
 if "basket_outcomes" not in d:continue
 for r in d["basket_outcomes"]: rows.append({"window":d.get("window"),"variant":d.get("variant"),"setup":r.get("setup"),"pattern":r.get("pattern"),"route":r.get("route"),"r":r.get("r",0),"net":r.get("net",0)})
g=collections.defaultdict(list)
for r in rows:g[(r["variant"],r["pattern"],r["route"])].append(r)
cells=[]
for (v,p,r),xs in sorted(g.items()):
 vals=[x["r"] for x in xs]; geos={x["setup"] for x in xs}; wins={x["window"] for x in xs if x["window"]}; cells.append({"variant":v,"pattern":p,"route":r,"rows":len(xs),"unique_geometries":len(geos),"windows":sorted(wins),"mean_r":sum(vals)/len(vals) if vals else 0})
rep={"version":"HarmonyBot V62","rows":len(rows),"cells":cells,"cluster_key":"setup","fresh_used":False}; (out/"V62_CLUSTER_EVIDENCE.json").write_text(json.dumps(rep,indent=2)); print(json.dumps(rep,indent=2))
