# HarmonyBot V71 Protected Architecture Rebase

Status: **behavior-preserving V71 refactor; not V72**.

## Hard boundaries

1. **Frozen Harmonic Detector**
   - Canonical 12-family identities and Fibonacci/PRZ contracts remain in the guarded region of `HarmonyBotV71.cs`.
   - `verify_frozen_harmonic_engine.py` SHA/length guard must remain exact.

2. **Protected V51 Core**
   - V51 remains first capital-slot priority.
   - MaxActiveBasket=1, no hedging, no Martingale/DCA/recovery, no stop widening.
   - Risk/execution behavior is unchanged by this refactor.

3. **Research Resolution Engine**
   - V71/V72 shadow/challenger resolution code is isolated in `Architecture/HarmonyBotV71.Resolution.cs`.
   - It may observe family/event outcomes but cannot supersede protected-core ownership unless formal gates later authorize a promoted version.

4. **Domain Contracts**
   - Shared enums/records/state containers live in `Architecture/HarmonyBotV71.Domain.cs`.
   - These are data contracts, not alpha.

## Fail-closed acceptance

Every structural extraction is accepted only if:
- both V71 and trusted V51 compile;
- frozen harmonic-engine guard is unchanged;
- V51 2021/2022/2023 data snapshot, canonical report and core-pipeline fingerprints are exact;
- risk/execution violations stay zero;
- Validation and Fresh remain unused.

A green workflow alone is not a strategy pass.
