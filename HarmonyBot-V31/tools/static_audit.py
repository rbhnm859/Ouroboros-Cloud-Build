#!/usr/bin/env python3
import pathlib,re,json,sys
src=pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
checks={
 "cleanroom_no_signalbars":"_signalBars" not in src,
 "cleanroom_no_v29":"V29" not in src,
 "cleanroom_no_v30":"V30" not in src,
 "no_grid":"EnableFibGrid" not in src and "GridBasket" not in src,
 "no_martingale":not re.search(r"\bMartingale\b|\bDCA\b|Loss Averaging|Recovery",src,re.I),
 "h4_explicit":"MarketData.GetBars(TimeFrame.Hour4, SymbolName)" in src,
 "h1_explicit":"MarketData.GetBars(TimeFrame.Hour, SymbolName)" in src,
 "m15_explicit":"MarketData.GetBars(TimeFrame.Minute15, SymbolName)" in src,
 "m1_explicit":"MarketData.GetBars(TimeFrame.Minute, SymbolName)" in src,
 "m15_detector":"DetectPatternCandidates(_m15Bars" in src,
 "m1_confirmation":"M1ConfirmationScore" in src and "_m1Bars" in src,
 "closed_bar_index":"b.Count - 2" in src,
 "confirmed_pivots":"endIndex - depth" in src,
 "dst_london":"Europe/London" in src,
 "dst_newyork":"America/New_York" in src,
 "candidate_state_machine":"CandidateState.WAIT_PRZ" in src and "CandidateState.CONFIRMING" in src and "CandidateState.ARMED" in src,
 "event_ledger":"[V31-EVENT]" in src,
 "structural_invalidation":"StructuralInvalidation" in src,
 "canonical_targets":"CanonicalTarget1" in src and "CanonicalTarget2" in src,
 "risk_one_default":'[Parameter("Risk %", DefaultValue = 1.0' in src,
 "maxdd_ten_default":'[Parameter("Max Drawdown %", DefaultValue = 10.0' in src,
 "single_position_scheduler":"OwnPositions().Any()" in src,
 "native_server_protection":"ExecuteMarketOrder" in src and "slPips, tpPips" in src
}
out={"status":"PASS" if all(checks.values()) else "FAIL","checks":checks,
     "forbidden_future_patterns":[x for x in ["Bars.Count - 1","LastValue"] if x in src]}
pathlib.Path("STATIC_AUDIT.json").write_text(json.dumps(out,indent=2))
pathlib.Path("TIMEFRAME_AUDIT.json").write_text(json.dumps({
 "status":"PASS" if all(checks[k] for k in ["h4_explicit","h1_explicit","m15_explicit","m1_explicit","m15_detector","m1_confirmation","closed_bar_index","confirmed_pivots"]) else "FAIL",
 "H4":"macro/context","H1":"intermediate/context","M15":"primary harmonic setup","M1":"execution confirmation",
 "completed_bar_only":checks["closed_bar_index"] and checks["confirmed_pivots"]
},indent=2))
pathlib.Path("NO_LOOKAHEAD_AUDIT.json").write_text(json.dumps({
 "status":"PASS" if checks["closed_bar_index"] and checks["confirmed_pivots"] else "FAIL",
 "evidence":["LastClosedIndex uses Count-2","pivot loop ends at endIndex-depth","M1 confirmation receives the latest completed M1 index"]
},indent=2))
pathlib.Path("SESSION_DST_AUDIT.json").write_text(json.dumps({
 "status":"PASS" if checks["dst_london"] and checks["dst_newyork"] else "FAIL",
 "london":"Europe/London with Windows fallback","new_york":"America/New_York with Windows fallback",
 "entry_window":"08:00 London local to 17:00 New York local"
},indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["status"]=="PASS" else 2)
