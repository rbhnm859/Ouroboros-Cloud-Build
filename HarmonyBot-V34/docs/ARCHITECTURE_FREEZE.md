# HarmonyBot V34.0 — Clean Execution & Adaptive Capital Architecture

V33 remains frozen as contaminated performance evidence because post-fill positions could survive beyond structural invalidation.

## Frozen strategy core
- H4/H1/M15/M1 causal architecture
- M15 harmonic detection + M1 confirmation
- harmonic ratios and pattern families
- Fibonacci levels 0 / .236 / .382 / .618
- normal-capital risk weights 3/7 / 2/7 / 1/7 / 1/7
- BasketRiskPercent <= 1.0%
- route thresholds, canonical targets, MinimumNetRR
- exposed DEV-A/B/C dates; they are engineering-regression data only

## V34 clean-execution scope
1. Post-fill structural safety kernel on Positions.Opened and PendingOrders.Filled.
2. Gap-through structural invalidation is fail-closed; no position may survive on the invalid side.
3. Actual-fill basket risk is recalculated from real entry prices.
4. Position protection must be confirmed after fill; protection failure is fail-closed.
5. Stop and take-profit repairs are separated to avoid combined-protection invalid requests.
6. Deeper pending exposure is causally revalidated before fill.
7. Execution leg state machine audits illegal lifecycle transitions.

## Adaptive-capital scope
- Minimum supported equity target: USD 100.
- Micro mode is a physical-exposure mapper, not a different signal strategy.
- All legal Fibonacci levels stay in the logical/virtual grid ledger.
- The largest safe physical prefix is selected using broker minimum volume, risk budget and estimated margin.
- In Micro mode only, active physical-leg weights are renormalized proportionally from 3:2:1:1 without exceeding the 1% basket budget.
- Remaining logical levels remain virtual and are tracked.
- If even L0 cannot be executed within risk/margin constraints, the trade is skipped. Risk is never inflated.

## Evidence policy
DEV-A/B/C are used only for engineering regression. PF, Net, expectancy and DD from these exposed windows are informational and MUST NOT be used for tuning or commercial claims.

Engineering clean gate requires:
- gapThroughSurvivors = 0
- unprotectedSurvivors = 0
- postFillProtectionFailures = 0
- actualBasketRiskViolations = 0
- executionStateViolations = 0
- executionErrors = 0
- gridRiskViolations = 0
- duplicateGridLegs = 0
- orphanPendingOrders = 0
- stopWideningViolations = 0
- marginRiskViolations = 0

A separate USD100 FxPro XAUUSD 1:500 engineering track must demonstrate at least one Micro-mode basket plus the same safety invariants.

Fresh performance validation remains locked until a previously unused interval is explicitly proven and reserved before execution.
