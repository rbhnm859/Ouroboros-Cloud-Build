#!/usr/bin/env python3
import json,pathlib,sys,re
s=pathlib.Path(sys.argv[1]).read_text()
checks={
 "identity":"class HarmonyBotV66" in s and 'BotPrefix = "HB66"' in s,
 "product_definition":"Trend-Thesis Proof & Positive Marginal Opportunity Commercial Convergence" in s,
 "alpha_truth_observation":"LEGACY_ALPHA_TRUTH_OBSERVATION_FAIL" in s and 'Reject(record, "ALPHA_TRUTH_REGIME_REJECT")' not in s,
 "trend_directional_proof":all(x in s for x in ["V66DirectionalTrendEligible","V66DirectionalMovement","DiPlusH1","DiMinusH1","EmaSlopeH1Atr"]),
 "trend_m1_proof":"V66_TREND_M1_REACCELERATION_WAIT" in s and "RouteSpecificM1EvidencePass" in s,
 "qualified_recall":"V66QualifiedRecallEligible" in s and "[V66-QUALIFIED-RECALL]" in s,
 "rejected_shadow":"RejectedOpportunityShadow" in s and "[V66-REJECTED-SHADOW]" in s,
 "no_future_decision_features":all(x not in s for x in ["FutureOutcome","ForwardMfe","ForwardMae","YearGate","DateGate"]),
 "fixed_execution":all(x in s for x in ["V66RouteGridContract","ConfigureV66SelectiveRunner","DeeperLegThesisEligible"]),
 "risk":"ActualBasketWorstRisk" in s and '[Parameter("Basket Risk %", DefaultValue = 1.0' in s,
 "no_hedge_martingale":all(x not in s.lower() for x in ["martingale", "loss averaging"]),
 "completed_bar_audit":"allCompletedBars=true" in s
}
o={"version":"HarmonyBot V66","checks":checks,"pass":all(checks.values())}
print(json.dumps(o,indent=2))
raise SystemExit(0 if o["pass"] else 66)
