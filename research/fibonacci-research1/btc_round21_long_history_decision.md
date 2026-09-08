# BTC Harmonic Frequency — Round 21 Long-History Validation

## Scope

Round 17 remained fully frozen. No entry, exit, pattern, risk, or health-gate parameters were changed.

Tested BITCOIN / H1 portfolio with normal and harsh costs across continuous 2Y, continuous 3Y, and three annual slices.

Frozen Round 17 reference:
- H1 Reciprocal ABCD primary engine, 1.0% equity risk
- M30 Reciprocal ABCD frequency engine, 0.5% equity risk
- M30 enabled only when at least 2 of the last 3 closed H1 trades are profitable
- MaxOpenPositions=1
- no hedging / grid / martingale / DCA / recovery / loss averaging

## Continuous results

| Window | Trades | ROI | PF | Max Equity DD |
|---|---:|---:|---:|---:|
| 2Y normal | 153 | +26.65% | 1.34 | 14.79% |
| 2Y harsh | 149 | +0.53% | 1.01 | 20.80% |
| 3Y normal | 246 | +31.76% | 1.24 | 21.08% |
| 3Y harsh | 238 | -3.79% | 0.97 | 26.91% |

## Annual slices

| Window | Trades | ROI | PF | Max Equity DD |
|---|---:|---:|---:|---:|
| 2023-09-08 to 2024-09-07 normal | 90 | +6.67% | 1.13 | 11.13% |
| 2023-09-08 to 2024-09-07 harsh | 86 | -2.53% | 0.95 | 11.83% |
| 2024-09-08 to 2025-09-07 normal | 51 | -7.12% | 0.79 | 12.20% |
| 2024-09-08 to 2025-09-07 harsh | 49 | -13.75% | 0.61 | 18.28% |
| 2025-09-08 to 2026-09-08 normal | 94 | +38.48% | 1.85 | 5.92% |
| 2025-09-08 to 2026-09-08 harsh | 92 | +19.25% | 1.40 | 7.67% |

## Engine contribution diagnostics

Continuous 3Y normal:
- H1: 139 trades, net +3541.79
- M30: 107 trades, net -365.53

Continuous 3Y harsh:
- H1: 138 trades, net +816.22
- M30: 100 trades, net -1195.16

Continuous 2Y normal:
- H1: 95 trades, net +1800.28
- M30: 58 trades, net +865.17

Continuous 2Y harsh:
- H1: 94 trades, net -64.80
- M30: 55 trades, net +117.30

Annual engine notes:
- 2023-2024 normal: H1 +1755.61, M30 -1088.28.
- 2023-2024 harsh: H1 +822.97, M30 -1076.40.
- 2024-2025 normal: H1 -860.01, M30 +148.04.
- 2024-2025 harsh: H1 -1222.28, M30 -152.68.
- 2025-2026 normal: H1 +2849.84, M30 +998.27.
- 2025-2026 harsh: H1 +1377.71, M30 +546.80.

## Decision

Round 17 remains a **BTC Harmonic Frequency Research Champion**, but it does **not** qualify as a production candidate under a 3-year robustness standard.

Reasons:
1. 3Y harsh PF falls below 1.0 (0.97) and ROI is negative (-3.79%).
2. Continuous 3Y max equity drawdown reaches 21.08% normal and 26.91% harsh, materially above the preferred research limits.
3. The 2024-2025 annual slice is clearly negative under both normal and harsh costs.
4. M30 improves recent frequency and recent-year performance, but its 3Y aggregate contribution is negative, especially under harsh costs.
5. H1 itself also has a cold regime in 2024-2025, so the problem cannot be solved merely by disabling M30 everywhere.

Do not tune directly to force these already-observed long-history windows above PF 1.0. Use them as diagnostic evidence. Any next regime-qualification hypothesis should be developed on a separated development subset and then validated on an untouched historical or forward segment.
