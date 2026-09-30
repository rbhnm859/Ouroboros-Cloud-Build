#!/usr/bin/env python3
import json,pathlib,sys,hashlib
p=pathlib.Path(sys.argv[1]); s=p.read_text(errors="ignore")
def between(a,b):
 i=s.find(a); j=s.find(b,i+len(a))
 return s[i:j] if i>=0 and j>i else ""
execblk=between("private void V71TryExecuteExpansion","// ---------------- Harmonic engine")
checks={
 "identity":"class HarmonyBotV71" in s and 'BotPrefix = "HB71"' in s,
 "trusted_parent":'V51TrustedParent = "1b670a0f43ba8ecaa637febfdacf605b1b146f01"' in s,
 "brace_balance":s.count("{")==s.count("}"),
 "source_complete":len(s)>190000 and "public sealed class PipelineCounter" in s,
 "risk_hard_ceiling":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 5.0)]' in s and '[Parameter("V71 Expansion Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 5.0)]' in s,
 "protected_core_priority":"V71CoreHasActiveThesis" in execblk and "V51_CORE_PREEMPT" in s,
 "same_setup_capital_blocked":"e.CapitalEligible && !e.CoreOverlapObserved" in execblk and "CapitalEligible = !coreOverlap" in s,
 "frozen_detector_present":"V71DetectExpansionPatternCandidates" in s and "fullFamilies = _profiles.ToList()" in s,
 "projected_prz_no_future":"Pure projected PRZ for Expansion" in s and "if (d.Price < przLow || d.Price > przHigh) return false;" in s,
 "completed_m1":"private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }" in s,
 "bifurcation_master":'[Parameter("Enable V72 Bifurcation Alpha", DefaultValue = false)]' in s and "EnableV72BifurcationAlpha" in execblk,
 "exhaustion_lane":'"EXHAUSTION_REVERSAL"' in s and "V72PreparePullbackEntry" in s,
 "trend_shadow_proof":"V72PrepareTrendVirtualProof" in s and "proofR=0.500" in s and "V72-TREND-PROOF-CONFIRMED" in s,
 "trend_reload_0618":"V72PrepareTrendReload" in s and "proof - .618 * displacement" in s and '"TREND_PROOF_RELOAD"' in s,
 "failure_continuation":"V72PrepareFailureContinuation" in s and "V72OppositeDirection" in s and '"FAILURE_CONTINUATION"' in s,
 "transition_shadow_only":'"TRANSITION_SHADOW"' in s and "e.CapitalEligible = false" in s,
 "no_selector_gate":"e.CapitalReady" in execblk and all(x not in s for x in ["V71EdgeModelSpec","V71ExpectedPathProbability","V71ExpectedRunnerProbability","V71SupportDistance","_v71ModelReady"]),
 "single_pending_leg":"V72BuildPullbackSingleLeg" in s and "V72SubmitPullbackSingleLeg" in s and "PlaceGridLimit(basket, l0)" in s,
 "fixed_2r_payoff":"2.0 * risk + costPrice" in s and 'V71FinalizeExpansionShadow(e, i, "V72_FIXED_2R_TARGET", 2.0)' in s,
 "exact_payoff_census":"V72RecordPayoffCensus" in s and "[V72-PAYOFF-CENSUS]" in s and "_v72PayoffSeen" in s and "_v72PayoffCensus" in s,
 "no_v72_early_exit":"V72_EARLY_CAPITAL_PROTECT" not in s and "!v72FixedPayoff && basket.PeakR >= TrailTriggerR" in s,
 "m15_expiry":"V72NextM15Boundary" in s and "PullbackExpiryUtc" in s and "VirtualProofExpiryUtc" in s,
 "same_bar_fail_closed":"FILL_PROOF_SAME_BAR_AMBIGUOUS" in s and "PROOF_STOP_SAME_BAR_AMBIGUOUS" in s and "PULLBACK_FILL_SAME_BAR_AMBIGUOUS" in s,
 "asymmetry_auction":"e.AsymmetryCompression" in execblk and ".OrderByDescending(e => e.AsymmetryCompression)" in execblk,
 "minimum_rr":'[Parameter("Minimum Net RR", DefaultValue = 2.0' in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "no_stop_widening":"stopWideningViolations" in s,
 "dst_aware":'ResolveTimeZone("Europe/London"' in s and 'ResolveTimeZone("America/New_York"' in s
}
out={"version":"HarmonyBot V71 -> V72","audit":"V72_HARMONIC_BIFURCATION_COMMERCIAL_GUARD",
 "source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"checks":checks,"pass":all(checks.values())}
pathlib.Path("V71_STATIC_CONTRACT_AUDIT.json").write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
