#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V67/src/HarmonyBotV67.cs").read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
route_family_checks=[
 'p == "Gartley"','p == "Bat"','p == "Alt Bat"','p == "Butterfly"',
 'p == "Crab"','p == "Deep Crab"','p == "Deep Gartley"','p == "Rat"',
 'p == "Cypher"','p == "Shark"','p == "5-0"','p == "AB=CD"'
]
completion_family_checks=[
 'p == "Gartley"','p == "Bat"','p == "Alt Bat"','p == "Butterfly"',
 'p == "Crab"','p == "Deep Crab"','p == "Deep Gartley"','p == "Rat"',
 'p == "Cypher"','p == "Shark"','p == "5-0"','p == "AB=CD"'
]
checks={
 "identity":"HarmonyBot V67" in s and "class HarmonyBotV67" in s and 'BotPrefix = "HB67"' in s,
 "v52_throughput_core":"EnableFamilyIdentityReconstruction" in s and "EnumerateBoundedPivotSequences" in s and "FamilyDetectionQuota" in s,
 "all_12_families":all(('Name = "'+p+'"') in s or ('AddStd("'+p+'"') in s for p in families),
 "family_native_routes":"V67FamilyRouteSignal" in s and "V67FamilyRouteEligible" in s and all(x in s for x in route_family_checks),
 "family_arbitration":"V67FamilyEvidenceScore" in s and "[V67-FAMILY-ARBITRATION]" in s and
                      "No family receives a fixed quota or fixed historical-performance bonus" in s,
 "all_family_completion":"UpdateFamilyCompletionEvidence" in s and
                         "UpdateV52FamilyCompletionEvidenceLegacy" in s and
                         all(x in s for x in completion_family_checks),
 "abcd_not_primary":"COMPLETION_PRIMITIVE" in s and "ABCD_EXACT" in s and "ABCD_NEAR_127" in s and "selective && aligned" in s,
 "dms_soft_context":"V67DirectionalMovement" in s and "V67SignedDmiBias" in s,
 "projected_prz_switch_present":"EnableFamilyNativeProjectedPrz" in s,
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "rr_hard_gate":"MinimumNetRR" in s and "SelectCanonicalBasketTarget" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "no_projected_d_primary":"TryProjectProfile" not in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
 "control_mode":"V67_CONTROL" in s and "V67_PRODUCT" in s and "UpdateV52FamilyCompletionEvidenceLegacy" in s,
 "control_product_route_split":"V67ProductEnabled()" in s and "V67FamilyRouteSignal" in s and "RouteSignal(signal" in s,
}
out={"version":"HarmonyBot V67","architecture":"V52_THROUGHPUT_FAMILY_NATIVE_COMMERCIAL_REBASE","families":families,"checks":checks,"pass":all(checks.values())}
pathlib.Path("V67_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
