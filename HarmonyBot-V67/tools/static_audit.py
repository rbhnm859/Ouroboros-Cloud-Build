#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V67/src/HarmonyBotV67.cs").read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={
"family_native_router_v2":"V67FamilyNativeRoute" in s and "V67FamilyPriorityBoost" in s,
"abcd_de_dominant":"ABCD_EXACT" in s and "ABCD_NEAR_127" in s and 'return -.02' in s,
"family_specific_context":"V67DmiBiasH4 <= -0.20" in s and "s.GeometryQuality >= .80" in s and "s.PrzConfluence >= .70" in s,
 "identity":"HarmonyBot V67" in s and "class HarmonyBotV67" in s and 'BotPrefix = "HB67"' in s,
 "v52_throughput_core":"EnableFamilyIdentityReconstruction" in s and "EnumerateBoundedPivotSequences" in s and "FamilyDetectionQuota" in s,
 "all_12_families":all(('Name = "'+p+'"') in s or ('AddStd("'+p+'"') in s for p in families),
 "hard_pattern_quality_restored":'Reject(record, "PATTERN_QUALITY")' in s and "V67_FAMILY_IDENTITY_QUALITY_OBSERVATION_ONLY" not in s,
 "single_live_router":"record.Route = RouteSignal(signal, record.Conflict, regime);" in s and "private HarmonicRoute V67FamilyRouteSignal" not in s,
 "family_capital_overlay":"V67FamilyRouteEligible" in s and "V67_FAMILY_SHADOW_ONLY_" in s and "CAPITAL_SHADOW_ONLY" in s,
 "v52_confirmation_live":"return UpdateV52FamilyCompletionEvidenceLegacy(i, c, out score);" in s,
 "legacy_completion_lane":'pattern == "Gartley"' in s and 'pattern == "5-0"' in s and 'pattern == "Shark"' not in s[s.index("private bool IsFamilyCompletionLane"):s.index("private void IncrementCounter")],
 "family_rank_shadow_only":"familyEvidenceShadow" in s and "V67FamilyEvidenceScore(winner)" in s and "rank = .70 * rank" not in s,
 "abcd_not_primary":"COMPLETION_PRIMITIVE" in s and "ABCD_EXACT" in s and "ABCD_NEAR_127" in s,
 "fivezero_shadow_only":"SHADOW_ONLY_NEGATIVE_CALIBRATION" in s and 'if (p == "5-0")' in s,
 "dms_telemetry_only":"V67DirectionalMovement" in s and "V67SignedDmiBias" in s and "V67DmsContextTelemetryEnabled" in s,
 "projected_prz_switch_present":"EnableFamilyNativeProjectedPrz" in s,
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "rr_hard_gate":"MinimumNetRR" in s and "SelectCanonicalBasketTarget" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "no_projected_d_primary":"TryProjectProfile" not in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
 "control_mode":"V67_CONTROL" in s and "V67_PRODUCT" in s,
}
out={"version":"HarmonyBot V67","architecture":"V52_THROUGHPUT_CONTROL_PRESERVING_FAMILY_CAPITAL_OVERLAY","families":families,"checks":checks,"pass":all(checks.values())}
pathlib.Path("V67_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
