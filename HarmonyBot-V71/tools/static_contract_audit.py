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
 "separate_expansion_book":"Dictionary<string, V71ExpansionCandidate> _v71Expansion" in s,
 "core_risk_isolated":"V71CandidateRiskPercent" in s and "c.V71Expansion" in s,
 "same_setup_capital_blocked":"e.CapitalEligible && !e.CoreOverlapObserved" in execblk and "CapitalEligible = !coreOverlap" in s,
 "deterministic_expansion_identity":"V71StableHash32(id)" in s and "private uint V71StableHash32" in s and "GetHashCode()" not in s,
 "frozen_detector_present":"V71DetectExpansionPatternCandidates" in s and "fullFamilies = _profiles.ToList()" in s,
 "projected_prz_no_future":"Pure projected PRZ for Expansion" in s and "if (d.Price < przLow || d.Price > przHigh) return false;" in s,
 "completed_m1":"private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }" in s,
 "v72_reaction_proof":"[V72-REACTION-PROVED]" in s and "V71ExpansionM1Confirmation" in s,
 "v72_pullback_0618":"proof - .618 * displacement" in s and "proof + .618 * displacement" in s and "[V72-PULLBACK-PLAN]" in s,
 "v72_single_pending_leg":"V72BuildPullbackSingleLeg" in s and "V72SubmitPullbackSingleLeg" in s and "PlaceGridLimit(basket, l0)" in s,
 "v72_no_selector_gate":"(!EnableV72ReactionAlpha && !_v71ModelReady)" in s and "e.ReactionProved && e.AwaitingPullbackFill" in execblk,
 "v72_structural_stop":"double stop = e.Signal.StructuralInvalidation;" in s,
 "v72_cost_adjusted_2r":"2.0 * risk + costPrice" in s and "netRr + 1e-9 < MinimumNetRR" in s,
 "v72_m15_expiry":"V72NextM15Boundary" in s and "PullbackExpiryUtc" in s,
 "v72_shadow_fill_causal":"PULLBACK_FILL_SAME_BAR_AMBIGUOUS" in s and "e.AwaitingPullbackFill = false" in s,
 "minimum_rr":'[Parameter("Minimum Net RR", DefaultValue = 2.0' in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "no_stop_widening":"stopWideningViolations" in s,
 "dst_aware":'ResolveTimeZone("Europe/London"' in s and 'ResolveTimeZone("America/New_York"' in s
}
out={"version":"HarmonyBot V71 -> V72","audit":"MINIMAL_V72_0618_PULLBACK_COMMERCIAL_GUARD",
 "source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"checks":checks,"pass":all(checks.values())}
pathlib.Path("V71_STATIC_CONTRACT_AUDIT.json").write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
