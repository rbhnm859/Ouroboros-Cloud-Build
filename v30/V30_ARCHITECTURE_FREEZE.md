# HarmonyBot V30.0 — Regime-Routed Harmonic Portfolio Engine

## Authority standard
Treat this as a major architecture replacement, not a V29.x patch.

## Evidence that forces V30
Run 35342318165 proved:
- R1: PF 0.703, expectancy -6.59, worst-window PF 0.150.
- R2: PF 0.719, expectancy -6.57, worst-window PF 0.196.
- R3: PF 0.762, expectancy -5.33, worst-window PF 0.216.
- DEV-B remains the dominant failure.
- R2 confirmation improves DEV-A but not DEV-B.
- R3 lifecycle reduces DD/loss but still does not create positive expectancy.
- Context score was weakly discriminative: R1 blocked only 3 signals across all Development windows.
- Current runner is Sell-only (V294AllowBuy=false).
- The detector contains 12 harmonic families but actual Development executions collapse to Cypher and 5-0.
- With Fibonacci Grid enabled, primary positions are wrapped as GridBasket even when no Grid add occurs; Grid BE/trail/scale-out can therefore manage the primary before any recovery level exists.

## New product/version
Version: HarmonyBot V30.0
Codename: Regime-Routed Harmonic Portfolio Engine
Commercial stage: Major Architecture RC

## V30 non-negotiable architecture
1. Harmonic/Fibonacci remains the sole setup generator.
2. Enable both Buy and Sell; no global one-sided direction lock.
3. Replace single-best downstream loss with a portfolio detector path: collect multiple valid harmonic candidates and let the causal router select the best executable candidate.
4. Disable in-run AutoDisableLosing during validation. Pattern families must not disappear because of path-dependent sample WR.
5. Replace legacy hard MTF gate with a V30 regime router when V30 is active.
6. Route valid harmonic setups into CONTINUATION / REVERSAL / TRANSITION using only signal-time data.
7. Require two-stage closed-bar confirmation before a setup is executable.
8. Disable Fibonacci Grid for V30 commercial candidate. Keep Grid code/risk-cap intact but inactive because prior Development executed zero adds while primary GridBasket management compressed payoff.
9. Preserve the real harmonic server TP and MinRR >= 2.0.
10. Replace legacy primary BE/partial/trailing with R-based V30 lifecycle:
   - no partial TP;
   - no breakeven before 1.0R peak;
   - at >=1.0R peak, protect +0.10R;
   - trail only after >=1.50R peak with 0.75R distance;
   - no-MFE thesis kill only after 3 minutes, peak MFE <0.15R and current <= -0.80R.
11. Never widen original SL, increase risk, hedge, duplicate entries, or bypass broker protections.

## V30 fixed router thresholds
These are frozen before V30 Development:
- ATR baseline = 240 bars
- valid ATR ratio band = 0.55 .. 1.70
- continuation: >=1 HTF alignment + M15 directional score >=0.55 + confirmation >=0.55
- reversal: >=1 HTF opposition + M15 directional score >=0.62 + geometry >=0.58 + PRZ >=0.58 + confirmation >=0.65
- transition: H1/H4 disagreement + M15 >=0.60 + confirmation >=0.65
- final rank = Confidence 0.30 + Geometry 0.25 + PRZ 0.15 + Confirmation 0.15 + RouteQuality 0.15
- portfolio max candidates per bar = 8

No date/hour lookup. No DEV-B-specific rule.

## V30 Development
Single candidate only:
V30 × DEV-A
V30 × DEV-B
V30 × DEV-C

Hard Development Gate:
- all three windows trade
- PF > 1 each
- expectancy > 0 each
- net > 0 each
- aggregate PF > 1
- aggregate expectancy/net > 0
- DD <= 10%
- execution errors = 0
- annualized frequency >= 50

If FAIL: V30 = HOLD / ARCHITECTURE LIMITATION. Do not tune against the same windows.

If PASS: continue automatically through one untouched Validation -> real $100 FxPro XAUUSD 1:500 tick gate -> OOS -> walk-forward -> ±5/10/20 sensitivity -> cost stress -> 5000-path Monte Carlo -> Final Holdout once.

## Commercial targets (not guarantees)
PF >= 2.5
Win rate >= 65%
Realized RR >= 2.0
Annualized ROI >= 100%
Profitable months >= 10/12
Actual executable frequency >= 200/year
Max DD <= 10%

Mandatory gates all PASS + targets all met => PASS.
Mandatory gates all PASS but target gaps remain => NEAR_TARGET.
Any mandatory downstream failure => HOLD.
