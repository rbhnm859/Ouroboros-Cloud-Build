# Fibonacci Harmonic Sniper Ultimate v0.4.0-store-rc1

## Status

This is a release candidate for engineering and backtest validation. It is not yet approved for live use and must not be advertised with guaranteed returns.

## Why the architecture changed

v0.3.0-fix5 repaired important execution/risk bugs, but its signal engine still rebuilt pivots by rescanning a long history window on every closed bar and its harmonic scoring treated broad valid ratio bands as essentially equal quality. That design is acceptable for diagnosis, but it is not a strong base for a Store product or long multi-year optimisation.

RC1 keeps Fibonacci/Harmonic geometry as the primary strategy and changes the implementation underneath it:

1. Incremental pivot engine: seed once, then evaluate only newly confirmable pivot indexes.
2. Weighted harmonic quality: XB and XD have the highest scoring weight; AC/BD remain valid bands but receive graded quality rather than automatic perfect scores throughout the band.
3. Eligibility before ranking: confirmation, D invalidation, regime compatibility, stop geometry, target geometry, costs and minimum net RR are all checked before candidate ranking.
4. Multi-timeframe regime context: configurable higher-timeframe EMA direction/slope is used as score or strict filter without replacing the Fibonacci signal.
5. Broker-adaptive execution filters: spread is measured relative to ATR rather than relying only on a fixed pip ceiling.
6. Adaptive Fibonacci exit: default target is 38.2% of AD; only high-quality, trend-aligned patterns qualify for the 61.8% AD runner target.
7. Risk budgeting after broker normalisation: minimum volume may not silently exceed the configured money risk.
8. Restart-aware daily controls: current-day history is used to rebuild trade count, loss streak and an approximate day-start balance instead of blindly resetting all state after a restart.
9. One-symbol exposure guard: default behaviour blocks other same-symbol positions/pending orders to prevent accidental hedging/stacking.
10. Break-even logic is throttled to at most one modification attempt per bar and uses an absolute price modification only after a 1R trigger.

## Default XAUUSD profile

- Strategy: Fibonacci/Harmonic reversal with higher-timeframe regime scoring.
- Intended chart period for primary validation: M15. H1 is a secondary comparison, not an automatic recommendation.
- Higher-timeframe regime: H1 EMA 50 with optional slope confirmation.
- Patterns: canonical CORE set only.
- Minimum harmonic score: 88%.
- Base equity risk: 0.75%.
- High-quality risk: up to 1.00% only when final score >= 94 and higher-timeframe direction agrees.
- Maximum positions: 1.
- Maximum trades/day: 3.
- Daily drawdown gate: 3%.
- Runtime peak-equity drawdown gate: 12%.
- Maximum consecutive losses: 3.
- Minimum net RR after execution reserve: 1.50.
- Suggested research balance: USD 3,000+ because XAUUSD broker minimum volume can otherwise make structurally valid stops exceed a small percentage-risk budget.

## Promotion gates

A build is not promoted merely because it compiles or because one window is profitable. The GitHub validation workflow calculates the following for each backtest window:

- total trades
- win rate
- net profit
- total ROI
- compounded average monthly ROI
- profit factor
- maximum equity drawdown

Internal Store-candidate gate for a validation window:

- compounded average monthly ROI >= 7%
- profit factor >= 1.30
- max equity drawdown <= 15%
- positive net profit
- minimum trade-count threshold for the window

The 7% level is used because cTrader Store currently hides the displayed monthly ROI metric when its system-calculated compounded monthly ROI is below 7%. It is not a guarantee and is not, by itself, an approval requirement.

## Validation design

Workflow: `.github/workflows/validate-fibonacci-store-rc1.yml`

Initial balance: USD 10,000.
Data mode: server M1 data.
Explicit development cost assumptions: 30 pips spread and USD 35 per million commission. These assumptions must be replaced/confirmed against the broker/account used for the final Store evidence.

Windows:

- XAUUSD M15 development: 2024-01-01 through 2025-12-31.
- XAUUSD M15 recent validation: 2026-01-01 through 2026-09-09.
- XAUUSD H1 recent comparison: 2026-01-01 through 2026-09-09.

Do not tune repeatedly against the recent validation window. If RC1 fails, use diagnostics to define a limited new hypothesis and re-test on development/walk-forward folds before touching final promotion evidence.

## Store publication checklist after performance validation

- Keep `AccessRights.None`.
- Build a final Cloud/local `.algo` and do not lock it to one user.
- Use an accurate product title and description with strategy type, target symbol/period, account size, leverage and risk assumptions.
- Prepare at least three Store screenshots, including reproducible backtest period and parameters.
- Enter ROI, max balance drawdown, dates, profit factor and the actual broker from the final backtest report.
- Complete the cBot trading profile accurately.
- Avoid guaranteed-profit or misleading performance language.
- Preserve the original cloud algo after publication so future updates remain linked to the product.
