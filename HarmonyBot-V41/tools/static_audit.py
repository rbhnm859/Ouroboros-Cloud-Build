#!/usr/bin/env python3
import json,sys,pathlib
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V41/src/HarmonyBotV41.cs")
s=p.read_text(errors="ignore")
checks={
 "identity":"HarmonyBot V41" in s and "class HarmonyBotV41" in s and 'BotPrefix = "HB41"' in s,
 "m15_thesis":"primaryPattern=M15" in s and "thesis=M15" in s,
 "m5_execution":"primaryExecution=M5" in s and "ProcessNewM5Close" in s,
 "m1_not_strategy_dependency":"_m1Bars" not in s and "ProcessNewM1Close" not in s and "M1ConfirmationScore" not in s,
 "canonical_candidate_key":"BuildCanonicalCandidateKey" in s and "CanonicalCandidateKey" in s,
 "canonical_dedupe":"_candidates.Values.Any(x => x.CanonicalCandidateKey == canonicalKey)" in s,
 "dual_lane":"CORE_ALPHA" in s and "MARGINAL_RESCUE" in s and "EnableMarginalRescueLane" in s,
 "rescue_is_evidence_failed_only":"if (evidencePass)" in s and "MarginalRescueEligible" in s,
 "opportunity_cost_model":"EnableOpportunityCostEdgeModel" in s and "profitDensityProxy" in s,
 "follow_through_engine":"EnableFollowThroughEngine" in s and "FollowThroughScore(Bars" in s,
 "thesis_failure_exit":"EnableThesisFailureExit" in s and "UpdateActiveBasketFollowThrough" in s,
 "attribution_outcome_has_key_lane":"[V41-ATTRIBUTION-OUTCOME]" in s and "key={1} lane={2}" in s,
 "pattern_funnel":"[V41-PIPELINE]" in s,
 "counterfactual_shadow":"CounterfactualShadow" in s and "UpdateCounterfactualShadows" in s,
 "all_in_risk_normalization":"VolumeForAllInRiskBudget" in s and "remainingAllInBudget" in s,
 "completed_bar_discipline":"LastClosedIndex" in s and "allCompletedBars=true" in s,
 "harmonic_core":"BuildPatternProfiles" in s and "DetectPatternCandidates" in s and "TryBuildFibonacciGridPlan" in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "basket_risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "post_fill_kernel":"PostFillSafetyKernel" in s and "ACTUAL_FILL_RISK_BUDGET_BREACH" in s,
 "server_protection":"ProtectionType.Absolute" in s and "EnsureServerProtection" in s,
 "frozen_fib":"new[] { 0.0, .236, .382, .618 }" in s,
 "frozen_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s and "1.0 / 7.0" in s,
 "no_recovery_terms":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
 "no_old_prefix":'"HB40-' not in s and '"HB39-' not in s
}
out={"version":"HarmonyBot V41","architecture":"CROSS_VALIDATED_MARGINAL_ALPHA_PATTERN_PORTFOLIO","checks":checks,"pass":all(checks.values())}
pathlib.Path("V41_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
