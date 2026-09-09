# Round27 Results — Lane-Specific Regime Validation

GitHub Actions run: 34350690549

## Method

Round27 was evaluated in a fixed order to avoid cherry-picking:
1. Full 3-year Standard screen: 2023-09-08 to 2026-09-08.
2. Candidate selection using gates committed before results were known.
3. Fixed yearly slices for all three years.
4. Full 3-year Harsh and recent 1-year Harsh validation.

Round26 exact-parity core architecture remained the base. H1 Buy, M30 Sell, SL/TP geometry, Round22 risk allocation, MaxOpenPositions=1 and all core signal thresholds were frozen.

## 3-year Standard screen

Frozen Round22/Round26 control:
- Trades: 256
- ROI: 26.55%
- Net: +2655.20
- PF: 1.22
- Max equity DD: 21.8930%

### M30 Buy Strict — selected by frozen ranking
- H1 Sell regime mode: off
- M30 Buy regime mode: strict H1 EMA alignment
- Trades: 241
- ROI: 27.38%
- Net: +2738.24
- PF: 1.22
- Max equity DD: 21.4435%
- Gates passed: trades >=240, ROI >26.55
- Gates failed: PF >=1.30, DD <=18%
- `pass_all = false`

### H1 Sell Soft
- Trades: 215
- ROI: 24.94%
- Net: +2494.45
- PF: 1.25
- DD: 13.5977%
- Strong DD improvement, but trade count and ROI regressed and PF did not reach 1.30.

### Combined
- Trades: 202
- ROI: 22.70%
- Net: +2269.73
- PF: 1.22
- DD: 13.7980%
- DD improved but trade count and return deteriorated materially.

## Fixed annual validation of selected M30 Buy Strict

### 2023-09-08 to 2024-09-08
- Trades: 87
- ROI: +8.91%
- Net: +890.51
- PF: 1.19
- DD: 9.8180%

### 2024-09-08 to 2025-09-08
- Trades: 59
- ROI: -9.26%
- Net: -926.40
- PF: 0.73
- DD: 14.1809%

### 2025-09-08 to 2026-09-08
- Trades: 89
- ROI: +34.60%
- Net: +3460.35
- PF: 1.85
- DD: 5.6338%

The recent-year gates failed on trade count (89 < 90) and ROI (34.60% < 35%). PF and DD passed. The worst yearly PF remained only 0.73, so the regime-dependence problem was not solved.

## Harsh validation

### Full 3Y Harsh
- Trades: 230
- ROI: -6.37%
- Net: -637.05
- PF: 0.95
- DD: 24.9629%

### Recent 1Y Harsh
- Trades: 89
- ROI: +14.36%
- Net: +1435.53
- PF: 1.32
- DD: 6.4819%

Recent Harsh PF failed the pre-committed >=1.35 gate; DD passed.

## Decision

`promotion_eligible = false`.

Round27 must not replace Round22 as Standard Champion. Round26 remains the preferred engineering/development base because it has exact economic parity with Round22.

## What Round27 taught us

- Hard/soft trend filtering can materially reduce drawdown, especially on H1 Sell, but it removes too many trades and sacrifices return.
- Strict H1 alignment for M30 Buy gives a small 3Y ROI lift (+0.83 percentage points) but does not improve PF and barely changes long-horizon DD.
- The 2024-2025 weak regime remains unresolved (PF 0.73), so a simple EMA price/slope state is not sufficient as the regime model.
- The next experiment should not tighten these filters further. It should use the Round26 layered architecture for a richer *quality score / risk scaling* model rather than binary blocking, and should add an independent trend-continuation alpha only after the regime layer is validated.
