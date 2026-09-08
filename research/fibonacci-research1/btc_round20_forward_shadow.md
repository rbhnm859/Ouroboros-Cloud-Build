# BTC Round20 — Frozen Forward / Shadow Validation

## Frozen candidate

Round 17 remains completely frozen:

- H1 Reciprocal ABCD primary engine
- M30 Reciprocal ABCD frequency engine
- M30 allowed only when at least 2 of the last 3 closed H1 trades are profitable
- H1 risk = 1.0% equity
- M30 risk = 0.5% equity
- MaxOpenPositions = 1
- no hedging / grid / martingale / DCA / recovery / loss averaging
- no Round18 or Round19 changes

## Forward boundary

Development / historical evaluation ends before this forward stream.

Forward start: **08/09/2026 00:00 UTC**.

Round20 must not change entry logic, pattern parameters, risk parameters, or health-gate rules in response to forward outcomes. Forward observations are evidence only.

## Initial shadow snapshot

GitHub Actions run: `34273125085`

Observed window: `08/09/2026 00:00` to approximately `08/09/2026 20:09 UTC`.

| Profile | Trades | Net Profit | ROI | PF | Max DD |
|---|---:|---:|---:|---:|---:|
| Normal | 0 | 0 | 0% | N/A | 0% |
| Harsh | 0 | 0 | 0% | N/A | 0% |

Diagnostics from the initial snapshot:

- H1 did not open a trade during the observed sub-day window.
- M30 opened 0 trades.
- M30 health gate blocked candidates while fewer than three closed H1 trades were available in this fresh forward stream.
- H1 diagnostics included confirmation-gate rejections and no-candidate/conflict observations.

A zero-trade first snapshot is not grounds for parameter modification. The sample is far too small for performance inference.

## Promotion discipline

Do not promote or reject Round17 from one day of forward data.

Continue accumulating untouched forward evidence. Evaluate only after a meaningful number of new trades has accumulated, with particular attention to:

- normal and harsh PF
- Max Equity DD
- H1/M30 contribution split
- whether M30 remains additive rather than destructive
- cost sensitivity
- frequency relative to the historical 69–71 trades / 6 months benchmark

The existing historical OOS/PRE6 windows remain frozen and must not be reused for new parameter fitting.
