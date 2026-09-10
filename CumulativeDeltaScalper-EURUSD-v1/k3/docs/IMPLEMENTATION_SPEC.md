# CumulativeDeltaScalper EURUSD K3 — Flow-First Commercial Research

## Purpose
This branch implements the pre-committed commercial validation redesign derived from K/K2 evidence. It does not modify the immutable Original Candidate K.

## Immutable lineage
- Original Candidate K source commit: `ca6d78774eb7f772d32e19e537a9584a5cfc5400`
- K2 attribution evidence head: `31dcdb360553e7bd3f6e92a61a6930a2f9691ea1`

## Single strategy-level change
Replace equal 3-of-5 confirmation voting with Flow-First hierarchical admission:
1. Existing cumulative-delta threshold crossing (DeltaThreshold=125).
2. Existing 3-bar same-direction delta persistence is mandatory.
3. Just-closed M1 candle must accept flow direction: long close>open; short close<open.
4. Existing context requires at least 2 of: HTF EMA direction, EMA slope, ADX>=16, dynamic spread.
5. Existing ATR/session/weekday/cooldown/risk/equity guards remain mandatory.
6. Execute one position maximum with entry-time SL/TP. No hedging.

No Fibonacci, RSI, MACD, Bollinger, ML, Grid, Martingale, DCA, Recovery, Loss Averaging, averaging down or reverse recovery.

## K2 decisions
- Breakeven is not treated as an edge generator.
- Adverse-delta exit is not treated as an edge generator.
- Cost estimation remains telemetry/economic safety information; Cost Ratio 2.0 is not the primary signal-quality selector.
- Equity protection remains enabled.

## Corrected commercial harness
All promotion evidence must use:
- EURUSD M1
- initial balance USD 30
- tick historical data (`--data-mode=ticks`)
- spread 0.43 pips
- commission 35 with explicit `UsdPerMillionUsdVolume`
- intended IS: 09/09/2024 00:00 UTC through 08/09/2025 23:59 UTC (CLI DD/MM/YYYY)
- intended OOS: 09/09/2025 00:00 UTC through 09/09/2026 23:59 UTC
- FULL: 09/09/2024 00:00 UTC through 09/09/2026 23:59 UTC
- leverage must be verified/asserted as 1:500 in the validation evidence.

## Validation sequence
1. Corrected Original K control.
2. Corrected K2 control.
3. K3 Flow-First IS.
4. Freeze K3 before OOS only if IS has positive post-cost expectancy and credible PF/trade count.
5. OOS hard gates: ROI>0, PF>=1.20, trades>=50, DD<=15%, largest loss>=-$1, post-cost expectancy>0.
6. FULL hard gates: ROI>=10%, PF>=1.20, trades>=100, DD<=15%, net>0, post-cost expectancy>0.
7. Cost stress 1.25x and 1.5x; at 1.5x require PF>=1.0, net>=0, DD<=20%.
8. Parameter-neighborhood robustness; no sharp isolated optimum.
9. Monte Carlo: median, 5th percentile, 95th-percentile DD, probability of loss, probability DD>20%, risk of ruin.

## Stop rule
Do not tune on OOS. If the pre-committed K3 architecture cannot establish a credible positive edge on corrected IS, stop this K3 hypothesis rather than brute-force parameters. A commercial/mobile release is created only after all promotion gates pass.
