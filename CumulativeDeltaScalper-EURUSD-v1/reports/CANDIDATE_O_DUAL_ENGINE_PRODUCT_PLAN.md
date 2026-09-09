# Candidate O Dual-Engine Product Plan

## Goal

Build a $30-start EURUSD M1 product with two clearly separated engines:

1. **Core Compound Scalper**
   - Primary objective: small-account survival, stable growth, monthly compounding.
   - Uses the proven K/K.1 edge: EURUSD M1, core 14:00-14:54 UTC window, one position only, no grid/martingale/DCA/recovery.
   - Keeps a small TP architecture because K/K.1 proved that the edge comes from short-duration micro scalps, not trend running.

2. **Aggressive Runner Mode**
   - Primary objective: high single-day upside when quality conditions are exceptional.
   - Not allowed to destroy the core account baseline.
   - Uses far emergency TP, breakeven, profit lock and ATR trailing.
   - Must be validated separately because L/M already showed that blind runner logic can destroy expectancy.

## Professional assessment

The objectives conflict if forced into one parameter set:

- Conservative compounding needs controlled frequency, small losses, stable daily exposure and low drawdown.
- Unlimited daily upside needs no profit cap, larger allowed trade count, runner logic and higher variance.

Therefore Candidate O will not be a single mixed setup. It will be tested as a three-profile matrix:

| Profile | Description | Purpose |
|---|---|---|
| O1 Core Compound | K.1-style core scalper with stricter capital protection | Find the safest $30 compounding baseline |
| O2 Aggressive Runner | Limited high-upside runner, no daily profit cap | Test whether high burst mode has positive expectancy |
| O3 Hybrid Guarded | K.1-style TP plus looser daily lock and controlled trade count | Attempt to improve monthly upside without breaking K.1 |

## Product-level rules

- Starting balance: 30 USD
- Symbol: EURUSD
- Timeframe: M1
- Maximum open positions: one by bot logic
- Grid: forbidden
- Martingale: forbidden
- DCA: forbidden
- Recovery / loss averaging: forbidden
- Hedging: forbidden by bot logic; use one label per test profile
- Hard actual loss cap: enabled
- Daily loss cap: enabled
- Daily profit target: disabled for O2/O3, replaced by profit lock
- Primary evaluation: 2Y + recent 1Y, not one cherry-picked period

## Pass/fail gates

A profile is promotable only if it passes the following minimum gates:

- 2Y ROI >= K.1 or recent 1Y improves materially versus K.1
- Profit Factor >= 1.25 for 2Y
- Recent 1Y Profit Factor >= 1.10
- Max drawdown <= 14%
- Largest loss <= 1.10 USD
- No grid/martingale/DCA/recovery behavior
- Trade count high enough to be statistically useful: at least 100 trades over 2Y for core mode

## Interpretation rule

If O2 runner fails again, the product must remain a conservative compound scalper. The aggressive runner mode may remain as a disabled experimental preset, but must not be promoted as the main mobile/cloud profile.
