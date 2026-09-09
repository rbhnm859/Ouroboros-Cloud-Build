# Round29 Results — Macro-Asymmetric H1 Sell

GitHub Actions run: `34408465465`

## Method

Round29 was validated without cherry-picking:

1. Full 3-year Standard screen: 2023-09-08 to 2026-09-08.
2. Three profiles were frozen before results were seen.
3. Candidate selected by pre-committed gates/ranking.
4. Selected candidate then tested on all three fixed yearly slices.
5. Full 3-year Harsh and recent 1-year Harsh were run.

Round29 only scales H1 Sell risk when the last fully closed D1 bar is in a macro bull regime. H1 Buy, M30 Buy, M30 Sell, signal thresholds, SL/TP, Round22 base risk allocation and MaxOpenPositions=1 remain frozen.

## Frozen profiles

- Mild: moderate bull scale 0.85 / strong bull scale 0.65
- Balanced: 0.75 / 0.50
- Defensive: 0.60 / 0.35

## 3-year Standard screen

### Round22 / Round26 control
- Trades: 256
- ROI: +26.55%
- Net: +2655.20
- PF: 1.22
- Max balance DD: 21.28%
- Max equity DD: 21.89%

### Mild
- Trades: 256
- ROI: +26.99%
- PF: 1.23
- Max balance DD: 20.65%
- Max equity DD: 20.95%

### Balanced
- Trades: 256
- ROI: +27.48%
- PF: 1.24
- Max balance DD: 20.12%
- Max equity DD: 20.42%

### Defensive — selected
- Moderate bull H1 Sell scale: 0.60
- Strong bull H1 Sell scale: 0.35
- Trades: 255
- ROI: +27.50%
- Net: +2749.57
- PF: 1.25
- Max balance DD: 20.08%
- Max equity DD: 20.38%

Frozen 3Y gates:
- Trades >=250: PASS
- ROI > control: PASS
- PF >=1.30: FAIL
- Equity DD <=18%: FAIL

Therefore `pass_all = false`.

## Fixed annual validation — Defensive

### 2023-09-08 to 2024-09-08
- Trades: 90
- ROI: -0.75%
- Net: -74.76
- PF: 0.98
- Max balance DD: 12.01%
- Max equity DD: 12.66%

### 2024-09-08 to 2025-09-08
- Trades: 59
- ROI: -4.96%
- Net: -496.26
- PF: 0.82
- Max balance DD: 8.94%
- Max equity DD: 10.00%

### 2025-09-08 to 2026-09-08
- Trades: 95
- ROI: +39.31%
- Net: +3930.91
- PF: 1.94
- Max balance DD: 4.91%
- Max equity DD: 5.66%

Recent-year gates all PASS, but robustness gates fail because only one of the three fixed years is profitable and the worst-year PF is 0.82 (<0.90).

## Harsh validation

### Full 3Y Harsh
- Trades: 245
- ROI: -1.77%
- Net: -176.74
- PF: 0.98
- Max balance DD: 22.60%
- Max equity DD: 22.91%

### Recent 1Y Harsh
- Trades: 95
- ROI: +17.85%
- Net: +1785.07
- PF: 1.39
- Max balance DD: 6.24%
- Max equity DD: 6.45%

The recent Harsh gates pass, but the full 3Y Harsh non-negative ROI and PF>=1.00 gates fail.

## Regime counts

Across the full 3Y Standard run, H1 Sell entries were classified as:
- Neutral/non-bull: 32
- Moderate bull: 7
- Strong bull: 30

By year under the selected profile:
- 2023-2024: neutral 7 / moderate bull 2 / strong bull 14
- 2024-2025: neutral 2 / moderate bull 2 / strong bull 16
- 2025-2026: neutral 24 / moderate bull 2 / strong bull 0

This explains why the asymmetric rule preserves the strong recent year: almost all recent H1 Sells are outside the D1 strong-bull regime, while the two earlier weak years contained many strong-bull H1 Sells.

## Decision

`promotion_eligible = false`

**Round29 must not replace Round22 as Standard Champion.**

Round29 is nevertheless a useful research improvement over Round27/Round28 because it improves the weak 2024-2025 year substantially while preserving the recent-year performance. The remaining bottleneck is that H1 Sell macro scaling alone cannot raise 3Y PF to >=1.30 or reduce 3Y drawdown to <=18%, and full-3Y Harsh remains slightly negative.

Recommended next research step: keep the Round29 macro-asymmetric H1 Sell concept as a candidate component, but address the remaining non-H1-Sell losses with an independent alpha/exit-quality change rather than further shrinking H1 Sell risk.
