#!/usr/bin/env python3
import json,pathlib,sys,hashlib,re
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V69/src/HarmonyBotV69.cs")
src=p.read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
def between(a,b):
    i=src.find(a); j=src.find(b,i+len(a))
    return src[i:j] if i>=0 and j>i else ""
router=between("private HarmonicRoute RouteSignalFamilyNativeV67","private bool UpdateV67FamilyContractEvidence")
ranker=between("private double CandidateRank","private double M1ConfirmationScore")
shadow=between("private void TryStartV69Shadow","private string NewCandidateId")
checks={
 "identity":"class HarmonyBotV69" in src and 'BotPrefix = "HB69"' in src,
 "brace_balance":src.count("{")==src.count("}"),
 "all_12_family_mapping":all(('case "'+f+'"') in src for f in families),
 "all_12_family_contracts":all(('AddV67FamilyContract("'+f+'"') in src for f in families),
 "equal_visibility_param":"EnableV69EqualFamilyVisibility" in src,
 "shadow_census_param":"EnableV69ShadowAlphaCensus" in src,
 "funnel_telemetry":"[V69-FAMILY-FUNNEL]" in src,
 "terminal_telemetry":"[V69-FAMILY-TERMINAL]" in src,
 "shadow_start":"[V69-SHADOW-START]" in src,
 "shadow_outcome":"[V69-SHADOW-OUTCOME]" in src,
 "shadow_updates_completed_bar":"UpdateV69ShadowAlphaCensus(i, utc);" in src and "LastClosedIndex(_m1Bars)" in shadow,
 "shadow_not_in_router":all(x not in router for x in ["_v69Shadow","OutcomeR","ShadowAlphaObservation","V69Shadow"]),
 "shadow_not_in_ranker":all(x not in ranker for x in ["_v69Shadow","OutcomeR","ShadowAlphaObservation","V69Shadow"]),
 "terminal_hooks":all(x in src for x in ['V69RecordTerminal(c, "REJECTED"','V69RecordTerminal(c, "EXPIRED"','V69RecordTerminal(c, "INVALIDATED"']),
 "canonical_family":"public CanonicalFamilyId FamilyId;" in src,
 "canonical_setup":"public string CanonicalSetupId;" in src,
 "whole_basket_risk":"plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8" in src,
 "minimum_rr":'[Parameter("Minimum Net RR", DefaultValue = 2.0' in src,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in src,
 "completed_bar_clock":"private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }" in src,
 "dst_aware":'ResolveTimeZone("Europe/London"' in src and 'ResolveTimeZone("America/New_York"' in src,
 "no_stop_widening":"stopWideningViolations" in src and "retryImproves" in src
}
out={"version":"HarmonyBot V69","audit":"equal_visibility_shadow_census_no_alpha_leak","source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"checks":checks,"pass":all(checks.values())}
pathlib.Path("V69_STATIC_CONTRACT_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
