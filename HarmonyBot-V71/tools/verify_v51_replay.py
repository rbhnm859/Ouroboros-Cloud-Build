#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.parent.mkdir(parents=True,exist_ok=True)
W=["Y2021","Y2022","Y2023"]
def one(pattern):
 xs=list(root.rglob(pattern))
 if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {pattern}: {len(xs)}")
 return json.load(open(xs[0]))
evidence={}; ok=True
for w in W:
 a=one(f"A_V51_PROTECTED_CORE-{w}.json"); r=one(f"V51_REFERENCE-{w}.json")
 data_exact=bool(a.get("data_snapshot_sha256") and a.get("data_snapshot_sha256")==r.get("data_snapshot_sha256"))
 report_exact=bool(a.get("canonical_report_sha256") and a.get("canonical_report_sha256")==r.get("canonical_report_sha256"))
 pipeline_exact=bool(a.get("core_pipeline_sha256") and a.get("core_pipeline_sha256")==r.get("core_pipeline_sha256"))
 passed=data_exact and report_exact and pipeline_exact
 evidence[w]={"pass":passed,"data_snapshot_exact":data_exact,"canonical_report_exact":report_exact,"core_pipeline_exact":pipeline_exact,
  "a_data_snapshot_sha256":a.get("data_snapshot_sha256"),"reference_data_snapshot_sha256":r.get("data_snapshot_sha256"),
  "a_report_sha256":a.get("canonical_report_sha256"),"reference_report_sha256":r.get("canonical_report_sha256"),
  "a_pipeline_sha256":a.get("core_pipeline_sha256"),"reference_pipeline_sha256":r.get("core_pipeline_sha256")}
 ok=ok and passed
result={"version":"HarmonyBot V71","gate":"V51_EXACT_REPLAY_BEFORE_EXPANSION","windows":W,"evidence":evidence,"pass":ok,
 "expansion_allowed":ok,"validation_used":False,"fresh_used":False}
out.write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
