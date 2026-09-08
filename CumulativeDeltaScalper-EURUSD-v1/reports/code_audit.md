# Code Audit — Upstream `CumulativeDeltaScalper.cs`

## Scope

- Source reviewed: `original/CumulativeDeltaScalper.cs`
- Audit basis: static code review against the requested EURUSD cTrader delivery constraints.

## High-priority findings

1. **No chart timeframe restriction**  
   The upstream bot can be attached to unsupported chart periods. The requested package must hard-stop unless the chart timeframe is M1, M5, M15, or M30.

2. **No EURUSD-only guard**  
   The upstream bot trades whichever symbol it is attached to. The requested build is specifically an EURUSD scalper and must reject other symbols.

3. **Single-position protection is incomplete**  
   `HasOpenPosition()` only checks positions matching the bot label and symbol. That allows the account to carry another EURUSD position under a different label or manual entry, which violates the requested "最多同時一倉" and anti-hedging constraints.

4. **Missing fixed-money-risk sizing**  
   The upstream implementation supports percent-risk or fixed lots, but it does not expose a fixed-money-risk model.

5. **Broker min/max/step handling is incomplete**  
   The upstream sizing normalizes volume but does not explicitly reject broker-minimum oversizing scenarios caused by a too-small risk budget.

6. **Daily risk controls are incomplete**  
   The upstream file has max daily loss percent, but it does not include max daily loss money, daily profit target money, or max consecutive losses.

7. **Cooldown model does not cover the requested rule set**  
   The upstream code includes separate minimum-seconds-between-trades and loss cooldown concepts, but not a single explicit user-facing cooldown control for the hardened package.

8. **No debug logging toggle**  
   The upstream bot always prints operational messages. A configurable debug switch was requested.

9. **No explicit anti-grid / anti-martingale / anti-DCA / anti-recovery declarations in control flow**  
   The upstream logic does not intentionally average down, but the hardened delivery still needs explicit one-position-only entry guards so those behaviors remain structurally impossible.

## Compile-portability concerns reviewed during the audit

- The upstream file relies on multiple cTrader API calls (`MarketData.GetBars`, `DirectionalMovementSystem`, position event hooks, and SL/TP overloads) that are valid only if the project file and package references are set correctly.
- The hardened package therefore includes its own `.csproj`, explicit startup validation, and post-entry SL/TP verification.

## Audit outcome

The upstream strategy logic was usable as a starting point, but it did **not** satisfy the requested deployment and risk constraints as-is. The independent EURUSD v1 build in `src/` applies the required symbol, timeframe, sizing, volume, and daily-risk hardening.
