#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V67/src/HarmonyBotV67.cs").read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]

family_route=s[s.index("private bool V67FamilyRouteEligible"):s.index("private double V67FamilyPriorityBoost")]
family_priority=s[s.index("private double V67FamilyPriorityBoost"):s.index("private double V67FamilyEvidenceScore")]
family_completion=s[s.index("private bool UpdateFamilyCompletionEvidence"):s.index("private void IncrementCounter")]
scheduler=s[s.index("private void TryScheduleAndExecute"):s.index("private void ParkArmedCandidates")]

posthoc_literals=[
    "V67DmiBiasH4 <= -0.20",
    "s.PrzConfluence >= .69",
    "s.PrzConfluence >= .70",
    "s.PrzConfluence >= .75",
    "s.GeometryQuality >= .80",
    "s.GeometryQuality >= .82",
    "s.PrzConfluence >= .64",
    "s.PrzConfluence >= .68"
]

checks={
 "identity":"HarmonyBot V67" in s and "class HarmonyBotV67" in s and 'BotPrefix = "HB67"' in s,
 "v52_throughput_core":"EnableFamilyIdentityReconstruction" in s and "EnumerateBoundedPivotSequences" in s and "FamilyDetectionQuota" in s,
 "all_12_families":all(('Name = "'+p+'"') in s or ('AddStd("'+p+'"') in s for p in families),
 "hard_pattern_quality_restored":'Reject(record, "PATTERN_QUALITY")' in s,
 "v52_live_router_preserved":"record.Route = RouteSignal(signal, record.Conflict, regime);" in s and "V67FamilyNativeRoute" not in s,
 "family_capital_overlay":"V67FamilyRouteEligible" in s and "V67_FAMILY_SHADOW_ONLY_" in s and "CAPITAL_SHADOW_ONLY" in s,
 "no_posthoc_family_profit_thresholds":all(x not in family_route for x in posthoc_literals),
 "family_native_m1_contracts":all(x in family_completion for x in ['p == "Shark"','p == "Cypher"','p == "AB=CD"',"FamilyReclaim","FamilyBos","FamilyFailedExtension"]),
 "same_thesis_evidence_arbitration":"GroupBy" in scheduler and "V67FamilyEvidenceScore" in scheduler and "ThenByDescending" in scheduler,
 "no_fixed_family_share_boost":"return 0;" in family_priority and 'return .11' not in family_priority and 'return -.02' not in family_priority,
 "abcd_de_dominant":all(x in s for x in ["COMPLETION_PRIMITIVE","ABCD_EXACT","ABCD_NEAR_127"]) and
                      'p == "AB=CD"' in family_completion and "V67FamilyEvidenceScore" in scheduler,
 "fivezero_shadow_only":"SHADOW_ONLY_NEGATIVE_CALIBRATION" in s and 'if (p == "5-0")' in family_route and "return false;" in family_route,
 "dms_soft_context":"V67DirectionalMovement" in s and "V67SignedDmiBias" in s and "dmiSoft" in s and "V67DmsContextTelemetryEnabled" in s,
 "legacy_completion_preserved":"UpdateV52FamilyCompletionEvidenceLegacy" in s,
 "projected_prz_switch_present":"EnableFamilyNativeProjectedPrz" in s,
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "rr_hard_gate":"MinimumNetRR" in s and "SelectCanonicalBasketTarget" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "no_projected_d_primary":"TryProjectProfile" not in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
 "control_mode":"V67_CONTROL" in s and "V67_PRODUCT" in s,
}
out={"version":"HarmonyBot V67","architecture":"V52_THROUGHPUT_FAMILY_EVIDENCE_ARBITRATION","families":families,"checks":checks,"pass":all(checks.values())}
pathlib.Path("V67_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
