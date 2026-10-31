#!/usr/bin/env python3
import json,sys,pathlib
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V36/src/HarmonyBotV36.cs")
s=p.read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V36" in s and "class HarmonyBotV36" in s and 'BotPrefix = "HB36"' in s,
 "fibonacci_harmonic_core":"BuildPatternProfiles" in s and "TryBuildFibonacciGridPlan" in s,
 "multi_timeframe":"TimeFrame.Hour4" in s and "TimeFrame.Hour" in s and "TimeFrame.Minute15" in s and "TimeFrame.Minute" in s,
 "completed_bar_discipline":"LastClosedIndex" in s and "allCompletedBars=true" in s,
 "deferred_candidate_retention":"EnableDeferredCandidateRetention" in s and "SCHEDULER_DEFERRED_KEEP_ALIVE" in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "structured_recall_bounded":"StructuredRecallRoute" in s and "conflict == MtfConflict.CONFLICT" in s and "RecallMinGeometry" in s,
 "aging_priority":"EnableFrequencyAgingPriority" in s and "CandidateAgeRankBoost" in s,
 "exhaustion_evidence":"structurallyExtended = r.ExtensionAtr >= 1.20" in s and "trendNotStrengthening = r.AdxH1Slope <= 0" in s,
 "legacy_confirmation_preserved":"double legacyScore = M1ConfirmationScore" in s and "legacyRequired" in s,
 "capital_gate_default_off":'[Parameter("Capital Feasibility Gate", DefaultValue = false)]' in s,
 "post_fill_kernel":"PostFillSafetyKernel" in s and "GAP_THROUGH_STRUCTURAL_INVALIDATION" in s,
 "risk_reconciliation":"ActualBasketWorstRisk" in s and "ACTUAL_FILL_RISK_BUDGET_BREACH" in s,
 "frozen_fib":"new[] { 0.0, .236, .382, .618 }" in s,
 "frozen_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s and "1.0 / 7.0" in s,
 "no_old_prefix":'"HB351-' not in s and '"HB35-' not in s
}
out={"version":"HarmonyBot V36","checks":checks,"pass":all(checks.values())}
pathlib.Path("V36_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
