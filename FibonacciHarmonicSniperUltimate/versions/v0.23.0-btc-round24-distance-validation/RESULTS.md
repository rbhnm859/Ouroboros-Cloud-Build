# Round24 3Y Distance Validation — Results

## Executive result

The `1.80 < H1 Buy entry distance <= 2.00 ATR` hypothesis remains promising but **does not pass the pre-committed research gate** because the truly new feasible sample is still too small.

### 3-year Round22 control baseline

- Period: 2023-09-08 → 2026-09-08
- Trades: 256
- ROI: 26.55%
- Net: +2655.20 on 10,000 initial balance
- Profit Factor: 1.22
- Max equity drawdown: 21.8930%

Diagnostics-on produced the same trading metrics, confirming instrumentation did not change the strategy path.

## Corrected DIST_1.8_2.0 shadow result

The workflow summary used the short label `DIST`, while the raw cBot log emits `DIST_1.8_2.0`. The raw log was therefore re-parsed using the actual category name.

Truly new feasible candidates (`feasible=true`, `baselineLater=false`):

1. 2023-10-23 16:00 UTC — score 87.87 — distance 1.990 ATR — TARGET — +1.80R
2. 2024-05-22 16:00 UTC — score 87.40 — distance 1.988 ATR — STOP — -1.00R
3. 2025-11-28 05:00 UTC — score 84.33 — distance 1.907 ATR — TARGET — +1.80R

Aggregate:

- Count: 3
- Wins / losses: 2 / 1
- Total R: +2.60R
- Average R: +0.8667R
- R-based PF: 3.60
- Positive yearly segments: 2 of 3

### Pre-committed gate

- count >= 5: **FAIL**
- total R > +2.0R: PASS
- average R > +0.20R: PASS
- R-based PF >= 1.30: PASS
- at least 2 of 3 yearly segments positive: PASS

Final research gate: **FAIL — insufficient sample size only.**

`MaxEntryDistanceAtr` therefore remains frozen at **1.80** in the production Round22 Champion.

## More important 3-year finding: regime dependence

Lane attribution from the 3-year Round22 control shows the larger optimization problem is regime robustness, not entry-distance scarcity.

### 2023-09-08 → 2024-09-08

- All: 90 trades, +162.02, PF 1.03
- H1 Buy: 20 trades, +51.74, PF 1.03
- H1 Sell: 23 trades, +825.17, PF 1.77
- M30 Buy: 23 trades, -272.12, PF 0.63
- M30 Sell: 24 trades, -442.77, PF 0.57

### 2024-09-08 → 2025-09-08

- All: 63 trades, -1011.44, PF 0.72
- H1 Buy: 23 trades, -290.25, PF 0.84
- H1 Sell: 20 trades, -715.92, PF 0.45
- M30 Buy: 11 trades, -85.85, PF 0.61
- M30 Sell: 9 trades, +80.58, PF 1.43

### 2025-09-08 → 2026-09-08

- All: 102 trades, +3558.63, PF 1.89
- H1 Buy: 26 trades, +2549.41, PF 3.32
- H1 Sell: 26 trades, +374.73, PF 1.26
- M30 Buy: 23 trades, +341.69, PF 1.63
- M30 Sell: 27 trades, +292.80, PF 1.32

## Professional conclusion

Round22 is a strong recent-regime Standard Champion, but the 3-year test shows material regime dependence. The next optimization priority should be a **causal regime/lane quality mechanism** that protects weak H1 Sell and M30 periods without using look-ahead and without simply reducing all trading.

Only after 3-year PF and drawdown improve should the project re-open controlled trade-count expansion such as the 1.8–2.0 ATR H1 Buy lane.
