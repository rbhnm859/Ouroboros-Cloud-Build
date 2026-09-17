# HarmonyBot V29 — Persistent PRZ Execution RC

## Why V29 exists

V28.4 fixed the Small Account SL-floor precedence and added capital-aware PRZ gating, but the D7 and D7_LONG_WARMUP runs produced the same result: 221 detected signals, 45 geometry-valid setups, 38 precision waits, 6 capital hard rejects, 0 precision-ready setups and 0 orders. The warmup length changed substantially while the evaluation result did not, so the main bottleneck is the one-shot precision-entry design rather than missing historical warmup.

## V29 architecture

V29 changes the execution model from `detect -> check now -> discard` to a persistent candidate state machine:

`Pattern -> Geometry -> Pending Candidate -> PRZ Recheck -> Capital Recheck -> MTF/Risk/Anti-Hedge -> Order -> Outcome`

### 1. Persistent PRZ candidate queue

A geometry-approved harmonic setup that is not yet executable is retained instead of being discarded. Each candidate stores the original harmonic structural stop, target, reference price, quality metrics, completion index, creation bar, ATR context, composite quality and order-attempt state.

Lifecycle states are represented by diagnostics: created, rechecked, triggered, executed, expired, invalidated and superseded.

### 2. Structural-stop preservation

V29 does not move the harmonic invalidation point simply to fit a USD 100 account. The structural SL remains the setup's invalidation level. Entry becomes executable only when market price reaches a location where the original structural SL fits the all-in risk budget at broker minimum volume.

### 3. Capital-aware re-evaluation

Every pending candidate is re-evaluated using current equity, dynamic risk budget, broker minimum volume and estimated execution reserve. The candidate can move from infeasible to feasible without changing RiskPercent or MaxDrawdown.

### 4. Quality-adaptive PRZ execution

V28.4 used one fixed PRZ distance threshold. V29 keeps the base threshold but permits a controlled additional PRZ band only for stronger geometry. The adaptive band is capped and does not reduce the Geometry Quality, PRZ Confluence, Time Symmetry or Pivot Quality gates.

Composite execution quality weights:

- Geometry quality: 40%
- PRZ confluence: 20%
- Pivot quality: 15%
- Time symmetry: 10%
- Pattern confidence: 15%

The execution layer therefore becomes less binary without weakening the pattern validator.

### 5. Queue fairness and deduplication

The queue has both a global cap and per-pattern cap. When full, a new setup must exceed the weakest candidate by a replacement margin before it may supersede it. This prevents one pattern family from filling the entire queue while preserving higher-quality opportunities.

### 6. Deterministic warmup behavior

V29 no longer treats the evaluation-start gate as a full strategy early-return. Historical bars can build detector and pending-candidate state while order execution remains disabled. Pending candidates are bounded by bar age, so sufficiently long warmups should converge to the same evaluation state.

### 7. Revalidation at execution

A pending candidate is not executed merely because it was once valid. Before an order it still passes the existing dedupe, daily pattern budget, MTF filter, anti-hedge rule, same-direction cap, order-geometry check, commercial risk geometry, volume normalization, notional/margin checks and broker execution layer.

Candidates are invalidated if the structural stop or original target has already been crossed, expired after the configured age, or removed after repeated execution failures.

### 8. Risk contract retained

V29 keeps the commercial safety contract:

- Base test RiskPercent: 1.0%
- MaxDrawdown: 10%
- Small Account effective minimum SL: 25 pips
- Minimum RR: 2.0
- No Martingale / DCA / Recovery / Loss Averaging
- Anti-Hedge retained
- Broker minimum-volume and normalized-volume risk validation retained
- Fibonacci Grid retained and still subject to the commercial risk budget
- All 12 harmonic families retained

## New V29 diagnostics

The V29 summary includes:

- pendingCreated
- pendingRechecked
- pendingTriggered
- pendingExecuted
- pendingExpired
- pendingInvalidated
- pendingSuperseded
- pendingOrderFailed
- pendingMtfBlocked
- pendingOpen
- warmupDetected
- warmupSeeded
- effectiveMinSL

Per-pattern pending lifecycle lines are emitted as `[V29-PATTERN-PENDING]`.

## Validation sequence

1. D7: verify compile, queue activity, candidate conversions and no risk regression.
2. D7_LONG_WARMUP: compare the same evaluation window with a longer warmup. Candidate/trade behavior should materially converge.
3. M1 only if D7 shows actual candidate-to-order conversion without unacceptable drawdown.
4. After a viable M1, continue to M6 and 1Y with commission/spread/slippage stress, parameter plateau checks and OOS validation.

V29 must not be called SEALED until the historical commercial gates are actually met by backtest evidence.
