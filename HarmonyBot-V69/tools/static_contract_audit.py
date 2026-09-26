#!/usr/bin/env python3
import json,pathlib,sys,re
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V69/src/HarmonyBotV69.cs")
src=p.read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
a=src.find("private bool V69CommercialSurvivalPass")
b=src.find("\n        private ",a+10) if a>=0 else -1
survival=src[a:b if b>a else len(src)] if a>=0 else ""
forbidden=["ShadowMfeR","ShadowMaeR","CompletionAnchorMfeR","CompletionAnchorMaeR","NativeConfirmMfeR","NativeConfirmMaeR"]
checks={
 "identity":"class HarmonyBotV69" in src and 'BotPrefix = "HB69"' in src,
 "all_family_contracts":all(('AddV69FamilyContract("'+f+'"') in src for f in families),
 "all_dedicated_grid_modules":all(('AddV69Grid("'+f+'"') in src for f in families),
 "family_identity_abcd_separation":"if (!EnableFamilyIdentityReconstruction)" in src and "CanonicalAbcdCoordinate" in src,
 "commercial_survival_veto":"V69CommercialSurvivalPass" in src and "V69_COMMERCIAL_SURVIVAL_VETO" in src,
 "survival_preentry_only":bool(survival) and all(x not in survival for x in forbidden),
 "grid_atlas_runtime":"TryBuildV69FamilyGridAtlasPlan" in src and "EnableV69FamilyGridAtlas" in src,
 "route_specific_grid":"TrendFractions" in src and "ExhaustionFractions" in src and "TransitionFractions" in src,
 "positive_throughput_lane":"EnableV69PositiveThroughputExpansion" in src and "V69IsSupplyRecoveryFamily" in src,
 "no_fixed_family_allocation":"NO_FIXED_FAMILY_QUOTA_EACH_FAMILY_MUST_PROVE_OWN_POSITIVE_CONTRIBUTION" in src,
 "whole_basket_risk":'Basket Risk %' in src and "plan.WorstCaseRisk <= plan.BasketRiskAmount + 1e-8" in src,
 "minimum_rr":'[Parameter("Minimum Net RR", DefaultValue = 2.0' in src and "netRr<MinimumNetRR" in src,
 "single_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in src,
 "completed_bars":"private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }" in src,
 "no_projected_d_primary":"TryProjectProfile" not in src,
 "no_recovery":all(x not in src for x in ["Martingale","RecoveryGrid","Loss Averaging"]),
 "abcd_broad_guard":"V69AbcdStandaloneEligible" in src and "V69_ABCD_CONFLUENCE_ONLY" in src,
 "family_scheduler_no_quota":"V69FamilyOpportunityScore" in src,
}
out={"version":"HarmonyBot V69","architecture":"FAMILY_POSITIVE_COHORT_COMMERCIAL_BREAKTHROUGH","checks":checks,"pass":all(checks.values())}
pathlib.Path("V69_STATIC_CONTRACT_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
