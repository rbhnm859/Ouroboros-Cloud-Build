#!/usr/bin/env python3
import json,pathlib,sys,re
src=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V68/src/HarmonyBotV68.cs").read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={
 "identity":"class HarmonyBotV68" in src and 'BotPrefix = "HB68"' in src,
 "all_family_contracts":all(('AddV68FamilyContract("'+f+'"') in src for f in families),
 "all_dedicated_grid_modules":all(('AddV68Grid("'+f+'"') in src for f in families),
 "grid_atlas_runtime":"TryBuildV68FamilyGridAtlasPlan" in src and "EnableV68FamilyGridAtlas" in src,
 "family_geometry_bases":all(x in src for x in ['"D_STOP"','"CD"','"XC"','"BC"','"AB"']),
 "route_specific_grid":"TrendFractions" in src and "ExhaustionFractions" in src and "TransitionFractions" in src,
 "family_specific_ttl":"PendingTtlMinutes" in src and "CancelPendingAtMfeR" in src,
 "positive_throughput_lane":"EnableV68PositiveThroughputExpansion" in src and "V68IsSupplyRecoveryFamily" in src,
 "no_fixed_family_allocation":"NO_FIXED_FAMILY_QUOTA_EACH_FAMILY_MUST_PROVE_OWN_POSITIVE_CONTRIBUTION" in src,
 "whole_basket_risk":'Basket Risk %' in src and "plan.WorstCaseRisk <= plan.BasketRiskAmount + 1e-8" in src,
 "minimum_rr":'[Parameter("Minimum Net RR", DefaultValue = 2.0' in src and "netRr<MinimumNetRR" in src,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in src,
 "completed_bars":"private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }" in src,
 "no_projected_d_primary":"TryProjectProfile" not in src,
 "no_recovery":all(x not in src for x in ["Martingale","RecoveryGrid","Loss Averaging"]),
 "abcd_broad_guard":"V68AbcdStandaloneEligible" in src and "V68_ABCD_CONFLUENCE_ONLY" in src,
 "family_scheduler_no_quota":"V68FamilyOpportunityScore" in src,
}
out={"version":"HarmonyBot V68","architecture":"HARMONIC_FAMILY_GRID_ATLAS_POSITIVE_THROUGHPUT_REBASE","checks":checks,"pass":all(checks.values())}
pathlib.Path("V68_STATIC_CONTRACT_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
