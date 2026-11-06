# R19 Next Data Gate — NO_FILL and forward tick audit

The sealed R18 logs contain pre-decision feature frames (R15 trajectory, R16 micro, R17 tick-state aggregates) and outcome records of the EXISTING R18 actions. They are not a source-certified chronological full bid/ask tick tape for newly created R19 action templates. Do not synthesize outcomes for R19_A1–A4 from old outcome labels.

From full ZIP-hash-verified 2016–2020 R18 research outcomes, the number of unique events with **any positive executed R18 action** BEFORE cap proxy and net RR constraints is respectively **113, 107, 128, 114, 138**; each is below the 175 winners necessary at N=250/WR=70%. Therefore a stronger classifier, removal of the R18 capital proxy or simply bypassing the R18 planned-RR filter cannot rescue that fixed action outcome universe. The outcome universe itself must change.

Observed event attrition per research year is in R19_R18_ATTRITION.json, alongside the original more restrictive certified bounds R19_R18_VERIFIED_BOUNDS.json.

## Next authorized necessary evidence

1. Check original Carney family grammar against code without modifying V51, and determine which pattern-specific PRZ/confirmation/structural stop formulas can be calculated strictly at decision time.
2. Implement a closed, pre-registered four-template research-only R19 action simulator with real chronological executable-side cTrader tick input, session/fee/margin semantics, and precise event timestamps. This is NOT possible from the existing aggregate frame features alone.
3. Start only a minimal tick fixture / short DEV interval for parity first; no multi-year costly replay until the source-certified simulator passes golden Python/C# parity and independent review.
4. Use 2016–2020 research folds only; burned 2021–2023, Validation/Fresh and live orders remain forbidden.
