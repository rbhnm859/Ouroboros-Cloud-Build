#!/usr/bin/env python3
import json,pathlib,sys,hashlib
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V71/src/HarmonyBotV71.cs")
s=p.read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
def between(a,b):
    i=s.find(a); j=s.find(b,i+len(a))
    return s[i:j] if i>=0 and j>i else ""
portfolio=between("private bool V71EvidenceQualifiedCapitalLane","private bool V71SelectiveQualityRecall")
backfill=between("private bool V71SelectiveBackfillAdmissionEligible","private double V71EffectiveBasketRiskPercent")
adaptive=between("private double V71EffectiveBasketRiskPercent","private bool V71SelectiveQualityRecall")
recall=between("private HarmonicRoute V71SelectiveRecallRoute","private double V70MinimumExecutionEvidenceScore")
grid=between("private bool V71TryGetGridTemplate","private bool GridPlanReject")
checks={
 "identity":"class HarmonyBotV71" in s and 'BotPrefix = "HB71"' in s,
 "brace_balance":s.count("{")==s.count("}"),
 "source_not_truncated":len(s)>250000 and "public sealed class PipelineCounter" in s,
 "all_12_families":all(('case "'+f+'"') in s for f in families),
 "evidence_portfolio":"V71EvidenceQualifiedCapitalLane" in s and 'p == "AB=CD"' in portfolio and 'p == "Rat"' in portfolio and 'p == "Shark"' in portfolio,
 "subtype_aware":all(x in portfolio for x in ['ABCD_EXACT','ABCD_NEAR_127','subtype == "Shark"']),
 "selective_recall_abcd_only":'AB=CD' in recall and 'Cypher' not in recall,
 "protected_rat_shark":'p == "Rat"' in portfolio and 'p == "Shark"' in portfolio,
 "family_native_grid_amplifier":"EnableV71FamilyNativeGridAmplifier" in s and "V71TryGetGridTemplate" in s,
 "grid_is_not_filter":"FAMILY_NATIVE_PROFIT_AMPLIFIER_NOT_FILTER" in s,
 "grid_evidence_lanes":'p == "Rat" && subtype == "Rat"' in grid and 'p == "Shark" && subtype == "Shark"' in grid,
 "grid_fib_levels":all(x in grid for x in [".236",".382",".618"]),
 "grid_risk_ceiling":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 5.0)]' in s and "plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8" in s,
 "selective_backfill":"EnableV71SelectiveBackfill" in s and "V71SelectiveBackfillAdmissionEligible" in s and "V71SelectiveBackfillExecutionEligible" in s,
 "selective_backfill_no_future":all(x not in backfill for x in ["OutcomeR","MfeR","MaeR","ShadowAlphaObservation","_v69Shadow"]),
 "carney_quality_backfill":all(x in backfill for x in ["GeometryQuality >= .72","PrzConfluence >= .72","Confidence >= .68"]),
 "adaptive_risk_5pct_cap":"EnableV71AdaptiveRiskScaling" in s and "Math.Min(5.0" in adaptive and "allocated = 5.0" in adaptive,
 "adaptive_risk_no_future":all(x not in adaptive for x in ["OutcomeR","MfeR","MaeR","ShadowAlphaObservation","_v69Shadow"]),
 "minimum_rr":'[Parameter("Minimum Net RR", DefaultValue = 2.0' in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "completed_bar":"private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }" in s,
 "broker_protection":"BrokerProtectionDistancesValid" in s and "SERVER_PROTECTION_FAIL_CLOSED" in s,
 "dst_aware":'ResolveTimeZone("Europe/London"' in s and 'ResolveTimeZone("America/New_York"' in s,
 "no_future_portfolio":all(x not in portfolio for x in ["OutcomeR","MfeR","MaeR","ShadowAlphaObservation","_v69Shadow"]),
 "no_future_recall":all(x not in recall for x in ["OutcomeR","MfeR","MaeR","ShadowAlphaObservation","_v69Shadow"]),
 "no_future_grid":all(x not in grid for x in ["OutcomeR","MfeR","MaeR","ShadowAlphaObservation","_v69Shadow"]),
 "no_stop_widening":"stopWideningViolations" in s and "retryImproves" in s,
 "v70_blanket_path_available_but_runner_disabled":"EnableV70HardVetoRationalization" in s and "EnableV70FamilyRouteAdmission" in s,
 "minimal_filter_rebase":"EnableV71MinimalFilterRebase" in s and "V71MinimalSignalIntegrityPass" in s and "V71MinimalRoute" in s,
 "minimal_all_family_no_whitelist":all(('p == "'+f+'"') not in between("private bool V71MinimalSignalIntegrityPass","private HarmonicRoute V71MinimalRoute") for f in families),
 "minimal_context_soft":"V71SignalPreservingScore" in s and "MTF_HARD_CONFLICT" in s and "!EnableV71MinimalFilterRebase" in s,
 "minimal_m1_execution_only":"V71MinimalM1ConfirmationPass" in s and "V71_MINIMAL_M1_EXECUTION_CONFIRMATION" in s,
 "nonblocking_grid":"V71BuildPostSelectionExecutionPlan" in s and "V71_GRID_NONBLOCKING_SINGLE_LEG_FALLBACK" in s,
 "single_leg_fallback_risk_bound":"V71BuildSingleLegExecutionPlan" in s and "plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8" in s,
 "signal_preserving_arbitration":"EnableV71SignalPreservingArbitration" in s and "V71SignalPreservingScore" in s,
 "minimal_no_future":all(x not in between("private bool V71MinimalSignalIntegrityPass","// V71 Final Structural Rebase:") for x in ["OutcomeR","MfeR","MaeR","ShadowAlphaObservation","_v69Shadow"])
}
out={"version":"HarmonyBot V71","audit":"minimal_gate_signal_preservation_fail_closed","source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"checks":checks,"pass":all(checks.values())}
pathlib.Path("V71_STATIC_CONTRACT_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
