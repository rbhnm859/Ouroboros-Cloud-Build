# BTC Round 12 — H1 Frequency Expansion Decision

## Baseline

Production/Growth control remains H1 `Reciprocal ABCD` with Pivot 2/2, tolerance 6, MinPatternScore 84, MaxPatternAgeBars 16, MaxEntryDistanceAtr 1.80, ConfirmationMoveAtr 0.05, candle confirmation enabled, CooldownBars 2, 1% risk, LegacyD stop anchor and LegacyFallback target policy.

## H1 second-pattern screening

Nineteen H1 harmonic families were screened individually on the fixed development window 2026-03-08 through 2026-08-08. Most patterns were either too sparse or negative. The only candidate with meaningful additional frequency and positive development-period edge was `121`.

Selected development observations:

- `121`: 14 trades, +1.96% ROI, PF 1.21, max DD 5.72%.
- `Max Bat`: 4 trades, +1.14% ROI, PF 1.52, max DD 3.17%; too sparse for the frequency objective.
- `3 Drives`: 3 trades, +2.69% ROI, PF 3.64; too sparse.
- `ABCD`: 20 trades, -3.94% ROI, PF 0.76, max DD 8.44%; rejected.
- `Max Gartley`: 1 trade, -1.07% ROI, PF 0; rejected.

## Frozen OOS check for 121

Frozen OOS: 2026-08-09 through 2026-09-08.

- H1 Control: 7 trades, +7.74% ROI, PF 4.17, max DD 2.83%.
- H1 Control harsh costs: 7 trades, +3.30% ROI, PF 1.75, max DD 4.12%.
- `121` alone: 0 trades in normal and harsh OOS.
- `Reciprocal ABCD + 121`: identical to Control in OOS, because 121 contributed no OOS trades.

## Six-month combination result

Normal costs:

- Control: 37 trades, +31.82% ROI, PF 2.68, max DD 4.40%.
- `Reciprocal ABCD + 121`: 49 trades, +29.68% ROI, PF 1.99, max DD 8.64%.

Harsh costs:

- `Reciprocal ABCD + 121`: 49 trades, +12.75% ROI, PF 1.37, max DD 9.04%.

## Decision

Do **not** promote `121` into the production H1 engine. It increases six-month trade count from 37 to 49 (+32%) but lowers normal ROI and PF, nearly doubles drawdown, and contributes zero trades in the most recent frozen OOS month. Keep it only as a research/frequency challenger.

The production H1 Growth Champion remains unchanged.

Proceed to BTC Round 13: independently calibrate an M30 `Reciprocal ABCD` engine using development data only, then validate any selected M30 candidate on the untouched frozen OOS and harsh-cost tests before considering combination with the H1 champion.

No Grid, Martingale, DCA, Recovery, Loss Averaging, or Hedging logic is introduced by this decision.
