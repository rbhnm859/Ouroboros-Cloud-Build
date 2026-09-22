#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V58/src/HarmonyBotV58.cs").read_text(errors="ignore")
checks={
"identity":"HarmonyBot V58" in s and "class HarmonyBotV58" in s and 'BotPrefix = "HB57"' in s,
"family_identity_split":"BuildFamilyHypothesisKey" in s and "IdentityKey" in s and "UNDERLYING_GEOMETRY_EXECUTED_BY_" in s,
"bounded_pivot_graph":"EnumerateBoundedPivotSequences" in s and "MaxMicroPivotSkips" in s,
"family_quota":"FamilyDetectionQuota" in s and "FAMILY_QUOTA_SELECTED" in s,
"detector_truth":"V58-DETECTOR-TRUTH" in s and "DetectorTruth" in s,
"family_topology":"TryFamilyTopology" in s,
"projected_prz":"FamilyProjectedPrzCenter" in s and "EnableFamilyNativeProjectedPrz" in s,
"joint_geometry":"FamilyNativeJointGeometryScore" in s,
"rr_hard_gate":"MinimumNetRR" in s and "SelectCanonicalBasketTarget" in s,
"risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
"single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
"server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
"fib_grid":"new[] { 0.0, .236, .382, .618 }" in s and "3.0 / 7.0" in s,
"no_projected_d_primary":"TryProjectProfile" not in s,
"no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
out={"version":"HarmonyBot V58","architecture":"HARMONIC_FAMILY_IDENTITY_DETECTION_GRAPH_RECONSTRUCTION","checks":checks,"pass":all(checks.values())}
pathlib.Path("V58_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 2)
