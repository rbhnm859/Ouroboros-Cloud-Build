# HarmonyBot XAUUSD V1.2 — engineering supplement and acceptance matrix

Purpose: supplement and execute the first unfixed dependency of the V1 cleanroom roadmap. NOT a commercial launch, broker simulation, account authorization or a V74 change.

## Source lock

- Repository: `rbhnm859/Ouroboros-Cloud-Build`
- ONLY mutable development ref: `feat/hbxau-v1-cleanroom-20261106`
- Prior verified cleanroom HEAD: `bddaba12bb8b2a601f4730c38bccc43684e112dd`
- V74 reference unchanged at preflight: `c3283e6f61741a5a9a3d2fc7ea31a066b64f7806`
- Prior verified CI: `42156660260` — 54/54 contracts; safe .algo compiled.
- Source docs: https://help.ctrader.com/ctrader-algo/documentation/cbots/cbot-bar-events/ and https://help.ctrader.com/ctrader-algo/how-tos/cbots/handle-bar-events/ and https://help.ctrader.com/ctrader-algo/references/General/Robot/OnBarClosed/
- Conflict: general cTrader guide says OnBarClosed's Bars excludes live bar, yet OnBarClosed-specific API code sample uses Bars.Last(1); we remove the ambiguity by using OnBar, where Last(0) is NEW live bar and Last(1) the completed bar. This is a source-backed design; real Runtime semantics are still **NOT VERIFIED**.

## P1-time patch contract

**Inputs:** closed bar open+OHLC; opening time of the newly live bar; first observed tick (UTC). The new bar's open price is never passed to the detector.

**Observations:** CausalBarReceipt.ClosedBar.CloseUtc is an effective **bar boundary / next-open marker**; in a Friday-to-Monday gap it is NOT guaranteed to represent the true last-traded tick on Friday. `ObservedAtUtc` and `AvailableAtUtc` are first received tick time (Server.Time), not anticipated candle time. Pivot proof after right bars becomes available no earlier than the final confirming bar observation. Pivot event index remains source-anchored.

**Failure behavior:** non-UTC, timestamp inversion, duplicate/out-of-order bar, delayed source with reversed observation chronology, OHLC invalidity => throw, cBot stops via fail-closed handler. No order API is present.

**Prohibited:** OnBarClosed ambiguous indexing; using OHLC of live bar as completed; calling order methods; inferring true Friday last tick from Monday opening; treating compile-only as execution parity.

**Rollback:** leave V74 and original V1 untouched. If new CI fails, create only a new forward-fix commit on Cleanroom. Prior HEAD remains recoverable. No force push, deletion or paid rerun.

## Newly specified tests — executable C# contract tests

| ID | Requirement | Test stimulus | Expected |
|---|---|---|---|
| T-P1-01 | normal source/observation chronology | close 12:01, tick 12:01:07 | boundary 12:01, available 12:01:07 |
| T-P1-02 | weekend gap | Friday bar, next open Monday tick | available only Monday |
| T-P1-03 | future-data reject | tick before new-open boundary | fail closed |
| T-P1-04 | UTC validation | local +08 timestamp | fail closed |
| T-P1-05 | pivot append causality | observation before close boundary | fail closed |
| T-P1-06 | confirmation lag | right-confirming bar observed 3s later | pivot available 3s later |
| T-P1-07 | replay monotonicity | newer bar observed earlier than prior | fail closed |
| T-P1-08 | gap not an actual last tick | Monday first tick != Friday last tick | record distinct timestamps |
| T-CI-09 | source binding | OnBar + Last(1) completed + Last(0) boundary + Server.Time | CI static contract |
| T-CI-10 | V74 isolation | old folders/workflows absent in cleanroom | CI fail if imported |
| T-CI-11 | no order creation | trading API presence | CI fail if imported |
| T-CI-12 | artifact custody | source SHA + algo SHA + all tests | CI manifest |

## Mandatory runtime integration — NOT VERIFIED

1. cTrader demo XAUUSD H1/M15/M1: log Last(0), Last(1), count, Server.Time, TimeFrame and UTC candle boundaries on OnBar() first tick; verify exact chronological records.
2. Reconnect/history reload; if live bar appears without fresh tick, confirm no phantom closed observation. Ensure no duplicate event identity across replay.
3. Friday-to-Monday and broker-specific weekend/holiday, verify that first tick arrival is not backdated to prior close.
4. UK/US DST different transition weeks: confirm absolute UTC and non-future as-of joins, no fixed-offset guesses.
5. High-frequency same-timestamp range/Renko bars: if NextOpenUtc<=ClosedOpenUtc, fail closed; do not claim time-based behavior for non-time bars.
6. For chart bars with market pause: observedAt may be later than nextBarOpen; never use it as earlier admission.
7. Runtime comparison of first-passage tick bid/ask, costs and order receipt before any later execution promotion.
8. Maintain original 54 tests; append new cases; require one actual successful CI on source SHA. No claim of full Runtime PASS.

## Broader implementation roadmap (pending source / demo authority)

- P2: separately source-lock each of the 10 family rules; full causal PRZ projection and confirmed D (Shark/5-0 separate grammars); positive+negative fixtures; disable if source is unverified.
- P3: candidate timeframes, complete-bar MTF as-of join, cost-aware walk-forward selection, ablation for EMA/ATR/RSI/ADX/liquidity/session/spread. Adaptive vs fixed compare.
- P4: DISCOVER/PROJECT/COMPLETE/EVALUATE/DEFER/REJECT/ENTER/MANAGE/CLOSE state machine, unique thesis and pending-order ledger, 0 live orders.
- P5: broker symbol discovery and verification of XAUUSD, VolumeInUnits, steps, tick/pip, FX conversion, margin, stop distances, trading hours; one global execution lease, no unknown resubmit.
- P6: Virtual Grid manages one open position only; no accumulation, stop widening, duplicated count, partials assigned to original approved R.
- P7: multi-year historical bid/ask native-tick research. Confirm cTrader CLI data-mode support before claiming tick. Keep source/data/cost SHA custody.
- P8: independent OOS with predeclared split; 500 distinct whole trades per full year, MeanR>=0.9, PF_R>=3.3, WR>=60%, AvgWinR>=2.3, block-bootstrap LCB95>0; DD<=10%, monthly compounding aspiration separate.
- P9: release only if independent Risk/Validation/Red Team/Data Governance vetoes all pass and separately authorized demo-to-production transition.

## Independent gates and status semantics

- `PASS`: measured evidence of stated scope only.
- `FAIL`: test/run found mismatch.
- `BLOCKED`: permission/environment/dependency prevents required action.
- `NOT VERIFIED`: no authoritative evidence yet.

The successful old 54-case CI does not certify this patch. Promotion and real trading remain BLOCKED. Neither the unchanged V74 alpha gates nor old CI are re-run by this V1 patch.
