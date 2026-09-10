# K4 Price-First Breakout — Precommitted Commercial Research Specification

## Purpose
K3 Flow-First is formally C-FAIL under corrected realistic-cost IS. This K4 branch is a new architecture hypothesis and is not a parameter-tuned continuation of K3.

## Core hypothesis
The prior family used cumulative/tick-direction imbalance as the primary trigger and did not survive realistic costs. K4 inverts the hierarchy: **closed-price breakout is the primary event; delta becomes a secondary confirmation/veto only**. The goal is to test whether larger, price-confirmed impulse events have enough gross edge to survive spread and commission.

## Fixed entry architecture
All entry decisions are based only on completed bars.

For LONG:
1. The just-closed M1 bar closes above the highest high of the previous five completed M1 bars, excluding the signal bar.
2. The signal bar closes in the upper 30% of its own high-low range.
3. The last completed M15 close is above the completed M15 EMA50 and the completed EMA50 slope over three M15 bars is positive.
4. Completed M15 ADX(14) is >=16.
5. Delta is confirmation only: cumulative delta is >0 and at least two of the last three completed M1 delta bars are positive.
6. Existing ATR, session, weekday, spread, cooldown, daily-loss and equity protections pass.

For SHORT the rules are exactly symmetric.

No threshold-cross requirement is used in K4. DeltaThreshold=125 from K/K2/K3 is not used as an entry trigger.

## Fixed risk/exit architecture
- One position maximum per symbol/label.
- No opposite concurrent position.
- Mandatory entry-time SL/TP.
- SL = 0.8 ATR(14) from the just-completed M1 bar.
- TP = 1.2 ATR(14), fixed for the first K4 test; no TP sweep before first IS result.
- Breakeven is not used as an edge generator. Initial K4 research keeps it disabled to avoid clipping the new price-impulse hypothesis; hard account/daily/floating-loss protection remains enabled.
- No trailing stop in the initial candidate.
- No averaging, recovery or re-entry layering.
- Maximum one trade per completed M1 bar.

## Cost handling
- Runtime cost telemetry remains mandatory.
- Spread is evaluated in broker units and commercial validation uses fixed 0.43 pip.
- Commission is 35 USD per million USD volume.
- Economic floor is a safety condition only: expected TP distance / estimated round-trip cost must be >=1.0. It is not an optimizer or ranking score.

## Locked research environment
- Broker environment: cTrader / FxPro-compatible EURUSD naming.
- Symbol: EURUSD.
- Timeframe: M1.
- Initial balance: USD 30.
- Target leverage: 1:500, runtime-verified.
- Historical mode: server ticks.
- IS: 09/09/2024 00:00 UTC through 08/09/2025 23:59 UTC.
- Spread: 0.43 pip.
- Commission: 35 USD per million USD volume.

## First-IS gates
K4 may be frozen only if ALL are true:
- ROI >0.
- PF >=1.15.
- Trades >=50.
- Max equity DD <=15%.
- Largest loss >=-$1.00.
- Post-cost average trade >0.

If the first exact K4 IS candidate materially fails these conditions, do not search breakout lookback, close-location percentile, ADX, delta vote count, session, weekday set, TP, SL or direction-specific thresholds on the same IS window.

## Promotion sequence
Only after K4 passes first IS and is frozen:
1. OOS 09/09/2025 00:00 through 09/09/2026 23:59 UTC.
2. OOS gates: ROI>0, PF>=1.20, trades>=50, DD<=15%, largest loss>=-$1, expectancy>0.
3. FULL: ROI>=10%, PF>=1.20, trades>=100, DD<=15%, net>0, expectancy>0.
4. Stress 1.25x and 1.5x costs; at 1.5x require PF>=1.0, net>=0, DD<=20%.
5. Robustness only after promotion candidate exists.
6. Monte Carlo only after robustness survives.

## Anti-overfit rule
- One exact architecture is tested first.
- No brute force.
- No OOS retuning.
- No hidden direction-specific optimization.
- No parameter neighborhood search unless the fixed candidate first establishes a positive, credible edge.

## Prohibited strategy elements
Grid, Martingale, DCA, Recovery, Loss Averaging, averaging down, reverse recovery and Hedging are prohibited.

## Status semantics
Until every promotion gate is passed, no K4 artifact may be labeled Commercial, Store, Production or Release. Any built `.algo` before that point is Research Only.
