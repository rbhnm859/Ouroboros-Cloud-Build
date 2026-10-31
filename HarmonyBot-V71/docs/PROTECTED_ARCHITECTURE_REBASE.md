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

## Physical module map

- `HarmonyBotV71.cs`: configuration/state composition root plus the immutable frozen harmonic detector region.
- `Architecture/HarmonyBotV71.ProtectedCore.cs`: V51 runtime lifecycle, candidate ownership, grid planning/execution orchestration and core-first capital scheduling.
- `Architecture/HarmonyBotV71.Resolution.cs`: V71/V72 challenger/shadow event-resolution logic.
- `Architecture/HarmonyBotV71.Context.cs`: MTF/regime routing and family-native confirmation/context support.
- `Architecture/HarmonyBotV71.Safety.cs`: risk/session/safety controls.
- `Architecture/HarmonyBotV71.TelemetryMath.cs`: candidate state, telemetry and numerical helpers.
- `Architecture/HarmonyBotV71.Domain.cs`: shared domain/state contracts.

The refactor is accepted only through exact replay; file boundaries are not permission boundaries and do not relax any fail-closed gate.
