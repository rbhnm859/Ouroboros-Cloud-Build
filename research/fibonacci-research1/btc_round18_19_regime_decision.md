# BTC Harmonic Frequency — Round 18/19 Regime Decision

## Decision

Round 17 remains the **BTC Harmonic Frequency Research Champion**.

Do not promote Round 18 or Round 19. Do not continue tuning against PRE6 merely to force PF above 1.0; the latest tests show that doing so damages performance in adjacent periods and increases curve-fitting risk.

## Round 17 frozen reference

- H1 Reciprocal ABCD primary engine
- M30 Reciprocal ABCD frequency engine
- M30 enabled only when at least 2 of the last 3 closed H1 trades are profitable
- H1 risk: 1.0% equity
- M30 risk: 0.5% equity
- MaxOpenPositions: 1
- no hedging / grid / martingale / DCA / recovery / loss averaging

Validated metrics:

| Window | Trades | ROI | PF | Max Equity DD |
|---|---:|---:|---:|---:|
| FULL6 | 71 | +39.23% | 2.22 | 5.30% |
| FULL6 harsh | 69 | +19.78% | 1.56 | 7.57% |
| OOS | 14 | +6.47% | 2.20 | 1.88% |
| OOS harsh | 12 | +1.88% | 1.28 | 2.90% |
| PRE6 | 21 | -0.69% | 0.95 | 5.72% |
| PRE6 harsh | 21 | -1.06% | 0.92 | 5.85% |
| FULL12 continuous | 94 | +38.48% | 1.85 | 5.92% |
| FULL12 continuous harsh | 92 | +19.25% | 1.40 | 7.67% |

## Round 18 — latest H1 win requirement

Hypothesis: retain the existing 2-of-3 H1 health gate but additionally require the latest H1 closed trade to be profitable before M30 may enter.

Result: reject.

- PRE6 remained essentially unchanged: 21 trades, about -0.69%, PF 0.95.
- PRE6 harsh remained about -1.06%, PF 0.92.
- FULL6 fell to 69 trades; harsh fell to 67 trades.
- FULL6 harsh PF weakened to about 1.53.
- The first half of PRE6 contained 10 trades and **zero M30 trades**, yet still produced about -2.05% / PF 0.72. Therefore the remaining PRE6 weakness cannot be repaired by further tightening the M30 gate.

## Round 19 — H1 cold-risk throttle

Hypothesis: keep all H1 entries, but reduce H1 risk from 1.0% to 0.5% whenever fewer than 2 of the last 3 H1 trades are profitable; restore 1.0% once health recovers. M30 remains at Round 17 rules and 0.5% risk.

Result: reject.

Paired split test:

- Old-A control: 10 trades, -2.05%, PF 0.72, DD 5.10%.
- Old-A cold-risk: 10 trades, -1.67%, PF 0.67, DD 3.55%.
- Old-B control: 11 trades, +1.44%, PF 1.26.
- Old-B cold-risk: 11 trades, -0.03%, PF 0.99.

Full-window confirmation:

- PRE6 cold-risk: 21 trades, -1.48%, PF 0.84, DD 4.50%.
- PRE6 harsh cold-risk: 21 trades, -1.74%, PF 0.81, DD 4.55%.
- FULL6 cold-risk: 71 trades, +34.08%, PF 2.14, DD 5.02%.
- FULL6 harsh cold-risk: 69 trades, +16.04%, PF 1.51, DD 6.65%.

The throttle reduced drawdown but damaged the positive Old-B recovery regime and reduced both PRE6 and recent FULL6 expectancy. It therefore does not generalize.

## Research conclusion

The catastrophic M30 regime dependence seen in Round 15 has already been substantially solved by the Round 16 H1-health gate and Round 17 asymmetric risk split. The small residual PRE6 loss is now primarily associated with the H1 edge itself rather than uncontrolled M30 frequency exposure.

Further parameter fitting to PRE6 is not justified. Round 17 should stay frozen. The next evidence should come from independent forward/shadow data or an untouched historical period, not additional tuning on PRE6 or the existing OOS window.
