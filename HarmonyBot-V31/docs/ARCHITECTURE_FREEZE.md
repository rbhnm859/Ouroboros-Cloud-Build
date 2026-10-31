# HarmonyBot V31.0 — Clean-Room Multi-Timeframe Harmonic Execution Kernel

## Source policy
V31 is a standalone source tree. Its final source is `HarmonyBot-V31/src/HarmonyBotV31.cs` and is not reconstructed from V26–V30 patch scripts.

## Timeframes
- H4: macro regime + active harmonic context.
- H1: intermediate regime + active harmonic context.
- M15: the only primary harmonic setup generator.
- M1: PRZ retest and two-stage execution confirmation only.
- Every analytical read uses a completed bar.

## Trading pipeline
M15 harmonic candidate → VALIDATED → MTF conflict → harmonic route → WAIT_PRZ → M1 CONFIRMING → ARMED → scheduler → EXECUTED.

Terminal states are EXPIRED / REJECTED / INVALIDATED. Every transition emits a CandidateId event; silent candidate loss is forbidden.

## Harmonic families
Gartley, Bat, Alt Bat, Butterfly, Crab, Deep Crab, Cypher, Shark, 5-0, AB=CD, Deep Gartley, Rat.

Each family has its own ratio profile, PRZ width, structural invalidation buffer, canonical targets, TTL and minimum quality.

## Routes
- TREND_ALIGNED_REVERSAL
- EXHAUSTION_REVERSAL
- TRANSITION_REVERSAL
- NO_TRADE

Generic continuation routing is removed.

## Execution and risk
No Grid, Martingale, DCA, Recovery or Loss Averaging.
One main position maximum. No hedge and no duplicate main entry.
Development risk is 1.0%.
Native server-side SL/TP are placed with the order.
No target is moved farther away merely to manufacture RR. A trade is rejected unless a canonical target clears net RR >= 2.0 after modeled costs.

## Session
DST-aware Europe/London 08:00 local through America/New_York 17:00 local. No historical hour blacklist.

## Lifecycle
- no-MFE thesis failure only after age >=3m, peak <0.15R and adverse >=0.80R;
- no breakeven before 1.0R peak;
- at >=1.0R, may lock +0.10R;
- trailing only after >=1.5R peak, 0.75R distance;
- stop can never be widened.

## Validation discipline
DEV-A/B/C are exposed development windows and may not be used for iterative threshold rescue.
A V31 Development failure ends the architecture attempt.
Downstream periods may only be called untouched when DATA_EXPOSURE_LEDGER proves that status.
Commercial targets are aspirational, not profit guarantees or fitting constraints.
