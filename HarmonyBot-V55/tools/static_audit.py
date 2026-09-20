#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V51/src/HarmonyBotV51.cs").read_text(errors="ignore")
checks={
"identity":"HarmonyBot V51" in s and "class HarmonyBotV51" in s and 'BotPrefix = "HB51"' in s,
"confirmed_d_m1":"_m1Bars" in s and "ProcessNewM1Close" in s and "TryProjectProfile" not in s,
"joint_geometry":"EnableFamilyNativeJointGeometry" in s and "FamilyNativeJointGeometryScore" in s and "Math.Exp(-.50 * q)" in s,
"canonical_family_manifold":"CanonicalAbcdCoordinate" in s and "EnableCanonicalFamilyContracts" in s,
"native_execution_corridor":"EnableFamilyNativeExecutionCorridor" in s and "Math.Abs(c.Signal.D.Price - stop)" in s,
"anchor_forensics":"V51-ENTRY-ANCHOR-FORENSICS" in s and "UpdateEntryAnchorForensics" in s,
"rr_hard_gate":"SelectCanonicalBasketTarget" in s and "MinimumNetRR" in s,
"risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
"setup_dedupe":"_executedSetupKeys" in s,
"single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
"server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
"fib_grid":"new[] { 0.0, .236, .382, .618 }" in s and "3.0 / 7.0" in s,
"no_projected_d":"TryProjectProfile" not in s,
"no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
out={"version":"HarmonyBot V51","architecture":"FAMILY_NATIVE_MATH_GEOMETRY_ECONOMIC_CONVERSION","checks":checks,"pass":all(checks.values())}
pathlib.Path("V51_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 2)
