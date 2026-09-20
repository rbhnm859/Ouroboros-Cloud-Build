#!/usr/bin/env python3
import json,sys,pathlib,re
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V42/src/HarmonyBotV42.cs")
s=p.read_text(errors="ignore")
patterns=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={
 "identity":"HarmonyBot V42" in s and "class HarmonyBotV42" in s and 'BotPrefix = "HB42"' in s,
 "m15_thesis":"primaryPattern=M15" in s and "thesis=M15" in s,
 "m5_execution":"primaryExecution=M5" in s and "ProcessNewM5Close" in s,
 "m1_not_strategy_dependency":"_m1Bars" not in s and "ProcessNewM1Close" not in s,
 "canonical_candidate_key":"BuildCanonicalCandidateKey" in s and "CanonicalCandidateKey" in s,
 "canonical_dedupe":"_candidates.Values.Any(x => x.CanonicalCandidateKey == canonicalKey)" in s,
 "dual_lane":"CORE_ALPHA" in s and "MARGINAL_RESCUE" in s,
 "all_12_profiles":all(('Name = "'+x+'"') in s or ('AddStd("'+x+'"') in s for x in patterns),
 "all_patterns_grid_configured":all(('ConfigureGrid("'+x+'"') in s for x in patterns),
 "fixed_four_level_logical_grid":"EnablePhysicalGridRealization ? new[] { 0.0, .236, .382, .618 }" in s,
 "frozen_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s and s.count("1.0 / 7.0")>=2,
 "physical_grid_realization":"RoutePhysicalDepthCap" in s and "maxPhysicalDepth" in s,
 "opportunity_queue":"EnableOpportunityQueue" in s and "OPPORTUNITY_QUEUE_SLOT_BLOCKED" in s and "slotRecovered" in s,
 "pattern_native_competition":"EnablePatternNativeExecution" in s and "PatternNativeOpportunityScore" in s and "PatternExecutionArchetype" in s,
 "opportunity_conversion_ledger":"[V42-OPPORTUNITY-CONVERSION]" in s and "[V42-OPPORTUNITY-SUMMARY]" in s,
 "follow_through_engine":"EnableFollowThroughEngine" in s and "FollowThroughScore(Bars" in s,
 "thesis_failure_exit":"EnableThesisFailureExit" in s and "UpdateActiveBasketFollowThrough" in s,
 "pattern_funnel":"[V42-PIPELINE]" in s,
 "all_in_risk_normalization":"VolumeForAllInRiskBudget" in s and "remainingAllInBudget" in s,
 "completed_bar_discipline":"LastClosedIndex" in s and "allCompletedBars=true" in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "basket_risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "post_fill_kernel":"PostFillSafetyKernel" in s and "ACTUAL_FILL_RISK_BUDGET_BREACH" in s,
 "server_protection":"ProtectionType.Absolute" in s and "EnsureServerProtection" in s,
 "no_recovery_terms":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
 "no_old_prefix":'"HB41-' not in s and '"HB40-' not in s
}
out={"version":"HarmonyBot V42","architecture":"MARGINAL_ALPHA_OPPORTUNITY_PATTERN_NATIVE_PORTFOLIO",
     "supported_patterns":patterns,"checks":checks,"pass":all(checks.values())}
pathlib.Path("V42_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
