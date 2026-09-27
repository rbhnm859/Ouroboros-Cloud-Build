#!/usr/bin/env python3
import json,pathlib,re,sys,hashlib
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V68/src/HarmonyBotV68.cs")
src=p.read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
def between(a,b):
    i=src.find(a); j=src.find(b,i+len(a))
    return src[i:j] if i>=0 and j>i else ""
router=between("private HarmonicRoute RouteSignalFamilyNativeV67","private bool UpdateV67FamilyContractEvidence")
risk=between("private bool ConfigureCapitalExecution","private double EstimatedMargin")
checks={
 "identity":"class HarmonyBotV68" in src and 'BotPrefix = "HB68"' in src,
 "brace_balance":src.count("{")==src.count("}"),
 "all_12_family_contracts":all(('AddV67FamilyContract("'+f+'"') in src for f in families),
 "canonical_enum":"enum CanonicalFamilyId" in src,
 "canonical_mapping":all(('case "'+f+'"') in src for f in families),
 "canonical_signal":"public CanonicalFamilyId FamilyId;" in src,
 "canonical_setup":"public string CanonicalSetupId;" in src,
 "identity_propagates_grid":"CanonicalSetupId = c.CanonicalSetupId" in src and "FamilyId = c.FamilyId" in src,
 "identity_propagates_basket":"CanonicalSetupId = c.CanonicalSetupId" in src and "FamilyId = c.FamilyId" in src,
 "identity_propagates_position":"CanonicalSetupId = basket.CanonicalSetupId" in src and "FamilyId = basket.FamilyId" in src,
 "machine_stable_telemetry":"familyId={2}" in src and "familyId={3}" in src,
 "evidence_preserving_quality":"legacyQualityPass || (EnableV68FamilyExpansion && familyQualityPass)" in src,
 "evidence_preserving_route":"legacyRoute != HarmonicRoute.NO_TRADE" in src,
 "evidence_preserving_confirmation":"c.LegacyConfirmationPassed = legacyConfirmationPass" in src,
 "legacy_rank_preserved":"EnableV67FamilyTradeContracts && !EnableV68EvidencePreservingAdmission" in src,
 "legacy_expiry_preserved":"EnableV67FamilyTradeContracts && !EnableV68EvidencePreservingAdmission" in src,
 "grid_challenger_isolated":"EnableV67FamilyNativeGrid && EnableV68GridChallenger" in src,
 "family_router_separate":"RouteSignalFamilyNativeV67" in src and "V67Contract(s.PatternName)" in router,
 "abcd_completion_role":'"COMPLETION_PRIMITIVE"' in src and "V67_ABCD_CONFLUENCE_ONLY" in src,
 "family_native_grid":"ApplyV67FamilyGridContracts" in src and "GridRiskWeights" in src,
 "grid_cancel_half_r":"basket.PeakR >= GridCancelMfeR" in src and 'CancelBasketPending(basket, "MFE_GRID_CANCEL")' in src,
 "whole_basket_risk_cap":"plan.WorstCaseRisk <= plan.BasketRiskAmount + 1e-8" in risk and "BasketRiskPercent" in src,
 "min_rr_2":'[Parameter("Minimum Net RR", DefaultValue = 2.0' in src and "c.NetRR < MinimumNetRR" in src,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in src,
 "completed_bar_clock":"private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }" in src,
 "runtime_router_no_outcome_leak":all(x not in router for x in ["ShadowMfeR","ShadowMaeR","RealizedNet","PeakR","MaxAdverseR"]),
 "dst_aware":'ResolveTimeZone("Europe/London"' in src and 'ResolveTimeZone("America/New_York"' in src,
 "no_stop_widening_design":"stopWideningViolations" in src and "retryImproves" in src,
}
out={"version":"HarmonyBot V68","audit":"truth_alpha_execution_portfolio_contracts","source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"checks":checks,"pass":all(checks.values())}
pathlib.Path("V68_STATIC_CONTRACT_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
