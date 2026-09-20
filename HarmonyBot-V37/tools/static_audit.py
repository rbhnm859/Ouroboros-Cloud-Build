#!/usr/bin/env python3
import json,sys,pathlib,re
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V37/src/HarmonyBotV37.cs")
s=p.read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V37" in s and "class HarmonyBotV37" in s and 'BotPrefix = "HB37"' in s,
 "m15_primary":"primaryPattern=M15" in s and "primaryExecution=M15" in s,
 "m1_not_strategy_dependency":"_m1Bars" not in s and "ProcessNewM1Close" not in s and "M1ConfirmationScore" not in s,
 "m5_optional":"EnableM5ExecutionRefinement" in s and "ProcessNewM5Close" in s,
 "htf_structure":"TimeFrame.Hour4" in s and "TimeFrame.Hour" in s and "TimeFrame.Minute15" in s,
 "completed_bar_discipline":"LastClosedIndex" in s and "allCompletedBars=true" in s,
 "harmonic_core":"BuildPatternProfiles" in s and "DetectPatternCandidates" in s and "TryBuildFibonacciGridPlan" in s,
 "structured_recall":"StructuredRecallRoute" in s and "EnableStructuredRecallExpansion" in s,
 "qualified_reroute":"QualifiedDynamicRerouteEligible" in s and "ReevaluateQualifiedRoutes" in s and "conflict == MtfConflict.CONFLICT" in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "basket_risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "post_fill_kernel":"PostFillSafetyKernel" in s and "ACTUAL_FILL_RISK_BUDGET_BREACH" in s,
 "server_protection":"ProtectionType.Absolute" in s and "EnsureServerProtection" in s,
 "frozen_fib":"new[] { 0.0, .236, .382, .618 }" in s,
 "frozen_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s and "1.0 / 7.0" in s,
 "no_recovery_terms":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
 "no_old_prefix":'"HB36-' not in s and '"HB351-' not in s
}
out={"version":"HarmonyBot V37","architecture":"M15_INTRADAY_CORE","checks":checks,"pass":all(checks.values())}
pathlib.Path("V37_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
