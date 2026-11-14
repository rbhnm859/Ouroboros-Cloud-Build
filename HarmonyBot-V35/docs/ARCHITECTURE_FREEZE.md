# HarmonyBot V35.0 — Regime-Aware Harmonic Alpha Architecture

## Purpose
V35 is an Alpha-layer refactor after V34 passed clean engineering regression but failed fresh Normal validation. V35 does **not** use the 2020-H1 validation result for parameter tuning.

## Frozen V34 execution/risk kernel
The following mechanisms are inherited and may not be weakened in V35 Development:
- post-fill structural safety / fail-close
- actual-fill basket risk reconciliation
- server SL/TP protection confirmation
- monotonic protection frontier / no stop widening
- Fibonacci logical grid levels 0 / .236 / .382 / .618
- normal grid weights 3/7, 2/7, 1/7, 1/7
- BasketRiskPercent <= 1%
- anti-hedge / one active basket / duplicate prevention
- execution state machine
- adaptive capital / broker minimum-volume checks
- margin headroom / daily loss / max DD locks
- London-open through New-York-close DST-aware session
- no Grid/Martingale/DCA/Recovery/Loss Averaging rescue

## V35 research modules
Only four modules are under study:
1. Enhanced Harmonic Robustness — combines ratio geometry, PRZ confluence, time symmetry and pivot quality; weak time/pivot structure cannot be hidden by one strong ratio score.
2. Regime Context — H4/H1 trend, M15 ATR percentile, efficiency ratio and H1/H4 ADX context. Strong/rising counter-trend regimes are rejected unless a true exhaustion condition exists.
3. Enhanced M1 Confirmation — completed-bar directional reclaim, one/two-bar structure break, rejection wick, failed extension and displacement.
4. Capital Feasibility Precheck — identifies candidates that cannot safely execute even minimum L0 under the frozen 1% basket budget and broker margin constraints. It never raises risk or forces minimum volume.

## Indicator governance
ADX, efficiency ratio and ATR percentile are context/regime evidence, not independent entry triggers. Harmonic/Fibonacci remains the only setup generator. No RSI/MACD/Stochastic/Bollinger stack is added.

## Data governance
- 2020-H1 Fresh Validation is now EXPOSED_VALIDATION_FAILED and may never be used to tune V35.
- DEV-A/B/C (2021-01-04..2022-06-30) remain EXPOSED_DEVELOPMENT and are allowed for architecture ablation only.
- 2022-H2 is EXPOSED retired validation.
- 2023-01-02..2023-08-31 remains protected Final Holdout and must not be run.
- A new validation interval must be proven and reserved only after V35 Development architecture is frozen.

## One-pass ablation
Normal-capital Development compares exactly five fixed families:
- BASE_V34: all V35 alpha modules OFF
- QUALITY_ONLY
- REGIME_ONLY
- CONFIRM_ONLY
- FULL_V35: Quality + Regime + Confirmation + Capital Feasibility

No threshold sweep is authorized. The pre-registered default Min Harmonic Robustness is 0.56.

FULL_V35 is also run on $100 across DEV-A/B/C strictly for capital-feasibility engineering evidence, not performance promotion.

## Development advancement gate
A family may be nominated for a new fresh validation reservation only if:
- engineering clean in all three windows
- no window DD > 10%
- aggregate Net > 0
- aggregate PF > 1
- aggregate Expectancy > 0
- at least 2 of 3 windows Net >= 0
- at least 30 baskets total
- no execution/risk invariant regression

Development results cannot be commercial evidence.
