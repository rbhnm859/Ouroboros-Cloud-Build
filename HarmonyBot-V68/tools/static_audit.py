#!/usr/bin/env python3
import json,pathlib,sys
s=pathlib.Path(sys.argv[1]).read_text(errors="ignore")
checks={
 "identity":"class HarmonyBotV68" in s and 'BotPrefix = "HB68"' in s,
 "v52_control":"V68_V52_CONTROL" in s and "V68ProductEnabled" in s,
 "family_owned_route":"V68FamilyRouteSignal" in s and "V68FamilyOwnedRouting" in s and "V68_FAMILY_OWNED_ROUTE_" in s,
 "named_joint_quality":"V68PatternQualityEligible" in s and "V68NamedFamilyJointQuality" in s,
 "exact_family_confirmation":all(x in s for x in ['p == "Gartley"','p == "Bat"','p == "Deep Gartley"','p == "Rat"','p == "Alt Bat"','p == "Butterfly"','p == "Crab" || p == "Deep Crab"','p == "Shark"','p == "Cypher"','p == "5-0"','p == "AB=CD"']),
 "parent_abcd_suppression":"PARENT_FAMILY_SUPPRESSED" in s and "V68SuppressParentAbcd" in s,
 "family_fair_detection":"V68FamilyDetectionQuotaFor" in s and "FAMILY_QUOTA_SELECTED" in s,
 "grid_normalization":"V68NormalizeGridRisk" in s and "V68FamilyGridWeights" in s and "INVALID_GRID_WEIGHT_SUM" in s,
 "grid_rebalance":"V68RebalancePhysicalGridRisk" in s and "V68RebalanceGridRiskBudget" in s,
 "whole_basket_risk":'Basket Risk %' in s and "ActualBasketWorstRisk" in s,
 "minimum_rr":'Minimum Net RR' in s and "DefaultValue = 2.0" in s,
 "completed_bar_only":"allCompletedBars=true" in s,
 "single_basket":"TryScheduleAndExecute" in s and "slotBusy" in s,
 "no_future_features":all(x not in s for x in ["FutureOutcome","ForwardMfe","ForwardMae","YearGate","DateGate"]),
 "no_recovery_logic":all(x not in s.lower() for x in ["martingale","loss averaging"]),
 "no_new_indicator_alpha":all(x not in s for x in ["RelativeStrengthIndex","StochasticOscillator","MacdCrossOver","IchimokuKinkoHyo"])
}
out={"version":"HarmonyBot V68","checks":checks,"pass":all(checks.values())}
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["pass"] else 68)
