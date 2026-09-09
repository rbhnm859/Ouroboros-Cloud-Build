# BTC Harmonic Guard — Store Edition v1.0

Base: Round26 architecture with Round22 Champion economics.

## Objective
First make the product live-safe and Store-safe. Only then optimize monthly geometric compounding. No change is promoted merely because it increases a short-window ROI.

## P0 hardening
1. Champion Balanced settings become code defaults (not an external JSON dependency): R21 bypass score 93, bypass risk 0.10%, H1 buy/sell risk 1.15/0.80%, M30 buy/sell risk 0.40/0.50%, MaxOpenPositions hard-capped to 1, MaxTradesPerDay 6, MaxDailyLossPercent 5, MinimumRR 1.50, FallbackRR 1.80, diagnostics/research switches off unless explicitly debug-only.
2. Hard no-hedging / no-grid / no-martingale / no-DCA / no-recovery invariant. New entries are rejected whenever an owned position already exists.
3. Unify H1 and M30 sizing through one percent-of-equity risk engine. Store edition removes ambiguous FixedLots/FixedCash behavior from the active execution path.
4. Pre-trade broker validation: normalized volume must satisfy min/max/step; estimated AmountRisked must not exceed budget; SL/TP distances must be valid; insufficient margin/invalid protection rejects the trade before execution when detectable.
5. Protection fail-safe: every market entry must have SL and TP. If post-entry protection is missing/invalid, immediately attempt close; check ClosePosition result; retry with bounded attempts; stop new entries and emit a fatal protection lock if the position cannot be made safe.
6. Persistent/reconstructed daily controls across restart: daily trade count and daily realized P/L are reconstructed from History for the current UTC trading day; current open risk is included in safety checks. Restart must not reset the daily-loss lock.
7. Reconstruct duplicate-signal guards from current positions/history where possible so restart cannot intentionally re-enter the same already-consumed signal.
8. Startup validation: intended Store profile is BTC/BITCOIN on H1; unsupported symbol/timeframe requires explicit override or refuses live trading. Log broker symbol limits and effective risk settings.
9. Store product name <= 40 chars: `BTC Harmonic Guard`.
10. Research-only Round switches remain internal/hidden in the Store build where possible. Customer-facing controls target <= 25 parameters.

## Monthly geometric compounding objective
The optimization target is geometric monthly growth, not one attractive month.

For each candidate calculate monthly return r_m and:
- geometric monthly return = (product(1+r_m))^(1/N)-1
- median monthly return
- worst month
- percentage of positive months
- monthly return standard deviation
- longest losing-month streak

### Frozen candidate methodology
Use only a small precommitted screen. No brute-force parameter mining.

Candidate A — Store Champion control:
- exact Round22 economic behavior after hardening parity.

Candidate B — Balanced compound:
- preserve H1 Buy 1.15%, H1 Sell 0.80%, M30 Buy 0.40%, M30 Sell 0.50% baseline;
- continuous causal quality multiplier only: 0.75x / 1.00x / 1.10x;
- multiplier may use only fully closed higher-timeframe information;
- never increase risk after a loss; no P/L-chasing or martingale behavior.

Candidate C — Conservative compound:
- multiplier 0.60x / 1.00x / 1.05x;
- same causal quality inputs and no binary trade blocking.

Candidate D — Continuation alpha shadow first:
- independent H1/H4 trend-continuation/pullback signal;
- initially shadow-only and does not trade until its OOS sample passes its own gate;
- purpose is to increase opportunity count without loosening harmonic thresholds.

## Validation windows
Use the longest continuous FxPro BITCOIN history available, with the same cost model used for the validated Champion.
Required reports:
- full 3Y Standard
- fixed annual Y1/Y2/Y3
- recent 1Y Standard
- recent 1Y Harsh
- rolling 6-month windows
- calendar-month return table
- trade-order Monte Carlo / bootstrap if the workflow supports it

## Promotion gates
A candidate is NOT promoted unless all are true:
- full 3Y trades >= 250
- full 3Y PF >= 1.30
- full 3Y equity DD <= 18%
- recent 1Y trades >= 95
- recent 1Y PF >= 1.80
- recent 1Y equity DD <= 6%
- recent 1Y ROI >= 39.93% OR geometric monthly return improves by >= 10% relative while recent ROI is no worse than -5% relative
- Harsh recent PF >= 1.35
- Harsh recent DD <= 6.8%
- at least 2 of 3 fixed years positive
- worst yearly PF >= 0.90
- no calendar month loss worse than the control by > 3 percentage points
- no hardening safety regression

If no candidate passes, retain Round22 economics and ship only the hardening changes. Do not manufacture a higher monthly-return claim.
