# HarmonyBot V65 — Harmonic Alpha Regime Truth Engine

V65 is a single-major-version Alpha Engine rebuild over the fixed V64 execution/risk kernel.

## Root cause
V64 proved execution can preserve right-tail and improve DEV economics, while 2023 and 2025H2 remained structurally negative. V65 therefore changes Alpha qualification only; it does not redesign Grid, Runner, sizing, exits, or risk.

## New Alpha Truth contract
Every routed harmonic setup receives a pre-entry score using only completed-bar information available at that moment:
- harmonic geometry quality
- PRZ confluence
- time symmetry and pivot quality
- H4/H1 conflict/context
- M15 ATR percentile and ATR shock ratio
- H1/H4 ADX level
- H1 ADX slope
- M15 efficiency
- H1 extension from EMA50
- route-specific context fit

Regimes are descriptive only: SHOCK, TRANSITION, DIRECTIONAL, CHOP, BALANCED.
No year/date identifier, future outcome, MFE/MAE, or post-entry information may enter the decision.

## Hard vetoes
- simultaneous extreme ATR percentile + ATR shock
- accelerating high-volatility trend-aligned entry
- exhaustion entry while ADX is still strengthening
- unstable transition with extreme ADX slope

## Governance
V64 Product remains the immutable execution/risk control.
V65 must improve the bad regimes without destroying positive regimes.
No parameter search. One preregistered configuration only.
No V65.x chain.
Fresh remains untouched until DEV + validation + small-capital gates pass.
