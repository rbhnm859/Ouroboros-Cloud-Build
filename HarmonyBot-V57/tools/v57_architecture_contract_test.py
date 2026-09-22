from pathlib import Path
s=Path("HarmonyBot-V57/src/HarmonyBotV57.cs").read_text(encoding="utf-8")
checks={
"identity":"class HarmonyBotV57" in s and 'BotPrefix = "HB57"' in s,
"v51_risk":'[Parameter("Basket Risk %", DefaultValue = 1.0' in s and 'DefaultValue = 2.0' in s,
"v52_identity":"BuildFamilyHypothesisKey" in s and "EnumerateBoundedPivotSequences" in s and "FamilyDetectionQuota" in s,
"family_books":"_familyBooks" in s and "InitializeV57FamilyBooks" in s,
"parallel_shadow":"FamilyShadowTrade" in s and "V57-SHADOW-CLOSED" in s and "StartV57FamilyShadowTrade" in s,
"calibration":"V57CalibrationManifest" in s and "V57CalibratedCapitalEligible" in s,
"abcd_primitive":"EnableV57AbcdStandaloneCapital" in s,
"two_stage":"EnableV57FamilyRepresentativeArbitration" in s and "GroupBy(c => c.Signal == null ? \"UNKNOWN\" : c.Signal.PatternName)" in s,
"slot_efficiency":"CalibratedRPerSlotHour" in s and "V57FamilyCapitalScore" in s,
"legacy_grid_only":"EnableV57GridExecution" in s and "FamilyGridFractionsV4" not in s,
"no_v56_proxy":"ExpectedNetRProxy" not in s and "CommercialMarginProxy" not in s,
}
bad=[k for k,v in checks.items() if not v]
print({"version":"HarmonyBot V57","checks":checks,"pass":not bad})
if bad: raise SystemExit("V57 contract FAIL: "+",".join(bad))
