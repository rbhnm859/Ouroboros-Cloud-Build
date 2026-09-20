#!/usr/bin/env python3
import json,sys,pathlib
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V38/src/HarmonyBotV38.cs")
s=p.read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V38" in s and "class HarmonyBotV38" in s and 'BotPrefix = "HB38"' in s,
 "m15_thesis":"primaryPattern=M15" in s and "thesis=M15" in s,
 "m5_execution":"primaryExecution=M5" in s and "ProcessNewM5Close" in s,
 "m1_not_strategy_dependency":"_m1Bars" not in s and "ProcessNewM1Close" not in s and "M1ConfirmationScore" not in s,
 "evidence_accumulation":"EnableEvidenceAccumulation" in s and "EvidenceCompositeScore" in s and "EvidenceScores" in s,
 "candidate_survival":"EnableCandidateSurvival" in s and "EVIDENCE_BUILDING" in s and "PRZ_TOUCHED" in s,
 "counterfactual_shadow":"CounterfactualShadow" in s and "UpdateCounterfactualShadows" in s and "V38-SHADOW-RESOLVE" in s,
 "opportunity_arbitration":"EnableOpportunityCostArbitration" in s and "OpportunityCostRank" in s,
 "all_in_risk_normalization":"VolumeForAllInRiskBudget" in s and "remainingAllInBudget" in s and "executionRiskRenormalizations" in s,
 "completed_bar_discipline":"LastClosedIndex" in s and "allCompletedBars=true" in s,
 "harmonic_core":"BuildPatternProfiles" in s and "DetectPatternCandidates" in s and "TryBuildFibonacciGridPlan" in s,
 "structured_recall":"StructuredRecallRoute" in s and "EnableStructuredRecallExpansion" in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "basket_risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "post_fill_kernel":"PostFillSafetyKernel" in s and "ACTUAL_FILL_RISK_BUDGET_BREACH" in s,
 "server_protection":"ProtectionType.Absolute" in s and "EnsureServerProtection" in s,
 "frozen_fib":"new[] { 0.0, .236, .382, .618 }" in s,
 "frozen_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s and "1.0 / 7.0" in s,
 "no_recovery_terms":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
 "no_old_prefix":'"HB37-' not in s and '"HB36-' not in s
}
out={"version":"HarmonyBot V38","architecture":"M15_THESIS_M5_EVIDENCE_EXECUTION","checks":checks,"pass":all(checks.values())}
pathlib.Path("V38_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
