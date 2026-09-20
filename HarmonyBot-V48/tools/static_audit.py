#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V48/src/HarmonyBotV48.cs").read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V48" in s and "class HarmonyBotV48" in s and 'BotPrefix = "HB48"' in s,
 "confirmed_d_m1":"TryProjectProfile" not in s and "_m1Bars" in s and "_m5Bars" not in s,
 "canonical_adxa":"double adxa = ad / xa;" in s and "double xad = EnableCanonicalStandardCoordinates ? adxa : xdxa;" in s,
 "structural_extension_fix":"double deepestD = a.Price + p.XadMax * (x.Price - a.Price);" in s,
 "family_grid_envelope":"FamilyGridSpanEnvelope" in s and "legalMinSpanXa" in s and "legalMaxSpanXa" in s,
 "family_route_matrix":"FamilyRouteCompatible" in s and "FAMILY_ROUTE_INCOMPATIBLE" in s,
 "family_native_execution":"UpdateFamilyNativeM1Evidence" in s and "FAMILY_NATIVE_M1_PASS_" in s,
 "proven_families_preserved":'sig.PatternName == "AB=CD" || sig.PatternName == "Shark" || sig.PatternName == "Cypher"' in s,
 "setup_dedupe":"_executedSetupKeys" in s and "EnableCanonicalSetupIdentity" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "fib_grid":"new[] { 0.0, .236, .382, .618 }" in s and "3.0 / 7.0" in s and "2.0 / 7.0" in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
out={"version":"HarmonyBot V48","architecture":"FAMILY_NATIVE_HARMONIC_PORTFOLIO_REFORM","checks":checks,"pass":all(checks.values())}
pathlib.Path("V48_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 2)
