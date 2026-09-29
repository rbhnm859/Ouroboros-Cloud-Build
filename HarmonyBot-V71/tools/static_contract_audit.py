#!/usr/bin/env python3
import json,pathlib,sys,hashlib,re
p=pathlib.Path(sys.argv[1]); s=p.read_text(errors="ignore")
def between(a,b):
 i=s.find(a); j=s.find(b,i+len(a))
 return s[i:j] if i>=0 and j>i else ""
edge=between("private double V71ExpectedEdge","private double V71ExpectedSlotHours")
execblk=between("private void V71TryExecuteExpansion","// ---------------- Harmonic engine")
checks={
 "identity":"class HarmonyBotV71" in s and 'BotPrefix = "HB71"' in s,
 "trusted_parent":'V51TrustedParent = "1b670a0f43ba8ecaa637febfdacf605b1b146f01"' in s,
 "brace_balance":s.count("{")==s.count("}"),
 "source_complete":len(s)>190000 and "public sealed class PipelineCounter" in s,
 "risk_hard_ceiling":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 5.0)]' in s and '[Parameter("V71 Expansion Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 5.0)]' in s,
 "protected_core_priority":"if (armed.Count == 0)" in s and "V71TryExecuteExpansion(now)" in s and "V71CoreHasActiveThesis" in execblk,
 "separate_expansion_book":"Dictionary<string, V71ExpansionCandidate> _v71Expansion" in s,
 "core_risk_isolated":"V71CandidateRiskPercent" in s and "c.V71Expansion" in s,
 "crossfit_model_runtime":"V71EdgeModelSpec" in s and "V71ExpectedEdge" in s and "EdgeLcb" in s,
 "edge_no_future":all(x not in edge for x in ["ShadowOutcomeR","Mfe","Mae","future","OutcomeR"]),
 "expansion_only_positive_lcb":"e.EdgeLcb > 0" in execblk and "V71CapitalQualificationScore(e) > V71ExpansionMinEdgeLcbR" in execblk,
 "core_preemption":"V71PreemptExpansionForCore" in s and "V51_CORE_PREEMPT" in s and "CORE_PREEMPT" in s,
 "same_setup_capital_blocked":"e.CapitalEligible && !e.CoreOverlapObserved" in execblk and "CoreOverlapObserved = coreOverlap" in s,
 "family_native_expansion_identity":"V71DetectExpansionPatternCandidates" in s and 'V71FamilyKey(x.PatternName) + "|" + BuildSetupGeometryKey(x)' in s,
 "family_balance_before_global_cap":"perFamilyPool" in s and '.GroupBy(x => V71FamilyKey(x.PatternName))' in s and "Never apply a global confidence cap before family balancing" in s,
 "decision_time_regime_refresh":"V71RefreshExpansionDecisionContext(e);" in s and "e.Route = V71ExpansionRoute(e.Signal, e.Conflict, regime);" in s,
 "deterministic_expansion_identity":"V71StableHash32(id)" in s and "private uint V71StableHash32" in s and "GetHashCode()" not in s,
 "runtime_lane_whitelist":"V71AllowedFamilyRouteSpec" in s and "V71FamilyRouteAllowed(e)" in execblk and "_v71AllowedFamilyRoutes.Count == 0" in s,
 "sparse_confirmed_pivot_manifold":"V71SparseLegInsideEnvelope" in s and "int[] hops = { 1, 3 };" in s and "TryMatchProfile(profile" in s,
 "full_family_pivot_lattice":"EnableV71FullFamilyPivotLattice" in s and "new[] { 2, 3, 5, 8 }" in s and "dPos - xPos > 16" in s,
 "overlap_shadow_visible":"Core overlap blocks Capital, not evidence collection" in s and "CapitalEligible = !coreOverlap" in s,
 "entry_exit_label_split":"STRUCTURAL_PATH_PLUS_NATIVE_EXIT_COMPLETED_M1" in s and "NativeExitCaptured" in s and "PathState" in s,
 "family_native_temporal_dag":"EnableV71FamilyNativeConfirmation" in s and "UpdatePatternNativeM1State(i, e.NativeEvidenceState" in s,
 "regime_context_whitelist":"V71AllowedFamilyRouteContextSpec" in s and "V71RegimeContextKey" in s and "_v71AllowedFamilyRouteContexts" in s,
 "dual_head_slot_score":"V71ExpectedSurvival" in s and "e.EdgeLcb * Math.Max(.05, Math.Min(.95, e.SurvivalProbability))" in s,
 "fixed_edge_lcb_threshold":'[Parameter("V71 Expansion Min Edge LCB R", DefaultValue = 0.015' in s,
 "completed_m1":"private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }" in s,
 "minimum_rr":'[Parameter("Minimum Net RR", DefaultValue = 2.0' in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "no_stop_widening":"stopWideningViolations" in s,
 "dst_aware":'ResolveTimeZone("Europe/London"' in s and 'ResolveTimeZone("America/New_York"' in s
}
out={"version":"HarmonyBot V71","audit":"protected_champion_core_crossfit_expansion_fail_closed",
 "source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"checks":checks,"pass":all(checks.values())}
pathlib.Path("V71_STATIC_CONTRACT_AUDIT.json").write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
