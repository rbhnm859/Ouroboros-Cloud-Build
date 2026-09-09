# Round24 — H1 Buy Distance Validation

Purpose: validate the only positive Round23 near-miss hypothesis before changing live trading logic.

## Frozen hypothesis

Round23 found one genuinely new, feasible H1 Buy candidate in the `DIST` bucket (`1.80 < entry distance <= 2.00 ATR`) that produced +1.80R. Score 82–84 and age 17–18 were negative and remain rejected.

Round24 does **not** enable new trades. It extends the same shadow diagnostic to a 3-year BTC H1 sample and compares diagnostics-on vs diagnostics-off on the exact same binary so instrumentation cannot silently change strategy economics.

## Period

- 2023-09-08 00:00 UTC through 2026-09-08 00:00 UTC
- Segment A: 2023-09-08 → 2024-09-08
- Segment B: 2024-09-08 → 2025-09-08
- Segment C: 2025-09-08 → 2026-09-08

## Pre-committed research gate for DIST lane

A live Round24/25 implementation is justified only if the truly new feasible `DIST` sample (`feasible=true`, `baselineLater=false`) meets all of:

- count >= 5
- total R > +2.0R
- average R > +0.20R
- R-based profit factor >= 1.30
- at least 2 of 3 yearly segments have positive total R

If it fails, Round22 remains the Standard Champion and `MaxEntryDistanceAtr=1.80` stays frozen.

## Constraints kept frozen

- MaxOpenPositions = 1
- no Grid / Martingale / Hedging / DCA / Recovery
- MinPatternScore = 84
- MaxPatternAgeBars = 16
- existing Round22 risk allocation unchanged
- no execution changes in this research round
