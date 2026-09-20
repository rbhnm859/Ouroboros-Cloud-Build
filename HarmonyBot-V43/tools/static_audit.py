#!/usr/bin/env python3
import json,sys,pathlib
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V43/src/HarmonyBotV43.cs")
s=p.read_text(errors="ignore")
patterns=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={
 "identity":"class HarmonyBotV43" in s and 'BotPrefix = "HB43"' in s and "HarmonyBot V43" in s,
 "timeframe_architecture":"primaryPattern=M15" in s and "primaryExecution=M5" in s and "m1StrategyDependency=false" in s,
 "completed_bar_discipline":"LastClosedIndex(_m15Bars)" in s and "LastClosedIndex(_m5Bars)" in s,
 "all_12_profiles":all(('Name = "'+x+'"') in s or ('AddStd("'+x+'"') in s for x in patterns),
 "all_12_grid_contracts":all(('ConfigureGrid("'+x+'"') in s for x in patterns),
 "canonical_candidate_key":"BuildCanonicalCandidateKey" in s and "CanonicalCandidateKey" in s,
 "multiscale_discovery":"EnableMultiScalePatternDiscovery" in s and "CollectPatternMatchesForDepth" in s and "depth + 2" in s,
 "pattern_diversity":"EnablePatternDiversityAdmission" in s and ".GroupBy(x => x.PatternName)" in s,
 "ratio_matcher_preserved":"TryMatchProfile" in s and "InRange(xab, p.XabMin, p.XabMax)" in s and "InRange(xad, p.XadMin, p.XadMax)" in s,
 "structural_grid_eligibility":"EnableStructuralGridEligibility" in s and "legacySpanEligible" in s and "stage=SPAN_XA result=BYPASS" in s,
 "prz_synchronous_completed_bar":"EnablePrzSynchronousEvidence" in s and "PRZ_TOUCHED_" in s and "_przSynchronousStarts" in s,
 "fixed_four_level_grid":"new[] { 0.0, .236, .382, .618 }" in s,
 "fixed_grid_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s and s.count("1.0 / 7.0")>=2,
 "all_in_risk":"VolumeForAllInRiskBudget" in s and "remainingAllInBudget" in s,
 "basket_risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "server_protection":"ProtectionType.Absolute" in s and "EnsureServerProtection" in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "min_volume_fail_closed":"VolumeInUnitsMin" in s and "NormalizeVolumeInUnits" in s,
 "margin_fail_closed":"EstimatedMargin" in s and "MinFreeMarginRiskMultiple" in s,
 "no_recovery_terms":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
 "no_old_prefix":'"HB42-' not in s and 'BotPrefix = "HB42"' not in s
}
out={"version":"HarmonyBot V43","architecture":"MULTISCALE_HARMONIC_DISCOVERY_POSITIVE_ALPHA_EXECUTION",
     "supported_patterns":patterns,"pattern_contract_coverage":sum(checks["all_12_profiles"] and checks["all_12_grid_contracts"] for _ in [0])*12,
     "checks":checks,"pass":all(checks.values())}
pathlib.Path("V43_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
