# Round23 H1 Buy Near-Miss Findings

## Baseline integrity

Round23 diagnostics preserved the frozen Round22 Balanced economics exactly within the workflow gate:

- Trades: 95
- ROI: 39.93%
- Net: 3993.04 on 10,000
- Profit Factor: 1.95
- Max Equity Drawdown: 5.6463%

## Shadow research

Total shadow candidates: 15

All shadow candidates combined:

- Positive-R outcomes: 7 / 15
- Sum R: +4.0448R
- Average R: +0.2697R
- R-based PF: 1.5056
- 7 candidates were later consumed by the Round22 baseline

The primary decision set is restricted to candidates that were both `feasible=true` at the signal time and `baselineLater=false`.

### Feasible + genuinely new candidates

Total: 3

- Sum R: -0.20R
- Average R: -0.0667R
- R-based PF: 0.90

By lane:

1. `DIST_1.8_2.0`
   - 1 genuinely new feasible candidate
   - +1.80R
   - Target hit
   - Candidate: 2025-11-28 05:00 UTC, score 84.33, age 2, distance 1.907 ATR

2. `SCORE_82_84`
   - 1 genuinely new feasible candidate
   - -1.00R
   - Stop hit

3. `AGE_17_18`
   - 1 genuinely new feasible candidate
   - -1.00R
   - Stop hit

4. `CONFIRM_NEXT1`
   - 9 total shadows looked positive in aggregate (+4.4448R, R-PF 2.1112), but 6 were later consumed by the baseline and none qualified as both feasible and genuinely new.
   - Therefore this lane does not currently add independent trade count under the existing one-position/cooldown constraints.

## Decision

Do not promote Score 82–84 or Age 17–18 into live trading.

Do not promote next-bar confirmation as an independent lane because the apparent performance is mostly overlap with trades the baseline already takes.

Distance 1.8–2.0 ATR is the only lane with a positive genuinely-new observation, but n=1 is insufficient evidence for live promotion. Keep Round22 as the Standard Champion.

The next statistically responsible step is a wider historical robustness study of the Distance 1.8–2.0 ATR H1 Buy lane before creating a Round24 live candidate.
