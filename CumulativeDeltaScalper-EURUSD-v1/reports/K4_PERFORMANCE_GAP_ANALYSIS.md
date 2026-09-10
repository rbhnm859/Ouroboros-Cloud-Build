# K4 Price-First Breakout — Commercial Performance Gap Analysis

## Scope

This analysis is performed **after** the single pre-committed corrected IS test and is diagnostic only. It must not be used to retune K4 on the same IS window or any OOS window.

## Evidence

- Branch: `cds-k4-price-first-breakout-research`
- Tested commit: `6b71671afc4a6a1d5e601a01c9c9dcd7a5ff7cab`
- Corrected IS run: `34485464338`
- Artifact: `CDScalper_K4_PRICE_FIRST_CORRECTED_IS`
- Artifact ID: `10155864421`
- Artifact digest: `sha256:ade28bdefd818394ae649e666cfa29bd385305bed8f1e86e38faf1912cb9dfce`

## Locked validation contract

- EURUSD M1
- Initial balance: USD 30
- Leverage: 1:500
- Historical mode: server ticks
- IS: 09/09/2024 through 08/09/2025 UTC
- Spread: 0.43 pip
- Commission: 35 USD per million USD volume
- One position maximum
- Mandatory entry-time SL/TP
- No hedging / grid / martingale / DCA / recovery / loss averaging
- Hard daily, floating-loss and equity protection enabled

## Observed K4 IS result

| Metric | Result | IS gate | Gap |
|---|---:|---:|---:|
| ROI | -10.47% | >0 | FAIL by 10.47 percentage points to break-even |
| Net profit | -$3.14 | >0 | FAIL |
| Profit Factor | 0.51 | >=1.15 | -0.64 |
| Trades | 32 | >=50 | -18 trades |
| Win rate | 40.63% | informational | — |
| Average trade | -$0.10 | >0 | FAIL |
| Max equity DD | 12.05% | <=15% | PASS |
| Largest loss | -$0.44 | >=-$1.00 | PASS |
| Commission | -$3.76 | realistic cost included | — |

Directional diagnostics:
- Long PF: 0.62; long net: -$0.75
- Short PF: 0.45; short net: -$2.39

## Commercialization gaps

### 1. Post-cost expectancy is still negative
K4 does not have a commercially usable edge under the locked realistic-cost model. Average trade remains negative and PF is substantially below 1.0, therefore gross winners do not compensate for aggregate losses after modeled costs.

### 2. Signal information content is insufficient
The architectural change from delta-first to price-first increased the number of trades relative to K3, but the resulting sample still loses money. This indicates that merely changing the primary trigger to a 5-bar breakout did not create enough directional information content to overcome execution costs and losing trades.

### 3. Sample quantity is still below the project minimum
K4 generated 32 trades versus the pre-committed minimum of 50. Even if profitability had been marginally positive, this trade count would still block Freeze because statistical confidence is inadequate under the project protocol.

### 4. Risk containment is not the primary failure
Max equity DD (12.05%) and largest single loss (-$0.44) passed their hard limits. The commercial failure is therefore not principally caused by insufficient account protection. Relaxing equity protection, daily protection, stop-loss controls or one-position restrictions is not justified.

### 5. Direction-specific mining is prohibited
Short performance is worse than long performance, but both PF values are below 1.0. The sample is also too small. Therefore disabling shorts or creating long/short-specific thresholds from this result would be post-hoc optimization and is prohibited by the precommit.

### 6. K4 exit/risk parameters may not be mined after the result
SL=0.8 ATR and TP=1.2 ATR were part of the pre-committed architecture. Changing them after seeing the result would invalidate the one-shot protocol. The same restriction applies to breakout lookback, close-location percentile, M15 EMA/ADX conditions, delta confirmation, session and weekday set.

## Root-cause classification

Based on the corrected K/K2/K3/K4 evidence, the dominant unresolved problem is classified as:

**Primary: insufficient entry/gross edge under realistic costs.**

Secondary:
- insufficient trade count / weak statistical confidence;
- cost sensitivity inherent to short-horizon EURUSD M1 trading;
- weak payoff realization relative to spread + commission burden.

Not supported as primary causes:
- breakeven logic;
- adverse-delta exit;
- disabling account drawdown protection;
- hedging / multi-position behavior;
- harness date/data-mode errors (these were corrected before K4).

## Allowed improvement direction

K4 itself is closed. Any further commercial attempt must be a **new architecture hypothesis defined before testing**. It must not reuse the K4 IS result to choose direction-specific settings, thresholds or exits.

A new architecture should address the two observed deficiencies at design time:
1. require a larger expected price excursion per trade relative to total round-trip cost; and
2. produce enough independent opportunities to reach the minimum sample without lowering signal quality through parameter mining.

The next hypothesis may use price action / market structure / trend-pullback-momentum concepts under the existing project prohibitions, but its exact rules, exits, sessions, costs, risk controls and gates must be pre-committed before the first corrected IS run.

## Prohibited actions after this analysis

- No K4 parameter sweep.
- No K4 TP/SL sweep.
- No K4 long-only/short-only mining from this sample.
- No K4 OOS run for tuning.
- No K4 FULL/stress/Monte Carlo promotion tests.
- No commercial/store/mobile release label for K4.
- No disabling hard risk controls to improve backtest ROI.
