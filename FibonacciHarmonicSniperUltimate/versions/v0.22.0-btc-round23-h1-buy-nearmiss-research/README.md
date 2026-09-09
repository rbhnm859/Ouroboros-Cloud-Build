# BTC Round23 — H1 Buy Near-Miss Research

Round23 is a diagnostics-only research round built on the frozen Round22 Balanced Standard Champion.

It does **not** change live order entry, exit, SL/TP, position count, or risk allocation. The Round22 baseline must remain economically identical during the research backtest.

## Research lanes

- `SCORE_82_84`: Buy patterns scoring 82–84 that pass the other baseline filters.
- `AGE_17_18`: Buy patterns aged 17–18 bars that otherwise pass the baseline.
- `DIST_1.8_2.0`: Buy patterns 1.8–2.0 ATR away that otherwise pass the baseline.
- `CONFIRM_NEXT1`: baseline-quality Buy patterns that fail confirmation on the first bar and are checked once on the next H1 close.

Each candidate is shadow-tracked with the existing Round22 stop/target geometry. The research output records R outcome, MFE/MAE, whether the signal was actually feasible under the one-position/cooldown/daily-limit rules, and whether Round22 later consumed the same signal.

The primary decision set for a possible Round24 expansion is `feasible=true` and `baselineLater=false`.

## Acceptance philosophy

No Round23 signal becomes live merely because it increases count. A Round24 lane should only be promoted if the shadow evidence shows positive expectancy with enough samples and does not require loosening MaxOpenPositions, Grid, Martingale, DCA, Recovery, or other prohibited risk behavior.
