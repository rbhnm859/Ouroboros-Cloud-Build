#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V67/src/HarmonyBotV67.cs").read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={
 "all_family_profiles":all(('Name = "'+p+'"') in s or ('AddStd("'+p+'"') in s for p in families),
 "multi_label_identity":"BuildFamilyHypothesisKey" in s and 's.PatternName ?? "UNKNOWN"' in s,
 "underlying_execution_dedupe":"_executedSetupKeys.Add(c.SetupKey)" in s,
 "bounded_skip_cap":"skips > maxTotalSkips" in s and "MaxMicroPivotSkips" in s,
 "family_quota_before_execution":"FAMILY_QUOTA_SELECTED" in s,
 "family_arbitration":"V67FamilyPriorityBonus" in s,
 "abcd_completion_primitive":"V67AbcdCompletionConfluence" in s and "COMPLETION_PRIMITIVE" in s,
 "all_family_completion":"IsFamilyCompletionLane" in s and "UpdateFamilyCompletionEvidence" in s,
 "truth_stages":all(x in s for x in ["TOPOLOGY_ATTEMPT","TOPOLOGY_MATCH","RATIO_IDENTITY_PASS","FAMILY_HYPOTHESIS_CREATED"]),
 "no_family_trade_quota":"MaximumFamilyTrades" not in s and "FamilyTradeQuota" not in s,
}
out={"version":"HarmonyBot V67","families":families,"checks":checks,"pass":all(checks.values())}
pathlib.Path("V67_DETECTOR_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2));raise SystemExit(0 if out["pass"] else 4)
