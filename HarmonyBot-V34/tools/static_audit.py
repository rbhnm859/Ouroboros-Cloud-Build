#!/usr/bin/env python3
import pathlib,json,sys,re
s=pathlib.Path(sys.argv[1]).read_text()
checks={
 "v34_class":"class HarmonyBotV34" in s,
 "events":"Positions.Opened += OnPositionOpened" in s and "PendingOrders.Filled += OnPendingOrderFilled" in s,
 "post_fill_kernel":"PostFillSafetyKernel" in s and "GAP_THROUGH_STRUCTURAL_INVALIDATION" in s,
 "actual_fill_risk":"ActualBasketWorstRisk" in s and "ACTUAL_FILL_RISK_BUDGET_BREACH" in s,
 "protection_fail_closed":"EnsurePostFillProtection" in s and "POST_FILL_PROTECTION_FAIL_CLOSED" in s,
 "stop_only_modify":"ModifyStopLossPrice" in s,
 "tp_only_modify":"ModifyTakeProfitPrice" in s,
 "adaptive_capital":"AdaptiveCapitalMode" in s and "MinimumSupportedEquity" in s and "MicroCapitalThreshold" in s,
 "virtual_grid":"VIRTUAL_ONLY" in s and "VIRTUAL_FILLED" in s and "UpdateVirtualGridState" in s,
 "capital_depth":"ConfigureCapitalExecution" in s and "PhysicalDepth" in s,
 "exposure_governor":"RevalidatePendingExposureGovernor" in s,
 "execution_state_machine":"TransitionLegState" in s and "STATE-VIOLATION" in s,
 "planned_ttl_expiry_legal":"prior == GridLegState.PLANNED" in s and "next == GridLegState.EXPIRED" in s,
 "post_fill_reentrancy_guard":"_postFillInProgress" in s and "V34-POST-FILL-DEDUPE" in s,
 "protected_fill_telemetry":"FILL_TELEMETRY_WITHOUT_PROTECTION" in s and "_postFillValidated.Contains(leg.PositionId)" in s,
 "initial_capital_semantics":"_initialCapitalEligible" in s and "_initialEquity" in s,
 "pending_ttl_race_guard":"PENDING_TTL_NOT_STRICTLY_FUTURE" in s,
 "frontier_target_race_guard":"TargetTooCloseForProtectionUpdate" in s and "FRONTIER_RETRY_SUCCESS" in s,
 "frozen_fib":"new[] { 0.0, .236, .382, .618 }" in s,
 "frozen_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s and "1.0 / 7.0" in s,
 "basket_risk_one":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
 "no_recovery":not re.search(r"\bMartingale\b|\bDCA\b|Loss Averaging|Recovery Grid",s,re.I),
 "no_v33_telemetry":"[V33-" not in s,
 "v34_ids":'"V34-" + _candidateSeq' in s and '"HB34-" + SymbolName' in s
}
status="PASS" if all(checks.values()) else "FAIL"
pathlib.Path("V34_ARCHITECTURE_AUDIT.json").write_text(json.dumps({"status":status,"checks":checks},indent=2))
print(json.dumps({"status":status,"checks":checks},indent=2))
raise SystemExit(0 if status=="PASS" else 2)
