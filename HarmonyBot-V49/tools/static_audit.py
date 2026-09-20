#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V49/src/HarmonyBotV49.cs").read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V49" in s and "class HarmonyBotV49" in s and 'BotPrefix = "HB49"' in s,
 "confirmed_d_m1":"_m1Bars" in s and "ProcessNewM1Close" in s and "TryProjectProfile" not in s and "_m5Bars" not in s,
 "v46_lane_frozen":"provenLane=ABCD_SHARK_CYPHER_FROZEN" in s,
 "canonical_switch":"EnableCanonicalFamilyContracts" in s and "StandardFamilyAbcdCompatible" in s,
 "bat_bc_min_fixed":'AddStd("Bat", .382, .500, .382, .886, 1.618, 2.618' in s,
 "gartley_contract":'AddStd("Gartley", .600, .636' in s and '.770, .800' in s,
 "crab_contract":'AddStd("Crab", .382, .618' in s and '1.58, 1.66' in s,
 "deep_crab_contract":'AddStd("Deep Crab", .875, .900' in s,
 "completion_switch":"EnableFamilyCompletionContract" in s and "FamilyConfirmationWindowBars" in s,
 "evidence_accumulation":"UpdateFamilyCompletionEvidence" in s and "FamilyReclaim" in s and "FamilyBos" in s,
 "same_bar_evidence":"c.FamilySweep |= sweep" in s and "c.FamilyFailedExtension |= failedExtension" in s,
 "fixed_window":'DefaultValue = 6, MinValue = 6, MaxValue = 6' in s,
 "setup_dedupe":"_executedSetupKeys" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "fib_grid":"new[] { 0.0, .236, .382, .618 }" in s and "3.0 / 7.0" in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
out={"version":"HarmonyBot V49","architecture":"PATTERN_NATIVE_COMPLETION_CONTRACT","checks":checks,"pass":all(checks.values())}
pathlib.Path("V49_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)); raise SystemExit(0 if out["pass"] else 2)
