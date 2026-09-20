#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V49/src/HarmonyBotV49.cs").read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V49" in s and "class HarmonyBotV49" in s and 'BotPrefix = "HB49"' in s,
 "no_projected_d":"TryProjectProfile" not in s,
 "no_m5_primary":"_m5Bars" not in s,
 "counterfactual_ledger":all(x in s for x in ["V49-CF-START","V49-CONFIRM-BAR","V49-CF-SHADOW-BAR","V49-CF]","CfTwoRUtc","CfSlUtc"]),
 "post_terminal_shadow_horizon":all(x in s for x in ["V49CounterfactualHorizonMinutes = 180","UpdateV49CounterfactualBook","CfCandidateTerminalReason","CfShadowComplete"]),
 "order_independent_evidence":all(x in s for x in ["CfRejection && c.CfReclaim","CfSweep && c.CfCloseBackInside","V49EvidenceWindowBars"]),
 "incumbent_abcd_shark_frozen":'return false; // AB=CD and Shark stay on immutable incumbent lane' in s,
 "control_flags_default_off":'[Parameter("Counterfactual Confirmation Audit", DefaultValue = false)]' in s and '[Parameter("V49 Native Evidence Lanes", DefaultValue = false)]' in s,
 "setup_dedupe":"_executedSetupKeys" in s and "EnableCanonicalSetupIdentity" in s,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "server_protection":"EnsureServerProtection" in s and "ProtectionType.Absolute" in s,
 "fib_grid":"new[] { 0.0, .236, .382, .618 }" in s and "3.0 / 7.0" in s and "2.0 / 7.0" in s,
 "no_recovery":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
out={"version":"HarmonyBot V49","architecture":"HARMONIC_FAMILY_CONFIRMATION_KERNEL","checks":checks,"pass":all(checks.values())}
pathlib.Path("V49_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
