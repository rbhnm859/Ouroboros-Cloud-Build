# HarmonyBot V33.0 — Fibonacci Harmonic Basket Risk & Execution Architecture

## Purpose
V33 is a Major Architecture Generation built from the frozen V32 strategy core. V32 remains frozen. No V32.1/V32.2 rescue is permitted.

## Frozen strategy core
The following V32 components are intentionally preserved:
- H4/H1/M15/M1 independent Bars architecture
- completed-bar indexing and no-lookahead policy
- M15 primary harmonic detection
- M1 confirmation architecture
- H4/H1 harmonic conflict context
- Gartley, Bat, Alt Bat, Butterfly, Crab, Deep Crab, Cypher, Shark, 5-0, AB=CD, Deep Gartley and Rat profiles
- Fibonacci grid geometry 0 / 0.236 / 0.382 / 0.618
- risk weights 3/7 / 2/7 / 1/7 / 1/7
- BasketRiskPercent = 1.0% hard maximum
- pattern-specific structural invalidation
- canonical target / minimum Net RR logic
- DST institutional session engine

No historical DEV PF, losing-hour lookup, pattern blacklist or threshold rescue may be used.

## V33 replacement scope
V33 replaces only:
1. Basket Risk Engine
2. Deeper-Leg Exposure Admission
3. Protection Lifecycle
4. Pending/Position Execution State Machine

## Sequential Fibonacci exposure admission
- L0 executes only after the original M1 confirmation.
- L1/L2/L3 prices and risk weights remain pre-registered before L0.
- Only one deeper pending order may exist at a time.
- L2 cannot be admitted unless L1 actually filled.
- L3 cannot be admitted unless L1 and L2 actually filled.
- A missed/rejected earlier Fibonacci leg cannot be bypassed.
- Each deeper leg requires a fresh completed-M1 confirmation at the same route threshold used by the original entry.
- Hard MTF conflict, structural invalidation, session/risk locks or MFE >= 0.50R block further exposure.
- A deeper leg is never market-chased if price already crossed its pre-registered limit.

## Dynamic basket risk
Before every deeper-leg submission:
CurrentFilledRiskToFrontier + CandidateLegRisk + modeled cost <= Original Basket Risk Budget.

Risk released by a protected stop may reduce current downside risk, but unused risk is never reallocated to increase a leg above its original 3/7, 2/7, 1/7, 1/7 budget.

## Monotonic Protection Frontier
Each basket has exactly one ProtectionFrontier.
- Buy: S(t+1) >= S(t)
- Sell: S(t+1) <= S(t)
- Structural stop is the initial frontier.
- Break-even and Fibonacci structure trailing may only advance that frontier.
- The lifecycle does not intentionally generate adverse/widening stop proposals.
- Existing stronger server-side stops are never weakened.

## Execution state machine
Deeper legs use:
ADMISSION_WAIT -> SUBMIT_REQUESTED -> PENDING_ACCEPTED -> FILLED -> CLOSED
with RETRY_WAIT / CANCEL_REQUESTED / CANCELLED / REJECTED terminal/side states.

Only ErrorCode.TechnicalError receives one bounded retry on a later completed M1 bar. Other failed trade requests are recorded in the execution-error ledger.

## Evidence policy
DEV-A/B/C remain EXPOSED_ARCHITECTURE_VERIFICATION only.
V33 receives exactly one formal architecture-verification pass after engineering audits.
No post-result adjustment of Fibonacci levels, pattern availability, route thresholds or development gates is authorised.

Mandatory Development gate remains:
- 3/3 windows trade
- 3/3 PF > 1
- 3/3 expectancy > 0
- 3/3 net > 0
- aggregate PF / expectancy / net > 0
- Max DD <= 10%
- execution errors = 0
- annualized basket frequency >= 50/year
- risk violations = 0
- duplicate legs = 0
- orphan pending orders = 0
- stop-widening violations = 0

Only a full mandatory pass may unlock downstream governance checks. Commercial targets remain targets, never guarantees.
