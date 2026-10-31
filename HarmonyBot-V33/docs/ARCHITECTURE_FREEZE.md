# HarmonyBot V33.0 — Fibonacci Harmonic Basket Risk & Lifecycle Architecture

V32 is frozen as evidence. V33 is a major architecture replacement limited to basket risk, lifecycle and broker execution.

## Frozen strategy core
- H4/H1/M15/M1 architecture
- M15 primary harmonic detection; M1 confirmation
- Pattern geometry and enabled pattern families
- Fibonacci staged-entry fractions: 0 / .236 / .382 / .618
- Grid risk weights: 3/7 / 2/7 / 1/7 / 1/7
- BasketRiskPercent development cap: 1.0%
- Canonical targets and structural invalidation
- MinimumNetRR and route thresholds
- DEV-A/B/C windows and their exposed status

## V33 replacement scope
1. Monotonic Basket Protection Frontier. A widening stop proposal is never generated.
2. Broker-safe stop projection before ModifyPosition.
3. Live filled-risk + outstanding-pending-risk reconciliation before every deeper pending leg.
4. Deeper-leg causal thesis eligibility using only current completed-bar state; no historical PF/hour/date lookup.
5. Explicit execution-error attribution remains mandatory.

## Prohibited
No V32 threshold rescue, no Fibonacci spacing optimization, no pattern blacklist from DEV, no risk inflation, no Martingale/DCA/recovery grid, no historical losing-hour filter.

## Evaluation
Engineering audit first. Then the same exposed DEV-A/B/C may be used only as architecture verification. Results must not feed back into thresholds. Fresh downstream Validation/OOS/Holdout remains locked until a genuinely pre-reserved range is proven.
