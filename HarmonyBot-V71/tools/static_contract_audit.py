#!/usr/bin/env python3
import json,pathlib,sys,hashlib
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "HarmonyBot-V71/src/HarmonyBotV71.cs")
s=p.read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
def between(a,b):
    i=s.find(a); j=s.find(b,i+len(a))
    return s[i:j] if i>=0 and j>i else ""
selective=between("private bool V71SelectiveQualityRecall","private double V70MinimumExecutionEvidenceScore")
grid=between("private bool V71TryGetGridTemplate","private bool GridPlanReject")
checks={
 "identity":"class HarmonyBotV71" in s and 'BotPrefix = "HB71"' in s,
 "brace_balance":s.count("{")==s.count("}"),
 "source_not_truncated":len(s)>250000 and "public sealed class PipelineCounter" in s,
 "all_12_families":all(('case "'+f+'"') in s for f in families),
 "selective_suppression":"EnableV71SelectiveLaneSuppression" in s and "V71ShouldSuppressLegacyLane" in s,
 "selective_recall":"EnableV71SelectiveRecall" in s and "V71SelectiveRecallRoute" in s,
 "protected_rat_shark":'pattern == "Rat" || pattern == "Shark"' in s,
 "negative_lane_preregistration":all(x in selective for x in ['p == "AB=CD"','p == "Deep Gartley"','p == "5-0"']),
 "cypher_recall":'p == "Cypher"' in selective,
 "family_native_grid_amplifier":"EnableV71FamilyNativeGridAmplifier" in s and "V71TryGetGridTemplate" in s,
 "grid_is_not_filter":"FAMILY_NATIVE_PROFIT_AMPLIFIER_NOT_FILTER" in s,
 "grid_fib_levels":all(x in grid for x in [".236",".382",".618"]),
 "grid_risk_ceiling":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s and "plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8" in s,
 "minimum_rr":'[Parameter("Minimum Net RR", DefaultValue = 2.0' in s,
 "single_active_basket":"OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)" in s,
 "completed_bar":"private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }" in s,
 "broker_protection":"BrokerProtectionDistancesValid" in s and "SERVER_PROTECTION_FAIL_CLOSED" in s,
 "dst_aware":'ResolveTimeZone("Europe/London"' in s and 'ResolveTimeZone("America/New_York"' in s,
 "no_future_selective":all(x not in selective for x in ["OutcomeR","MfeR","MaeR","ShadowAlphaObservation","_v69Shadow"]),
 "no_future_grid":all(x not in grid for x in ["OutcomeR","MfeR","MaeR","ShadowAlphaObservation","_v69Shadow"]),
 "no_stop_widening":"stopWideningViolations" in s and "retryImproves" in s,
 "v70_blanket_path_available_but_disabled_by_runner":"EnableV70HardVetoRationalization" in s and "EnableV70FamilyRouteAdmission" in s
}
out={"version":"HarmonyBot V71","audit":"selective_causal_alpha_grid_fail_closed","source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"checks":checks,"pass":all(checks.values())}
pathlib.Path("V71_STATIC_CONTRACT_AUDIT.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 2)
