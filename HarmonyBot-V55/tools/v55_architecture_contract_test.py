#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V55/src/HarmonyBotV55.cs").read_text(errors="ignore")
checks={
 "identity":"public class HarmonyBotV55" in s and 'BotPrefix = "HB55"' in s,
 "v51_champion_live_kernel":"DetectPatternCandidates(" in s and "TryMatchProfile(" in s,
 "separate_research_book":"_researchCandidates" in s and "ResearchCandidate" in s,
 "universal_research":"EnableUniversalHarmonicResearchPlane" in s and "DetectResearchPatternCandidates" in s,
 "bounded_research_graph":"EnableResearchBoundedPivotGraph" in s and "EnumerateResearchPivotSequences" in s,
 "selective_capital":"EnableEvidenceAdmittedExpansion" in s and "EvidenceAdmissionEligible" in s and "PromoteResearchExpansion" in s,
 "no_live_liberation_bypass":"LIBERATION_QUALITY_VECTOR_CONTINUE" not in s and "LiberationDiagnosticRoute" not in s,
 "core_hard_priority":"coreArmed.Count > 0 ? coreArmed[0]" in s and "EXPANSION_DEFERRED_FOR_ACTIVE_CORE_THESIS" in s,
 "abcd_primitive_strict":'p=="AB=CD"' in s and "PivotScale!=M15SwingDepth" in s and "EXHAUSTION_REVERSAL" in s,
 "rr_floor":'DefaultValue = 2.0' in s and "ExpansionMinNetRR" in s,
 "basket_risk":"Account.Equity * BasketRiskPercent / 100.0" in s,
 "grid_core":".236" in s and ".382" in s and ".618" in s and "GridCancelMfeR" in s,
 "no_recovery":all(x not in s for x in ["MartingaleMultiplier","RecoveryMultiplier","LossAveragingMultiplier"])
}
out={"version":"HarmonyBot V55","checks":checks,"pass":all(checks.values())}
pathlib.Path("V55_ARCHITECTURE_CONTRACT_TEST.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 7)
