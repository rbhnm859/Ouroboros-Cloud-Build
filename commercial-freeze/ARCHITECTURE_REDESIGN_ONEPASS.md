# HarmonyBot Architecture Redesign → Commercial Freeze — One-Pass Command

## Mission
Continue from verified Commercial Convergence Run 35338325244. Do NOT create sequential V29.6/V29.7/V29.8 strategy versions. The previous A/B/C screen proved an architecture limitation: frequency and engineering are not the primary bottleneck; context-conditioned expectancy is.

This run is a single architecture-redesign program with a hard stop. Commercial KPI values are aspirational targets, never guarantees and never Development fitting constraints.

## Evidence lock
- Repository: rbhnm859/Ouroboros-Cloud-Build
- Frozen engineering baseline: HarmonyBot V29.5 lineage
- Commercial Convergence evidence Run: 35338325244
- A: 72.0 baskets/year, aggregate PF 0.733, net -628.25, expectancy -5.82, worst PF 0.163, DD 6.57%, FAIL
- B: 59.3/year, PF 0.665, net -668.92, expectancy -7.52, worst PF 0.033, DD 5.12%, FAIL
- C: 59.3/year, PF 0.690, net -605.92, expectancy -6.81, worst PF 0.032, DD 4.97%, FAIL
- Primary failure: DEV-B conditional edge collapse.
- Final Holdout remains untouched.

## Permanent engineering freeze
Do not change these to improve strategy metrics:
Risk sizing; min-volume protection; volume normalisation; margin/free-margin protection; protective/server-side SL; grid risk cap; anti-hedge; duplicate-main-entry protection; fail-closed behaviour; execution integrity; broker/API handling; capital protection.

## Architecture diagnosis to implement
The next architecture must separate:
1. Harmonic geometry validity.
2. Regime compatibility.
3. Direction/HTF context.
4. Entry confirmation/timing.
5. Payoff/thesis lifecycle.

Do NOT use hour/date/window lookup tables. Do NOT add a DEV-B-specific rule. Do NOT simply tighten every quality threshold.

### Causal context vector at signal time
Instrument and persist:
- pattern, direction, signal/entry UTC
- ATR now, rolling ATR baseline and ratio
- H4/H1/M15 directional state available at signal time
- trend/range state
- PRZ confluence, geometry quality, composite quality
- distance into PRZ, confirmation state
- spread/cost estimate
- initial risk/SL/TP
No future information may enter admission.

### Lifecycle telemetry
For each basket persist:
- MFE_R, MAE_R
- time-to-MFE / time-to-MAE
- thesis invalidation state
- winner giveback R
- exit reason
- realised R and money P/L
- grid eligibility/add context

## One-pass candidate families
Pre-register all numeric thresholds BEFORE any new Development result is viewed.

R1 — Context Compatibility
Harmonic pattern remains the sole setup generator. Admission requires pattern-specific compatibility across causal volatility + H4/H1/M15 directional/regime context. Use continuous scores / coarse regimes, not time-window memorisation.

R2 — Confirmation Quality
R1 + causal entry confirmation inside/around PRZ to reject patterns that immediately move into MAE. Entry confirmation must not invent a non-harmonic setup; it only confirms an existing valid harmonic pattern.

R3 — Lifecycle Conversion
R2 + thesis/payoff management using only causal post-entry MFE/MAE/thesis state. Its purpose is to reduce winner giveback and cut disproven trades; it must not widen initial risk or violate frozen risk controls.

Maximum 3 architecture candidates. No fourth rescue candidate.

## Development design
Use the same DEV-A/B/C windows only as Development:
DEV-A 2021-01-04..2021-06-30
DEV-B 2021-07-01..2021-12-31
DEV-C 2022-01-03..2022-06-30

Run R1/R2/R3 × all 3 windows once after preregistration.

Mandatory Development gate:
- all 3 windows have trades
- PF > 1 in all 3
- expectancy > 0 in all 3
- aggregate net > 0
- aggregate expectancy > 0
- max DD <= 10%
- execution errors = 0
- robust executable frequency >= 50 baskets/year

Selection frontier:
worst-window PF → worst-window expectancy → aggregate expectancy → DD → frequency → simplicity.
Do not select by headline PF alone.

If none pass: output STRATEGY_ARCHITECTURE_LIMITATION and STOP. Do not create another strategy version.

## Untouched downstream gate chain
Only if Development PASS:
1. One predeclared untouched Validation, once.
2. Real $100 FxPro XAUUSD 1:500 gate with Small Capital Mode ON and tick data where supported.
3. OOS.
4. Walk-forward.
5. Parameter sensitivity ±5%, ±10%, ±20% around selected values.
6. Spread, commission, slippage and combined-cost stress.
7. Basket Monte Carlo.
8. Final Holdout exactly once.

Any failure stops downstream execution. Never retune against Validation/OOS/Holdout.

Use cTrader's supported backtest/CLI facilities. Prefer tick server data for the real $100 commercial gate when practical; M1 may be used for Development screening. Record exact data mode, costs, symbol and account properties.

## Commercial target panel — targets, not guarantees
- PF >= 2.5
- Win rate >= 65%
- realised RR >= 2.0
- annualised ROI >= 100%
- profitable months >= 10/12
- actual executable frequency >= 200/year
- max DD <= 10%

PASS requires mandatory gates plus target panel.
NEAR_TARGET is allowed only when every mandatory robustness/safety gate passes but one or more aspirational targets remain below target. Report exact gaps.
HOLD for downstream mandatory-gate failure.
STRATEGY_ARCHITECTURE_LIMITATION if no Development architecture passes.

## Required engineering outputs
- ARCHITECTURE_PREREGISTRATION.json
- EDGE_ATTRIBUTION_MATRIX.json
- DEV_B_FAILURE_DECOMPOSITION.json
- LIFECYCLE_MFE_MAE_ANALYSIS.json
- DEVELOPMENT_GATE.json
- VALIDATION.json if authorised
- COMMERCIAL100.json if authorised
- OOS.json if authorised
- WALK_FORWARD.json if authorised
- SENSITIVITY.json if authorised
- COST_STRESS.json if authorised
- MONTE_CARLO.json if authorised
- FINAL_HOLDOUT.json only if authorised
- FINAL_COMMERCIAL_DECISION.json/md
- compiled .algo only for PASS or NEAR_TARGET
- SHA256SUMS and exact source commit provenance

## Execution rules
- Work only on branch harmonybot/architecture-redesign-freeze.
- Keep PR draft until the evidence chain finishes.
- Never auto-merge.
- Never fabricate missing telemetry.
- Never claim commercial readiness from in-sample performance.
- Never guarantee profit.
- One coherent architecture pass only.
