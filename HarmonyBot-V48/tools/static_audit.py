#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V48/src/HarmonyBotV48.cs").read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V48" in s and "class HarmonyBotV48" in s and 'BotPrefix = "HB48"' in s,
 "confirmed_d_m1":"_m1Bars" in s and "ProcessNewM1Close" in s and "TryProjectProfile" not in s and "_m5Bars" not in s,
 "canonical_standard":"double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;" in s,
 "v46_scale_route_frozen":"SECONDARY_SCALE_ABCD_ROUTE_REJECT" in s,
 "retracement_lane":"EnableRetracementFamilyActivation" in s and 'p == "Gartley"' in s and 'p == "Bat"' in s,
 "extension_lane":"EnableExtensionFamilyActivation" in s and 'p == "Butterfly"' in s and 'p == "Crab"' in s,
 "closed_m1_evidence":"UpdateDormantFamilyEvidence" in s and "LastClosedIndex(_m1Bars)" in s,
 "no_threshold_sweep":"Dormant Family Evidence Bars" in s and "MinValue = 6, MaxValue = 6" in s,
 "setup_dedupe":"_executedSetupKeys" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "fib_grid":"new[] { 0.0, .236, .382, .618 }" in s and "3.0 / 7.0" in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
out={"version":"HarmonyBot V48","architecture":"HARMONIC_FAMILY_SPECIALIZATION_DORMANT_ALPHA","checks":checks,"pass":all(checks.values())}
pathlib.Path("V48_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 2)
