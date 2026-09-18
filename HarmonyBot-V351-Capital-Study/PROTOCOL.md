# HarmonyBot V35.1 Capital Compatibility Study — Locked Protocol

Status: EXPOSED DEVELOPMENT / ENGINEERING EVIDENCE ONLY. This study is not Fresh OOS, Final Holdout, or commercial validation.

## Frozen candidate

- Source candidate: `EXHAUSTION_VETO_ONLY` from HarmonyBot V35.1.
- V34 route must pass first.
- `EnableTransitionStateVeto=false`.
- `EnableExhaustionEvidenceVeto=true`.
- `EnableRouteSpecificM1Veto=false`.
- Legacy harmonic / Fibonacci entry logic is unchanged.
- Capital feasibility is studied independently with `EnableCapitalFeasibilityGate=true`.
- No Alpha parameter, Fibonacci ratio, structural stop, risk percent, grid weight, session rule, or validation gate may be tuned from these results.

## Broker / execution lock

- FxPro demo USD account, leverage 1:500.
- Symbol: XAUUSD.
- Bot timezone: UTC.
- Basket Risk: 1.0% maximum.
- Adaptive Capital Mode: enabled.
- Minimum Supported Equity: $100.
- Micro Capital Threshold: $500.
- Fibonacci logical grid and V34 execution/risk kernel remain frozen.
- No forced minimum volume, no stop compression, no risk increase, no recovery behavior.

## Tested starting equity

Exactly: `$100`, `$150`, `$200`, `$300`, `$500`, `$1000`.

Each equity is run separately. Metrics are never pooled across different equity levels.

## Development windows

Only already-exposed DEV data are used:

- A: 2021-01-04 through 2021-06-30; evaluation starts 2021-01-11T00:00:00Z.
- B: 2021-07-01 through 2021-12-31; evaluation starts 2021-07-08T00:00:00Z.
- C: 2022-01-03 through 2022-06-30; evaluation starts 2022-01-10T00:00:00Z.

No 2020-H1/H2, 2022-H2, or 2023 Final Holdout data are used.

## Metric definitions locked before results

- `total_harmonic_candidates`: final `[V351-SUMMARY] candidates` count.
- `capital_feasible_candidates`: count of `[V351-ALPHA-CANDIDATE]` records when capital feasibility gate is enabled; these are candidates that passed the frozen route and the capital precheck.
- `capital_infeasible_candidates`: final `[V351-ALPHA-SUMMARY] capitalInfeasible` count.
- `alpha_eligible_candidates`: `capital_feasible_candidates + capital_infeasible_candidates`; this is the pre-capital-gate route-eligible population.
- `completed_baskets`: count of `[V351-BASKET-CLOSED]` records.
- `executable_basket_ratio`: `completed_baskets / capital_feasible_candidates`, reported only when the denominator is non-zero.
- `physical_grid_depth`: `physicalDepth` from `[V351-GRID-PLAN]`; report distribution, mean, median, min, max.
- `virtual_grid_depth`: `logicalLegs - physicalDepth` from `[V351-GRID-PLAN]`; report distribution, mean, median, min, max.
- `minimum_l0_risk`: minimum feasible `minL0Risk` from `[V351-ALPHA-CANDIDATE]`. If there are no feasible candidates, report null, not zero.
- `capitalRejectedBaskets`: final V35.1 summary counter.
- `margin_rejection`: report scheduler `MARGIN_HEADROOM` rejections and post-fill `marginRiskViolations` separately and combined.
- `realized_risk`: report closed-basket `initialRisk` / `worstRisk` and post-fill `actualWorst / budget` utilization; do not infer missing risk values.
- PF / Net / Expectancy / Max DD are development engineering evidence only.

## Equity conclusions locked before results

`Minimum Technical Equity` = the lowest tested equity satisfying all of:

1. at least one capital-feasible candidate;
2. at least one completed basket;
3. engineering-clean across all A/B/C windows;
4. zero grid-risk, actual-fill-risk, execution-state, unprotected-survivor, stop-widening, and margin-risk violations.

`Recommended Operating Equity` = the lowest tested equity satisfying all of:

1. the Minimum Technical Equity safety requirements;
2. capital-feasible candidates >= 80% of the $1000 benchmark count;
3. completed baskets >= 80% of the $1000 benchmark count;
4. mean physical grid depth >= 80% of the $1000 benchmark mean physical depth;
5. no scheduler margin-headroom rejection;
6. maximum observed post-fill actual-risk utilization <= 100% of the basket budget.

These thresholds are engineering operating criteria, not profit guarantees. PF/Net are deliberately excluded from the equity-selection rules to avoid choosing capital based on favorable PnL.
