#!/usr/bin/env python3
import csv,hashlib,json,math,pathlib,statistics,sys
ROOT=pathlib.Path(sys.argv[1]); OUT=pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True,exist_ok=True)
WINDOWS=("Y2021","Y2022","Y2023")
FAMILIES=("Gartley","Bat","AltBat","Butterfly","Crab","DeepCrab","DeepGartley","Rat","Cypher","Shark","FiveZero","ABCD")
KEEP=("cid","setup","family","role","route","lane","core_overlap","capital_eligible",
      "g","prz","conf","ts","pv","m1","rr","reg","eff","atr","ext","mtf","atp","adx1","adx4","adxs",
      "trend","spr","ses","przc","trans","runtime_survival","outcome_r","structural_r","path_state","path_usable",
      "path_success","mfe","mae","time_to_05","time_to_1","time_to_2","time_to_stop","time_to_mfe","giveback_r",
      "result","bars","cost_r")
def stats(rs):
    n=len(rs); vals=[float(x["structural_r"]) for x in rs]
    gp=sum(x for x in vals if x>0); gl=-sum(x for x in vals if x<0); m=sum(vals)/n if n else 0.0
    lcb=m-1.645*statistics.stdev(vals)/math.sqrt(n) if n>1 else -999.0
    return {"n":n,"mean_structural_r":m,"pf_r":gp/gl if gl>0 else (999.0 if gp>0 else 0.0),
            "lcb_r":lcb,"win_rate":sum(x>0 for x in vals)/n if n else 0.0,
            "path_usable":sum(bool(x["path_usable"]) for x in rs),
            "hit_0p5":sum(int(x["time_to_05"])>=0 for x in rs),"hit_1r":sum(int(x["time_to_1"])>=0 for x in rs),
            "hit_2r":sum(int(x["time_to_2"])>=0 for x in rs),"hit_stop":sum(int(x["time_to_stop"])>=0 for x in rs),
            "mean_mfe_r":sum(float(x["mfe"]) for x in rs)/n if n else 0.0,
            "mean_mae_r":sum(float(x["mae"]) for x in rs)/n if n else 0.0,
            "mean_giveback_r":sum(float(x["giveback_r"]) for x in rs)/n if n else 0.0}
events=[]; source_files={}; family_census={}; oracle={}; keys=set()
for window in WINDOWS:
    xs=list(ROOT.rglob(f"SHADOW_PREPASS-{window}.json"))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate shadow {window}: {len(xs)}")
    p=xs[0]; raw=p.read_bytes(); source_files[window]={"sha256":hashlib.sha256(raw).hexdigest(),"path":str(p)}
    d=json.loads(raw.decode())
    family_census[window]=d.get("family_census",{}); oracle[window]=d.get("oracle_summary",{})
    for row in d.get("shadow_outcomes",[]):
        fam=str(row.get("family",""))
        if fam not in FAMILIES: raise SystemExit(f"unknown family key {fam!r} in {window}")
        key=(window,str(row.get("cid","")),fam,str(row.get("setup","")),str(row.get("lane","")))
        if key in keys: raise SystemExit(f"duplicate harmonic event {key}")
        keys.add(key); z={"window":window}
        for k in KEEP: z[k]=row.get(k)
        z["event_id"]=hashlib.sha256(("|".join(key)).encode()).hexdigest()[:24]
        z["observed_only"]=True; z["native_proxy_excluded_from_research_target"]=True
        events.append(z)
coverage={w:{f:family_census[w].get(f,{"tracked":0,"armed":0,"core_overlap":0,"shadow_closed":0}) for f in FAMILIES} for w in WINDOWS}
by_window={w:stats([x for x in events if x["window"]==w]) for w in WINDOWS}
by_family={f:stats([x for x in events if x["family"]==f]) for f in FAMILIES}
by_family_window={f:{w:stats([x for x in events if x["family"]==f and x["window"]==w]) for w in WINDOWS} for f in FAMILIES}
oracle_ok=all(bool(oracle[w].get("perfect_recall",False)) for w in WINDOWS)
coverage_ok=all(all(f in coverage[w] for f in FAMILIES) for w in WINDOWS)
manifest={"schema":"HARMONYBOT_V71_OFFLINE_HARMONIC_EVENT_ATLAS_V1",
 "purpose":"DESCRIPTIVE_BURNED_CALIBRATION_RESEARCH_ONLY","windows":list(WINDOWS),"families":list(FAMILIES),
 "rows":len(events),"source_files":source_files,"oracle":oracle,"detector_family_census":coverage,
 "oracle_perfect_recall_3of3":oracle_ok,"family_namespace_12of12_3of3":coverage_ok,
 "by_window":by_window,"by_family":by_family,"by_family_window":by_family_window,
 "research_ready":bool(events) and oracle_ok and coverage_ok,"capital_decision_used":False,
 "validation_used":False,"fresh_used":False,
 "forbidden_inference":"native_outcome_r/native_result are V51_NATIVE_PROXY telemetry and are not research targets"}
(OUT/"HARMONIC_EVENT_ATLAS.json").write_text(json.dumps({"manifest":manifest,"events":events},indent=2))
(OUT/"HARMONIC_EVENT_ATLAS_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
with open(OUT/"HARMONIC_EVENT_ATLAS.jsonl","w") as f:
    for x in events: f.write(json.dumps(x,separators=(",",":"))+"\n")
if events:
    fields=["event_id","window"]+list(KEEP)
    with open(OUT/"HARMONIC_EVENT_ATLAS.csv","w",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader()
        for x in events: wr.writerow({k:x.get(k) for k in fields})
print(json.dumps(manifest,indent=2))
raise SystemExit(0 if manifest["research_ready"] else 61)
