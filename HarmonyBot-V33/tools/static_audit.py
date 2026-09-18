#!/usr/bin/env python3
import pathlib,re,json,sys
src=pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")

checks={
 "standalone_v33":"class HarmonyBotV33" in src and "HarmonyBot V33.0" in src,
 "no_v29_pending":"V29TryGetTriggeredPending" not in src and "V29PendingCandidate" not in src,
 "no_v30_router":"V30" not in src,
 "no_legacy_gridbasket":"GridBasket" not in src,
 "no_recovery_martingale":not re.search(r"\bMartingale\b|\bDCA\b|Loss Averaging|Recovery Grid",src,re.I),
 "h4_explicit":"MarketData.GetBars(TimeFrame.Hour4, SymbolName)" in src,
 "h1_explicit":"MarketData.GetBars(TimeFrame.Hour, SymbolName)" in src,
 "m15_explicit":"MarketData.GetBars(TimeFrame.Minute15, SymbolName)" in src,
 "m1_explicit":"MarketData.GetBars(TimeFrame.Minute, SymbolName)" in src,
 "m15_detector":"DetectPatternCandidates(_m15Bars" in src,
 "m1_confirmation":"M1ConfirmationScore" in src and "_m1Bars" in src,
 "completed_bars":"b.Count - 2" in src and "endIndex - depth" in src,
 "dst":"Europe/London" in src and "America/New_York" in src,
 "basket_risk_one":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in src,
 "frozen_fib_grid":"new[] { 0.0, .236, .382, .618 }" in src,
 "frozen_risk_weights":"3.0 / 7.0" in src and "2.0 / 7.0" in src and "1.0 / 7.0" in src,
 "preplanned_grid":"TryBuildFibonacciGridPlan" in src and "FIB_GRID_PLAN" in src,
 "sequential_admission":"ProcessBasketAdmissionOnM1" in src and "ADMISSION_WAIT" in src,
 "strict_leg_sequence":"ADMISSION_SEQUENCE_CANCEL" in src and "earlierNotFilled" in src,
 "one_pending_per_basket":"OwnPendingOrders().Any(o => LabelBasketId(o.Label) == basket.BasketId)" in src,
 "fresh_m1_admission":"M1ConfirmationScore(m1Index, basket.Candidate.Signal)" in src,
 "dynamic_filled_risk":"CurrentFilledRiskToFrontier" in src and "RiskForLegAtStop" in src,
 "risk_cap_on_admission":"currentRisk + candidateRisk > basket.InitialBasketRisk" in src,
 "no_market_chase":"ADMISSION_PRICE_ALREADY_CROSSED" in src,
 "bounded_technical_retry":"MaxPendingSubmitAttempts = 2" in src and "ErrorCode.TechnicalError" in src and "RETRY_WAIT" in src,
 "bounded_frontier_retry":"FrontierRetryAfterUtc" in src and "FrontierSubmitAttempts" in src and "FRONTIER_TRANSIENT_RETRY" in src,
 "server_limit_orders":"PlaceLimitOrder" in src and "ProtectionType.Absolute" in src,
 "pending_expiration":"ExpirationUtc" in src and "PendingTtlMinutes" in src,
 "shared_structural_stop":"PatternStructuralInvalidation" in src and "basket.StructuralStop" in src,
 "no_atr_stop":"Math.Min(d.Price, przLow) - atr * p.StopBufferAtr" not in src,
 "monotonic_frontier":"AdvanceProtectionFrontier" in src and "ProtectionFrontier" in src and "BetterStop" in src,
 "frontier_buy_monotonic":"proposed > basket.ProtectionFrontier + _symbol.TickSize" in src,
 "frontier_sell_monotonic":"proposed < basket.ProtectionFrontier - _symbol.TickSize" in src,
 "no_old_stop_manager":"ImproveBasketStops" not in src,
 "server_protection_no_weaken":"BetterStop(basket.Direction, p.StopLoss.Value, basket.ProtectionFrontier)" in src,
 "frontier_stop_only_api":"ModifyStopLossPrice(proposed)" in src and "ModifyPosition(p, proposed, p.TakeProfit" not in src,
 "duplicate_guard":"LegAlreadyExists" in src and "_duplicateGridLegs" in src,
 "orphan_guard":"_orphanPendingOrders" in src and "CancelPendingOrder" in src,
 "single_active_basket":"_baskets.Values.Any(b => b.IsActive)" in src,
 "grid_cancel_mfe":"GridCancelMfeR" in src and "MFE_GRID_CANCEL" in src,
 "no_old_single_lifecycle":"ManageOpenPosition" not in src and "ExecuteCandidate(" not in src,
 "execution_error_ledger":"[V33-EXECUTION-ERROR]" in src and "RecordExecutionError" in src,
 "broker_min_distance":"MinStopLossDistance" in src and "MinTakeProfitDistance" in src and "SymbolMinDistanceType.Pips" in src,
 "commercial_algo_not_embedded":"HarmonyBot_V33_Commercial.algo" not in src
}
forbidden=[x for x in ["Bars.Count - 1","LastValue"] if x in src]
status="PASS" if all(checks.values()) and not forbidden else "FAIL"

pathlib.Path("STATIC_AUDIT.json").write_text(json.dumps({"status":status,"checks":checks,"forbidden_future_patterns":forbidden},indent=2))
pathlib.Path("TIMEFRAME_AUDIT.json").write_text(json.dumps({
 "status":"PASS" if all(checks[k] for k in ("h4_explicit","h1_explicit","m15_explicit","m1_explicit","m15_detector","m1_confirmation","completed_bars")) else "FAIL",
 "H4":"macro harmonic/regime","H1":"intermediate harmonic/conflict","M15":"primary harmonic setup","M1":"entry plus deeper-leg causal confirmation","completed_bar_only":checks["completed_bars"]
},indent=2))
pathlib.Path("NO_LOOKAHEAD_AUDIT.json").write_text(json.dumps({
 "status":"PASS" if checks["completed_bars"] and not forbidden else "FAIL",
 "evidence":["LastClosedIndex Count-2","confirmed pivot depth","deeper-leg admission only from ProcessNewM1Close"]
},indent=2))
pathlib.Path("SESSION_DST_AUDIT.json").write_text(json.dumps({
 "status":"PASS" if checks["dst"] else "FAIL","london":"Europe/London","new_york":"America/New_York","historical_hour_blacklist":False
},indent=2))
pathlib.Path("GRID_RISK_AUDIT.json").write_text(json.dumps({
 "status":"PASS" if all(checks[k] for k in ("basket_risk_one","frozen_risk_weights","dynamic_filled_risk","risk_cap_on_admission","strict_leg_sequence","monotonic_frontier")) else "FAIL",
 "basket_risk_cap_pct":1.0,"risk_weights":["3/7","2/7","1/7","1/7"],"unused_risk_redistributed":False,
 "grid_levels":[0.0,0.236,0.382,0.618],"sequential_admission":True,"one_pending_deeper_leg":True,
 "structural_stop_widening_allowed":False
},indent=2))
pathlib.Path("EXECUTION_STATE_AUDIT.json").write_text(json.dumps({
 "status":"PASS" if all(checks[k] for k in ("bounded_technical_retry","bounded_frontier_retry","server_limit_orders","duplicate_guard","orphan_guard","execution_error_ledger","server_protection_no_weaken","frontier_stop_only_api")) else "FAIL",
 "states":["ADMISSION_WAIT","SUBMIT_REQUESTED","PENDING_ACCEPTED","RETRY_WAIT","FILLED","CANCEL_REQUESTED","CANCELLED","CLOSED","REJECTED"],
 "technical_error_retry_max_attempts":2
},indent=2))
print(json.dumps({"status":status,"checks":checks},indent=2))
raise SystemExit(0 if status=="PASS" else 2)
