#!/usr/bin/env python3
import json,sys,pathlib
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V44/src/HarmonyBotV44.cs")
s=p.read_text(errors="ignore")
base_patterns=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0"]
checks={
 "identity":"HarmonyBot V44" in s and "class HarmonyBotV44" in s and 'BotPrefix = "HB44"' in s,
 "m15_thesis":"primaryPattern=M15" in s and "thesis=M15" in s,
 "m5_execution":"primaryExecution=M5" in s and "ProcessNewM5Close" in s,
 "m1_not_strategy_dependency":"_m1Bars" not in s and "ProcessNewM1Close" not in s,
 "canonical_coordinates":all(x in s for x in ["double adxa = ad / xa;","double xdxa = xd / xa;","double abcd = cd / ab;","double cdxc = cd / Math.Max(xc, 1e-9);"]),
 "academic_contract_switch":"EnableAcademicHarmonicContracts" in s and "BuildLegacyV43PatternProfiles" in s,
 "abcd_hypotheses":all(x in s for x in ['Name = "AB=CD Exact"','Name = "AB=CD Alt 1.27"','Name = "AB=CD Alt 1.618"']),
 "projected_d_engine":"EnableProjectedDPrzEngine" in s and "TryProjectProfile" in s and "PROJECTED_XABC" in s,
 "canonical_prz_cluster":"EnableCanonicalPrzCluster" in s and "TryBuildCanonicalPrzCluster" in s and "PrzDispersionAtr" in s,
 "native_shark_fivezero":"NativeSchema=true" in s and "PatternMode.SHARK" in s and "PatternMode.FIVEZERO" in s,
 "multi_hypothesis":"EnablePatternHypothesisSet" in s and "HypothesisCount" in s and "SelectContextualHypothesis" in s,
 "thesis_routes":all(x in s for x in ["CONTINUATION_PULLBACK","COUNTERTREND_EXHAUSTION","STRUCTURAL_TRANSITION","EnableThesisConsistentRoutes"]),
 "regime_hysteresis":"ApplyRegimeHysteresis" in s and "RegimeHysteresisBars" in s,
 "pattern_native_temporal":"UpdatePatternTemporalState" in s and 'a == "ABCD_COMPLETION"' in s,
 "cross_regime_admission":"CrossRegimeAlphaEligible" in s and "PERSISTENT_TREND" in s,
 "robust_alpha_density":"RobustAlphaDensityScore" in s and "reliability" in s,
 "event_driven_auction":"EnableEventDrivenOpportunityAuction" in s and "[V44-AUCTION]" in s,
 "opportunity_loss_ledger":"EnableOpportunityLossLedger" in s and "[V44-OPPORTUNITY-LOSS]" in s,
 "all_core_profiles":all(('Name = "'+x+'"') in s or ('AddStd("'+x+'"') in s for x in base_patterns),
 "all_in_risk_normalization":"VolumeForAllInRiskBudget" in s and "remainingAllInBudget" in s,
 "completed_bar_discipline":"LastClosedIndex" in s and "allCompletedBars=true" in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "basket_risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "server_protection":"ProtectionType.Absolute" in s and "EnsureServerProtection" in s,
 "frozen_fib":"new[] { 0.0, .236, .382, .618 }" in s,
 "frozen_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s and "1.0 / 7.0" in s,
 "no_recovery_terms":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
out={"version":"HarmonyBot V44","architecture":"CANONICAL_HARMONIC_COMMERCIAL_CONVERGENCE","checks":checks,"pass":all(checks.values())}
pathlib.Path("V44_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
