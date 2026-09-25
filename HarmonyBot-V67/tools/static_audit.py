#!/usr/bin/env python3
import json,pathlib,sys,re
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V67/src/HarmonyBotV67.cs").read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={
 "identity":"HarmonyBot V67" in s and "class HarmonyBotV67" in s and 'BotPrefix = "HB67"' in s,
 "v52_throughput_core":"EnableFamilyIdentityReconstruction" in s and "EnumerateBoundedPivotSequences" in s and "FamilyDetectionQuota" in s,
 "all_12_families":all(('Name = "'+p+'"') in s or ('AddStd("'+p+'"') in s for p in families),
 "family_native_routes":"V67FamilyRouteEligible" in s and all(x in s for x in ["RETRACEMENT_EXPANSION","EXTENSION_EXPANSION","TRANSITION_EXPANSION"]),
 "family_arbitration":"V67FamilyPriorityBonus" in s and "[V67-FAMILY-ARBITRATION]" in s,
 "all_family_completion":"pattern == \"Shark\"" in s and 'pattern == "Cypher"' in s and 'pattern == "AB=CD"' in s and "UpdateFamilyCompletionEvidence" in s,
 "abcd_not_primary":"COMPLETION_PRIMITIVE" in s and "ABCD_EXACT" in s and "ABCD_NEAR_127" in s,
 "dms_soft_context":"V67DirectionalMovement" in s and "V67SignedDmiBias" in s,
 "projected_prz_not_required":"EnableFamilyNativeProjectedPrz" in s,
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "rr_hard_gate":"MinimumNetRR" in s and "SelectCanonicalBasketTarget" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "no_projected_d_primary":"TryProjectProfile" not in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
 "control_mode":"V67_CONTROL" in s and "V67_PRODUCT" in s,
}
out={"version":"HarmonyBot V67","architecture":"V52_THROUGHPUT_FAMILY_NATIVE_COMMERCIAL_REBASE","families":families,"checks":checks,"pass":all(checks.values())}
pathlib.Path("V67_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
