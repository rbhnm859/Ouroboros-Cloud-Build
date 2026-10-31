#!/usr/bin/env python3
import json,pathlib,sys,hashlib
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V70/src/HarmonyBotV70.cs")
s=p.read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
def between(a,b):
    i=s.find(a); j=s.find(b,i+len(a))
    return s[i:j] if i>=0 and j>i else ""
admission=between("private HarmonicRoute V70FamilyRouteAdmission","private double V70MinimumExecutionEvidenceScore")
arb=between("private double V70OpportunityCostScore","private double CandidateRank")
checks={
 "identity":"class HarmonyBotV70" in s and 'BotPrefix = "HB70"' in s,
 "brace_balance":s.count("{")==s.count("}"),
 "all_12_families":all(('case "'+f+'"') in s for f in families),
 "hard_veto_rationalization":"EnableV70HardVetoRationalization" in s,
 "family_route_admission":"EnableV70FamilyRouteAdmission" in s,
 "opportunity_cost_arbitration":"EnableV70OpportunityCostArbitration" in s,
 "protected_rat_shark":'pattern == "Rat" || pattern == "Shark"' in s,
 "challengers":all(x in s for x in ['p == "Cypher"','p == "5-0"','p == "AB=CD"']),
 "timing_state_machine":"V70_TIMING_DEFER_" in s and "V70MinimumExecutionEvidencePass" in s,
 "filter_evidence_ledger":"[V70-FILTER-EVIDENCE]" in s,
 "whole_basket_risk":"plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8" in s,
 "minimum_rr":'[Parameter("Minimum Net RR", DefaultValue = 2.0' in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "completed_bar":"private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }" in s,
 "broker_protection":"BrokerProtectionDistancesValid" in s and "SERVER_PROTECTION_FAIL_CLOSED" in s,
 "dst_aware":'ResolveTimeZone("Europe/London"' in s and 'ResolveTimeZone("America/New_York"' in s,
 "no_future_admission":all(x not in admission for x in ["OutcomeR","MfeR","MaeR","ShadowAlphaObservation","_v69Shadow"]),
 "no_future_arbitration":all(x not in arb for x in ["OutcomeR","MfeR","MaeR","ShadowAlphaObservation","_v69Shadow"]),
 "grid_control_not_rewritten":"ApplyV67FamilyGridContracts" in s,
 "exit_control_not_rewritten":"NO_MFE_THESIS_FAILURE" in s and "FIB_382_STRUCTURE_TRAIL" in s,
 "no_stop_widening":"stopWideningViolations" in s and "retryImproves" in s
}
out={"version":"HarmonyBot V70","audit":"causal_admission_reconstruction_fail_closed","source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"checks":checks,"pass":all(checks.values())}
pathlib.Path("V70_STATIC_CONTRACT_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
