#!/usr/bin/env python3
import json,sys,pathlib
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V46/src/HarmonyBotV46.cs").read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V46" in s and "class HarmonyBotV46" in s and 'BotPrefix = "HB46"' in s,
 "confirmed_d_m1_kernel":"_m1Bars" in s and "ProcessNewM1Close" in s and "TryProjectProfile" not in s,
 "canonical_setup":"EnableCanonicalSetupIdentity" in s and "_executedSetupKeys" in s,
 "canonical_standard":"double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;" in s,
 "independent_scales":"new[] { 2, 3, 5 }" in s,
 "transition_proof":"actualStructuralTransition" in s,
 "scale_route_gate":"SECONDARY_SCALE_ABCD_ROUTE_REJECT" in s and "signal.PivotScale != M15SwingDepth" in s,
 "temporal_m1":"UpdateM1TemporalEvidence" in s and "M1_TEMPORAL_RESCUE_ADMITTED" in s,
 "armed_grace":"ArmedGraceMinutes" in s and "ArmedGraceApplied" in s,
 "pre_execution_revalidation":"PRE_EXECUTION_REVALIDATION_FAILED" in s and "winner.GridPlan = null;" in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "basket_risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "fib_grid":"new[] { 0.0, .236, .382, .618 }" in s and "3.0 / 7.0" in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
out={"version":"HarmonyBot V46","architecture":"RESTORED_ALPHA_EXECUTION_CONVERSION","checks":checks,"pass":all(checks.values())}
pathlib.Path("V46_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 2)
