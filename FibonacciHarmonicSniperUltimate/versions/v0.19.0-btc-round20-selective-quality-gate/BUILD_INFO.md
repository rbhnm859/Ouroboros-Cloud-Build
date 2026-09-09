# Fibonacci BTC Round20 Selective Quality Gate

Anchor chain: frozen Round17 champion -> Round18 diagnostics -> Round19 quality expansion -> Round20 selective quality gate.

## Round20 hypothesis

Round19 increased Standard trade count from 94 to 99 but reduced ROI/PF and increased drawdown. Post-run attribution showed two independent causes:

1. Round19 reduced ordinary M30 Buy risk from the Round17 0.50% baseline to 0.35%, weakening profitable pre-existing M30 Buy trades.
2. Broad health-bypass admissions displaced higher-value H1 opportunities. Among the executed bypass sequence changes, the 2026-07-04 aligned Buy was the clearest positive addition.

## Default Round20 policy

- H1 logic unchanged; H1 risk 1.0% equity.
- Ordinary M30 Buy/Sell risk restored to 0.50% equity.
- H1 health gate remains enabled.
- Health bypass is selective:
  - Buy only.
  - Reciprocal ABCD candidate must already pass existing confirmation and EMA alignment.
  - M30 pattern score >= 96%.
  - same-direction H1 state age <= 2 hours.
  - Sell bypass disabled.
- MaxOpenPositions = 1.
- No hedging, grid, martingale, DCA, recovery, or loss averaging.

## Round17 hard reference

Standard: 94 trades, ROI 38.48%, PF 1.85, Max DD 5.92%.
Harsh: 92 trades, ROI 19.25%, PF 1.40, Max DD 7.67%.

Round20 is only promoted if it increases trade count and preserves or improves the economic quality gates. Standard and harsh results must be taken from generated cTrader reports, never inferred.

Source SHA-256 expected after transform:
`5916aede6a0fdee5fe5db0c6baa5262213cb07184210ae77036a5cb83dea0691`
