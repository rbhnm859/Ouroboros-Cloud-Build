#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V54/src/HarmonyBotV54.cs").read_text(errors="ignore")
checks={
"universal_liberation":"EnableUniversalHarmonicLiberation" in s and "LIBERATION_QUALITY_VECTOR_CONTINUE" in s and "LiberationDiagnosticRoute" in s,
"core_preservation":"EnableCoreAlphaPreservation" in s and "CoreAlphaPreservationScore" in s,
"grid_v3":"EnableFamilyGridAlphaCoreV3" in s and "FamilyGridFractionsV3" in s and "FamilyGridRiskWeightsV3" in s,
"state_aware_grid":"EnableStateAwareGridV3" in s and "FamilyGridCancelMfeR" in s,
"rr_immutable":'Minimum Net RR' in s and 'DefaultValue = 2.0' in s,
"risk_immutable":'BasketRiskAmount = Account.Equity * BasketRiskPercent / 100.0' in s,
"no_recovery":all(x not in s for x in ["MartingaleMultiplier","LossAveragingMultiplier","RecoveryMultiplier"]),
"v52_detector_preserved":"EnableFamilyIdentityReconstruction" in s and "EnableBoundedPivotGraph" in s and "FamilyDetectionQuota" in s,
"conversion_truth":"V54-CONVERSION-TRUTH" in s and "ConversionTruth" in s}
out={"version":"HarmonyBot V54","checks":checks,"pass":all(checks.values())};pathlib.Path("V54_ARCHITECTURE_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));raise SystemExit(0 if out["pass"] else 7)
