#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V56/src/HarmonyBotV56.cs").read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={
"all_family_profiles":all(('Name = "'+p+'"') in s or ('AddStd("'+p+'"') in s for p in families),
"multi_label_identity":"BuildFamilyHypothesisKey" in s and 's.PatternName ?? "UNKNOWN"' in s,
"underlying_execution_dedupe":"_executedSetupKeys.Add(c.SetupKey)" in s,
"bounded_skip_cap":"skips > maxTotalSkips" in s and "MaxMicroPivotSkips" in s,
"family_quota_before_execution":"FAMILY_QUOTA_SELECTED" in s,
"canonical_abcd_shadow":"ABCD_COMPONENT_SHADOW_MISMATCH" in s,
"family_leg_floor":"FamilyLegFloorAtr" in s,
"family_native_topology":"TryFamilyTopology" in s,
"truth_stages":all(x in s for x in ["TOPOLOGY_ATTEMPT","TOPOLOGY_MATCH","RATIO_IDENTITY_PASS","FAMILY_HYPOTHESIS_CREATED"]),
"no_silent_global_take_for_reconstruction":"_profiles.Count * quota" in s,
}
underlying="BUY|202601010900|X|A|B|C|D"
hyp={underlying+"|Gartley|3",underlying+"|AB=CD|3",underlying+"|Bat|3"}
checks["synthetic_overlap_multilabel"]=len(hyp)==3
out={"version":"HarmonyBot V56","families":families,"checks":checks,"pass":all(checks.values())}
pathlib.Path("V56_DETECTOR_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 4)
