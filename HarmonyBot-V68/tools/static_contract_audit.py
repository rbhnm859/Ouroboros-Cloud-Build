#!/usr/bin/env python3
import json,pathlib,sys,re
src_path=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V68/src/HarmonyBotV68.cs")
src=src_path.read_text(errors="strict")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
def between(a,b):
    i=src.find(a); j=src.find(b,i+len(a))
    return src[i:j] if i>=0 and j>i else ""
router=between("private HarmonicRoute RouteSignalFamilyNativeV68","private bool UpdateV68FamilyContractEvidence")
confirm=between("private bool UpdateV68FamilyContractEvidence","private bool V68FamilyRouteEvidencePass")
capital=between("private bool ConfigureCapitalExecution","private double EstimatedMargin")
checks={
  "source_nonempty":len(src)>150000,
  "balanced_braces":src.count("{")==src.count("}"),
  "identity":"class HarmonyBotV68" in src and 'BotPrefix = "HB68"' in src,
  "all_12_family_contracts":all(('AddV68FamilyContract("'+f+'"') in src for f in families),
  "v52_supply_trunk_preserved":"var baseRoute = RouteSignal(s, conflict, r);" in router and "if (baseRoute != HarmonicRoute.NO_TRADE) return baseRoute;" in router,
  "family_evidence_additive":"familyPass || legacyScore >= legacyRequired" in src,
  "family_route_evidence_additive":"return legacy || native;" in src,
  "no_strict_family_and_gate":"c.FamilyRejection && c.FamilyReclaim && c.FamilyBos && c.FamilyDisplacement" not in confirm,
  "abcd_completion_role":'"COMPLETION_PRIMITIVE"' in src and "V68_ABCD_CONFLUENCE_ONLY" in src,
  "abcd_broad_not_standalone":'s.HarmonicSubtype == "ABCD_LEGACY_BROAD"' in src and "V68AbcdStandaloneEligible" in src,
  "family_native_grid":"ApplyV68FamilyGridContracts" in src and "GridRiskWeights" in src,
  "grid_l0_nonblocking":"V68_GRID_DEGRADED_TO_L0_FOR_RR" in src and "optional deeper legs may disappear" in capital,
  "grid_cancel_half_r":"basket.PeakR >= GridCancelMfeR" in src and 'CancelBasketPending(basket, "MFE_GRID_CANCEL")' in src,
  "whole_basket_risk_cap":"plan.WorstCaseRisk <= plan.BasketRiskAmount + 1e-8" in capital and "BasketRiskPercent" in src,
  "min_rr_2":'[Parameter("Minimum Net RR", DefaultValue = 2.0' in src and "c.NetRR < MinimumNetRR" in src,
  "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in src,
  "completed_bar_clock":"private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }" in src,
  "no_future_outcome_in_router":all(x not in router for x in ["ShadowMfeR","ShadowMaeR","RealizedNet","PeakR","MaxAdverseR"]),
  "dst_aware":'ResolveTimeZone("Europe/London"' in src and 'ResolveTimeZone("America/New_York"' in src,
  "preexecution_risk_reject_separate":"gridRiskPlanRejections" in src and "actualBasketRiskViolations" in src,
  "no_stop_widening_design":"stopWideningViolations" in src and "retryImproves" in src
}
out={"version":"HarmonyBot V68","audit":"family_evidence_overlay_nonblocking_grid_risk_no_lookahead","checks":checks,"pass":all(checks.values())}
pathlib.Path("V68_STATIC_CONTRACT_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
