# CumulativeDeltaScalper EURUSD — One-Shot Commercial Validation Decision

## Final status for K4

**C — FAIL**

The one-shot validation protocol has completed through the K4 corrected IS decision point. The K4 candidate is not frozen and is not eligible for OOS, FULL, stress, robustness, Monte Carlo or commercial/mobile release testing.

## Completed workflow

1. Repository / CI / historical artifact audit — COMPLETE.
2. Corrected commercial harness — COMPLETE.
3. Corrected Original K / K2 / K3 controls — COMPLETE.
4. K3 Flow-First one-shot hypothesis — COMPLETE, C-FAIL.
5. K3 engineering audit — COMPLETE.
6. K4 Price-First Breakout architecture precommit — COMPLETE.
7. K4 source implementation and Release build — COMPLETE.
8. K4 corrected IS with server ticks and realistic costs — COMPLETE.
9. K4 performance-gap analysis — COMPLETE.
10. Freeze-or-fail decision — COMPLETE: C-FAIL.

## K4 evidence

- Tested commit: `6b71671afc4a6a1d5e601a01c9c9dcd7a5ff7cab`
- Validation run: `34485464338`
- Evidence artifact ID: `10155864421`
- Evidence digest: `sha256:ade28bdefd818394ae649e666cfa29bd385305bed8f1e86e38faf1912cb9dfce`

K4 corrected IS:
- ROI: -10.47%
- Net: -$3.14
- PF: 0.51
- Trades: 32
- Win rate: 40.63%
- Average trade: -$0.10
- Max equity DD: 12.05%
- Largest loss: -$0.44
- Commission: -$3.76

Passed only:
- Max equity DD <=15%
- Largest loss >=-$1.00

Failed:
- ROI >0
- PF >=1.15
- Trades >=50
- post-cost expectancy >0

## Stop-rule enforcement

The following actions are explicitly blocked for K4:
- creating `FREEZE_MANIFEST.json`;
- running OOS as promotion or tuning evidence;
- running FULL 2Y as promotion evidence;
- running 1.25x/1.5x cost stress as promotion evidence;
- parameter-neighborhood robustness testing for promotion;
- Monte Carlo promotion testing;
- changing breakout lookback, close-location threshold, ADX, delta vote, session, weekday set, SL, TP or direction-specific thresholds based on the K4 result;
- disabling hard risk controls;
- labeling any K4 `.algo` Commercial, Store, Production or Release.

## Commercialization conclusion

The cumulative-delta / tick-imbalance family and the K4 price-first variant have not demonstrated a positive post-cost edge under the locked EURUSD M1 commercial contract. Risk containment is acceptable, but risk containment alone cannot compensate for negative expectancy and PF below 1.

The project therefore does **not** have a commercial release candidate at K4.

## Only allowed next research path

A future attempt must start from a **new, separately pre-committed architecture**. It must be defined before its first IS run and must restart the full sequence at corrected IS. It may not be a renamed K4 parameter adjustment.

The existing branch `cds-k5-impulse-pullback-reclaim-research` is therefore treated as a research placeholder only. Before any K5 source or backtest is accepted, K5 must contain a precommit specification that fixes:
- primary market event / entry logic;
- confirmation hierarchy;
- session and weekday rules;
- SL/TP and maximum holding logic;
- one-position/no-hedge controls;
- cost model and execution assumptions;
- fixed risk controls;
- IS gates;
- Freeze rule;
- OOS/FULL/stress/robustness/Monte Carlo gates;
- stop rule;
- prohibited tuning actions.

Until that precommit exists and is independently auditable, K5 must not run commercial validation.
