# Fibonacci Harmonic Sniper Ultimate — BTC Round18 Frequency

This branch isolates the first Round18 objective: **increase valid trade count before optimizing ROI or net profit**.

## Immutable benchmark
Round17 is the comparison benchmark and must not be overwritten.

- BITCOIN / H1
- 2025-09-08 through 2026-09-08
- Initial balance: USD 10,000
- Standard-cost benchmark: 94 trades, ROI +38.48%, Profit Factor 1.85, max equity drawdown about 5.92%
- Harsh-cost benchmark: 92 trades, ROI +19.25%, Profit Factor 1.40, max drawdown about 7.67%

## Round18 frequency changes
The H1 primary strategy stays at 1.0% equity risk. The existing M30 Reciprocal ABCD lane stays at 0.50% risk. New frequency comes from a deliberately smaller M30 ABCD expansion lane at 0.25% risk.

Round18 also allows a narrow H1-alignment bypass when the older Round16 health gate blocks an M30 candidate, but only when the recent H1 harmonic state points in the same direction and meets the configured confidence/age limits.

Default frequency parameters:

- M30 cooldown: 3 bars
- H1 alignment bypass: enabled
- H1 alignment max age: 6 bars
- H1 minimum confidence: 0.65
- M30 ABCD expansion: enabled
- ABCD minimum score: 88%
- ABCD ratio tolerance: 5%
- ABCD maximum age: 20 bars
- ABCD trend confirmation: required
- ABCD risk: 0.25% equity

## Phase-1 research gates
These are candidate research gates, not profitability guarantees.

- Primary target: at least 110 one-year trades; any statistically meaningful increase over 94 is recorded.
- Standard-cost Profit Factor: >= 1.40
- Harsh-cost Profit Factor: >= 1.20
- Standard max equity drawdown: <= 8%
- Harsh max equity drawdown: <= 10%
- Every position must retain SL/TP protection.
- No Grid, Martingale, DCA, recovery, loss averaging, or hedging logic.

If trade count does not improve without unacceptable PF/DD deterioration, the candidate is rejected rather than forcing more trades.

## Rebuilding the source
The GitHub connector stores the large C# source in six deterministic parts. Run:

```bash
python3 assemble_source.py
```

This creates `FibonacciHarmonicSniperUltimate.cs` before compilation. The workflow verifies that all six parts exist.

## Validation scenarios
The dedicated workflow tests the same one-year BITCOIN/H1 window under two cost assumptions:

1. Standard: spread 0, commission 65 USD per million.
2. Harsh: spread 1500, commission 100 USD per million.

The workflow uploads the compiled `.algo`, HTML/JSON reports, and a concise comparison summary. Phase 2 (ROI/net-profit optimization) starts only after Phase 1 trade-frequency validation.
