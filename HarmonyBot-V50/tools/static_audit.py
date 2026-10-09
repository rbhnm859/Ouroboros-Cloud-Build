#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V50/src/HarmonyBotV50.cs").read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V50" in s and "class HarmonyBotV50" in s and 'BotPrefix = "HB50"' in s,
 "confirmed_d_m1":"_m1Bars" in s and "ProcessNewM1Close" in s and "TryProjectProfile" not in s,
 "completion_contract":"UpdateFamilyCompletionEvidence" in s and "EnableFamilyCompletionContract" in s,
 "grid_span_switch":"EnableGridSpanSemanticV2" in s and "LEGACY_XA_SPAN" in s,
 "structural_switch":"EnableStructuralInvalidationV2" in s,
 "extension_coordinate_fix":"x.Price + (1.0 - p.XadMax) * xa" in s and "x.Price - (1.0 - p.XadMax) * xa" in s,
 "grid_reject_telemetry":"GridPlanReject" in s and "V50-GRID-REJECT-SUMMARY" in s,
 "no_v2_minspan_gate":"!EnableGridSpanSemanticV2 && (spanXa < p.MinimumGridSpanXa || spanXa > p.MaximumGridSpanXa)" in s,
 "prz_legality":"price < legalLow || price > legalHigh" in s,
 "target_rr":"SelectCanonicalBasketTarget" in s and "MinimumNetRR" in s,
 "setup_dedupe":"_executedSetupKeys" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "fib_grid":"new[] { 0.0, .236, .382, .618 }" in s and "3.0 / 7.0" in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
out={"version":"HarmonyBot V50","architecture":"PATTERN_NATIVE_STRUCTURAL_GRID_CONTRACT","checks":checks,"pass":all(checks.values())}
pathlib.Path("V50_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 2)
