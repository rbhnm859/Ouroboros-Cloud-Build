#!/usr/bin/env python3
import json,sys,pathlib,re
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V44/src/HarmonyBotV44.cs")
s=p.read_text(errors="ignore")
patterns=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={
 "identity":"HarmonyBot V44" in s and "class HarmonyBotV44" in s and 'BotPrefix = "HB42"' in s,
 "m15_thesis":"primaryPattern=M15" in s and "thesis=M15" in s,
 "m5_execution":"primaryExecution=M5" in s and "ProcessNewM5Close" in s,
 "m1_not_strategy_dependency":"_m1Bars" not in s and "ProcessNewM1Close" not in s,
 "canonical_adxa":"double adxa = ad / xa;" in s and "double xdxa = xd / xa;" in s,
 "canonical_cypher":"double cdxc = cd / Math.Max(xc, 1e-9);" in s and "RatioScore(cdxc, .786)" in s,
 "no_ambiguous_xad_field":"public double Xab, Abc, Bcd, Xad;" not in s,
 "multi_scale_pivots":"new[] { 2, 3, 5 }" in s and "EnableMultiScalePivotGraph" in s,
 "setup_key_excludes_pattern":'return "SETUP|" + BuildSetupGeometryKey(s);' in s,
 "pattern_native":"PatternExecutionArchetype" in s and "PatternRoutePrior" in s,
 "logical_physical_grid":"EnableLogicalHarmonicGridAnchor" in s and "LogicalAnchor" in s and "physicalAnchor" in s,
 "opportunity_auction":"EnableOpportunityAuctionWindow" in s and "ExecutableUtc" in s,
 "all_12_profiles":all(('Name = "'+x+'"') in s or ('AddStd("'+x+'"') in s for x in patterns),
 "all_in_risk_normalization":"VolumeForAllInRiskBudget" in s and "remainingAllInBudget" in s,
 "completed_bar_discipline":"LastClosedIndex" in s and "allCompletedBars=true" in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "basket_risk_cap":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "post_fill_kernel":"PostFillSafetyKernel" in s and "ACTUAL_FILL_RISK_BUDGET_BREACH" in s,
 "server_protection":"ProtectionType.Absolute" in s and "EnsureServerProtection" in s,
 "frozen_fib":"new[] { 0.0, .236, .382, .618 }" in s,
 "frozen_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s and "1.0 / 7.0" in s,
 "no_recovery_terms":all(x not in s for x in ["Martingale","Loss Averaging","RecoveryGrid","DCA"]),
}
out={"version":"HarmonyBot V44","architecture":"CANONICAL_HARMONIC_GEOMETRY_OPPORTUNITY_PORTFOLIO","checks":checks,"pass":all(checks.values())}
pathlib.Path("V44_ARCHITECTURE_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
