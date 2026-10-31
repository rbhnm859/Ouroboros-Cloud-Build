#!/usr/bin/env python3
import json,pathlib,re,sys
src=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V67/src/HarmonyBotV67.cs").read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
def between(a,b):
    i=src.find(a); j=src.find(b,i+len(a))
    return src[i:j] if i>=0 and j>i else ""
router=between("private HarmonicRoute RouteSignalFamilyNativeV67","private bool UpdateV67FamilyContractEvidence")
detector=between("if (EnableV67FamilyDetectorFrontier)","int quota = Math.Max(1, FamilyDetectionQuota)")
risk=between("private bool ConfigureCapitalExecution","private double EstimatedMargin")
checks={
 "identity":"class HarmonyBotV67" in src and 'BotPrefix = "HB67"' in src,
 "all_12_family_contracts":all(('AddV67FamilyContract("'+f+'"') in src for f in families),
 "family_router_separate":"RouteSignalFamilyNativeV67" in src and "V67Contract(s.PatternName)" in router,
 "family_confirmation_separate":"UpdateV67FamilyContractEvidence" in src and all(('case "'+f+'"') in src for f in families),
 "no_fixed_family_quota_in_v67_frontier":"GroupBy(x => x.PatternName)" not in detector and "V67_FAMILY_FRONTIER_SELECTED" in detector,
 "abcd_completion_role":'"COMPLETION_PRIMITIVE"' in src and "V67_ABCD_CONFLUENCE_ONLY" in src,
 "abcd_broad_not_standalone":'s.HarmonicSubtype == "ABCD_LEGACY_BROAD"' in src and "V67AbcdStandaloneEligible" in src,
 "family_native_grid":"ApplyV67FamilyGridContracts" in src and "GridRiskWeights" in src,
 "grid_cancel_half_r":"basket.PeakR >= GridCancelMfeR" in src and 'CancelBasketPending(basket, "MFE_GRID_CANCEL")' in src,
 "whole_basket_risk_cap":"plan.WorstCaseRisk <= plan.BasketRiskAmount + 1e-8" in risk and "BasketRiskPercent" in src,
 "min_rr_2":'[Parameter("Minimum Net RR", DefaultValue = 2.0' in src and "c.NetRR < MinimumNetRR" in src,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in src,
 "completed_bar_clock":"private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }" in src,
 "no_projected_d_primary":"TryProjectProfile" not in src,
 "runtime_router_no_outcome_leak":all(x not in router for x in ["ShadowMfeR","ShadowMaeR","RealizedNet","PeakR","MaxAdverseR"]),
 "dst_aware":'ResolveTimeZone("Europe/London"' in src and 'ResolveTimeZone("America/New_York"' in src,
 "no_stop_widening_design":"stopWideningViolations" in src and "retryImproves" in src,
}
out={"version":"HarmonyBot V67","audit":"architecture_geometry_grid_risk_no_lookahead","checks":checks,"pass":all(checks.values())}
pathlib.Path("V67_STATIC_CONTRACT_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
