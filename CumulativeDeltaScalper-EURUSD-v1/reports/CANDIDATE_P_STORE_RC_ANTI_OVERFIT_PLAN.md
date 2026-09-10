# Candidate P — Store RC / Anti-Overfit Plan

## Objective
Build a $30-starting-balance M1 FX scalper that can be evaluated for cTrader Store release without relying on curve-fit parameter sweeps.

## Locked principles
- No Grid, Martingale, DCA, Recovery, Loss Averaging, or Hedging.
- One open position per symbol/label.
- Every entry has broker-valid SL/TP.
- Hard actual trade-loss cap remains enabled.
- Parameters are locked before testing new symbols.
- New symbols are first tested with the SAME core signal settings; no per-symbol optimisation in the first pass.
- ATR and spread filters are normalised to pips / spread-to-ATR ratio so JPY and non-JPY pairs use comparable market-state rules.
- Realistic cTrader testing costs are included via `--spread` and `--commission`.
- No brute-force optimisation in Candidate P.

## Symbols in first generalisation pass
1. EURUSD
2. GBPUSD
3. USDJPY
4. AUDUSD

## Shared strategy core
Candidate P starts from the O3/K1 profitable micro-scalping architecture, not the failed all-day Runner architecture.

Shared locked core for first pass:
- M1
- DeltaThreshold 125
- MinConfirmations 3
- HTF M15 EMA / slope filter
- ADX 16
- session 14:00–14:54 UTC
- Thursday disabled
- FixedMoneyRisk 0.95 with auto-scaling from $100 reference
- Max lot 0.02
- SL ATR 0.8
- TP ATR 0.45
- Runner disabled
- Breakeven enabled
- Adverse delta exit enabled
- Hard actual loss cap $1.00
- Daily loss money $1.00
- Daily equity DD money $1.00
- Daily profit target disabled; giveback lock enabled

## Normalised execution filters
Candidate P introduces optional normalised filters:
- ATR measured in pips instead of raw price units.
- Spread measured in pips instead of broker points.
- Spread/ATR ratio ceiling.

First-pass locked values:
- Min ATR: 0.5 pips
- Max ATR: 10.5 pips
- Max bot-side spread: 1.8 pips
- Max spread/ATR ratio: 0.50

These are intentionally broad and are not separately tuned per symbol.

## Cost assumptions for first pass
The workflow uses FxPro cTrader indicative average spread inputs and $35 per million USD volume commission:
- EURUSD spread 0.43 pips
- GBPUSD spread 0.73 pips
- USDJPY spread 0.35 pips
- AUDUSD spread 0.55 pips
- Commission: 35, type UsdPerMillionUsdVolume

EURUSD also receives a 1.5x-spread stress test.

## Anti-overfit validation windows
Parameters are locked before all tests.
- 2Y structural window: 2024-09-09 to 2026-09-09
- Recent 1Y validation: 2025-09-09 to 2026-09-09
- Recent 6M diagnostic for EURUSD: 2026-03-09 to 2026-09-09
- EURUSD cost stress: recent 1Y at 1.5x average spread

No parameters are selected by maximising a single-window ROI.

## Promotion gates
A symbol can only become a supported Store profile if, after realistic costs:
- 2Y net profit > 0
- recent 1Y net profit > 0
- Profit Factor preferably >= 1.15 on both windows
- Max equity drawdown <= 15%
- largest actual loss remains approximately <= $1.10
- enough trades exist for the result to be statistically useful
- profitability is not concentrated in only one short period

If a symbol fails, it remains unsupported rather than being aggressively tuned into a backtest winner.

## Store release rule
Candidate P is a Release Candidate, not a final Store release, until realistic-cost EURUSD validation and at least one forward/demo validation interval pass. Multi-FX symbols are optional modules and must pass independently.