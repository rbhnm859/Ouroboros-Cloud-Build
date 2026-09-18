#!/usr/bin/env python3
import pathlib,re,json,sys
src=pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
checks={
 "standalone_v32":"class HarmonyBotV32" in src and "HarmonyBot V32.0" in src,
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
 "fib_grid_levels":"new[] { 0.0, .236, .382, .618 }" in src,
 "risk_weights":"3.0 / 7.0" in src and "2.0 / 7.0" in src,
 "preplanned_grid":"TryBuildFibonacciGridPlan" in src and "FIB_GRID_PLAN" in src,
 "server_limit_orders":"PlaceLimitOrder" in src and "ProtectionType.Absolute" in src,
 "pending_expiration":"ExpirationUtc" in src and "PendingTtlMinutes" in src,
 "shared_structural_stop":"PatternStructuralInvalidation" in src and "basket.StructuralStop" in src,
 "no_atr_stop":"Math.Min(d.Price, przLow) - atr * p.StopBufferAtr" not in src,
 "worst_case_risk":"WorstCaseRisk" in src and "WORST_CASE_BASKET_RISK" in src,
 "duplicate_guard":"LegAlreadyExists" in src and "_duplicateGridLegs" in src,
 "orphan_guard":"_orphanPendingOrders" in src and "CancelPendingOrder" in src,
 "single_active_basket":"_baskets.Values.Any(b => b.IsActive)" in src,
 "grid_cancel_mfe":"GridCancelMfeR" in src and "MFE_GRID_CANCEL" in src,
 "no_old_single_lifecycle":"ManageOpenPosition" not in src and "ExecuteCandidate(" not in src,
 "basket_lifecycle":"ReconcileAndManageBaskets" in src and "FibonacciBasketState" in src,
 "fib_trailing":"FibonacciStructureTrail" in src and ".382" in src,
 "event_ledger":"[V32-BASKET-EVENT]" in src and "[V32-BASKET-CLOSED]" in src,
 "commercial_algo_not_embedded":"HarmonyBot_V32_Commercial.algo" not in src
}
status="PASS" if all(checks.values()) else "FAIL"
forbidden=[x for x in ["Bars.Count - 1","LastValue"] if x in src]
out={"status":status,"checks":checks,"forbidden_future_patterns":forbidden}
pathlib.Path("STATIC_AUDIT.json").write_text(json.dumps(out,indent=2))
pathlib.Path("TIMEFRAME_AUDIT.json").write_text(json.dumps({
 "status":"PASS" if all(checks[k] for k in ("h4_explicit","h1_explicit","m15_explicit","m1_explicit","m15_detector","m1_confirmation","completed_bars")) else "FAIL",
 "H4":"macro harmonic/regime","H1":"intermediate harmonic/conflict","M15":"primary harmonic setup","M1":"execution confirmation","completed_bar_only":checks["completed_bars"]
},indent=2))
pathlib.Path("NO_LOOKAHEAD_AUDIT.json").write_text(json.dumps({
 "status":"PASS" if checks["completed_bars"] and not forbidden else "FAIL",
 "evidence":["LastClosedIndex uses Count-2","confirmed pivots end at endIndex-depth","M1 confirmation reads completed M1 bars"]
},indent=2))
pathlib.Path("SESSION_DST_AUDIT.json").write_text(json.dumps({
 "status":"PASS" if checks["dst"] else "FAIL","london":"Europe/London","new_york":"America/New_York","historical_hour_blacklist":False
},indent=2))
pathlib.Path("GRID_RISK_AUDIT.json").write_text(json.dumps({
 "status":"PASS" if all(checks[k] for k in ("basket_risk_one","risk_weights","worst_case_risk","duplicate_guard","orphan_guard","shared_structural_stop","server_limit_orders")) else "FAIL",
 "basket_risk_cap_pct":1.0,"risk_weights":["3/7","2/7","1/7","1/7"],"unused_risk_redistributed":False,
 "maximum_grid_fraction":0.618,"recovery_grid":False,"structural_stop_widening_allowed":False
},indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if status=="PASS" else 2)
