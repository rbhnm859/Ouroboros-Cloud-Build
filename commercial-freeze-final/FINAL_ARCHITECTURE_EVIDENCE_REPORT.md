# HarmonyBot Final Commercial Freeze — Evidence Report

## Execution
- Final one-pass workflow run: 35340796310
- Workflow conclusion: SUCCESS
- Branch: harmonybot/final-commercial-freeze-redesign
- Workflow head SHA: e7bd54e173aab12619cbd372f6c1a1e92134c86f
- Artifact: HARMONYBOT-FINAL-COMMERCIAL-FREEZE (10544698783)
- Final strategy status: STRATEGY_ARCHITECTURE_LIMITATION
- Final Holdout: UNTOUCHED
- Validation / $100 / OOS / walk-forward / robustness: BLOCKED because Development did not pass.

## What the redesign changed
The engineering, risk, broker, anti-hedge, duplicate-entry and server-side protection core remained frozen.

The strategy edge layer was redesigned in one pass:
- restored both BUY and SELL directions;
- added completed-bar H4/H1/M15 context arbitration;
- added universal closed-bar confirmation;
- removed the prior volatility-only admission dependency as the primary solution;
- disabled Fibonacci Grid for the final candidate;
- bypassed partial TP / early BE / trailing so Development measured the structural >=2R payoff;
- preregistered only P1/P2/P3 before execution.

## Development evidence

### P1 — Balanced HTF/M15
- DEV-A: 39 baskets, PF 0.7994, Net -368.50, Expectancy -9.4487, WR 35.90%, realized RR 1.4275, DD 6.59%
- DEV-B: 31 baskets, PF 0.5828, Net -605.33, Expectancy -19.5268, WR 25.81%, realized RR 1.6757, DD 8.20%
- DEV-C: 39 baskets, PF 0.4013, Net -887.83, Expectancy -22.7649, WR 20.51%, realized RR 1.5551, DD 9.74%
- Result: FAIL

### P2 — 2-of-3 Consensus
- DEV-A: 51 baskets, PF 0.7561, Net -572.43, Expectancy -11.2241, WR 27.45%, realized RR 1.9982, DD 9.78%
- DEV-B: 37 baskets, PF 0.6273, Net -608.95, Expectancy -16.4581, WR 27.03%, realized RR 1.6938, DD 8.24%
- DEV-C: 46 baskets, PF 0.5473, Net -944.66, Expectancy -20.5361, WR 21.74%, realized RR 1.9704, DD 9.75%
- Result: FAIL

### P3 — Strict 3-of-3
- DEV-A: 19 baskets, PF 0.8358, Net -186.22, Expectancy -9.8011, WR 31.58%, realized RR 1.8108, DD 4.78%
- DEV-B: 7 baskets, PF 2.2393, Net +408.44, Expectancy +58.3486, WR 57.14%, realized RR 1.6795, DD 1.84%
- DEV-C: 27 baskets, PF 0.5335, Net -604.01, Expectancy -22.3707, WR 25.93%, realized RR 1.5243, DD 7.83%
- Result: FAIL (cross-window instability and frequency collapse)

## Architecture diagnosis
1. Execution engineering is not the primary bottleneck: execution errors remained zero.
2. Frequency is not the primary bottleneck: looser profiles produced adequate gross frequency but negative expectancy.
3. Payoff clipping was a real secondary problem: after removing early Grid/partial/BE/trailing management, realized RR improved materially, reaching ~2R in P2, but PF remained <1 because entry win rate/context quality remained insufficient.
4. Static H4/H1/M15 EMA consensus is not the missing regime variable. It filtered heavily but did not create stable positive expectancy.
5. Restoring BUY did not solve the issue. Direction profitability flips by window; a global direction switch is structurally fragile.
6. Effective live strategy diversity is much narrower than the nominal 12-pattern detector. Executed baskets are dominated by Cypher and 5-0.
7. The next legitimate research question is detector-level and pattern-specific: canonical pattern conformance, PRZ semantics, pivot selection, pattern-specific invalidation, and pattern-specific regime/context. It must not be another post-hoc threshold patch on the same Development windows.

## Commercial decision
Commercial freeze cannot honestly be marked PASS or NEAR_TARGET from this run.

Formal status:
STRATEGY_ARCHITECTURE_LIMITATION

Per preregistered stop rule:
- no P4 was created after observing P1/P2/P3;
- no Validation was consumed;
- no $100 commercial gate was consumed;
- no OOS was consumed;
- no Final Holdout was consumed;
- no final commercial .algo was emitted.

This preserves the untouched evidence required for a future detector-level redesign.
