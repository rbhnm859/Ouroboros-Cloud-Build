# Store Comparison and Candidate N Optimization Plan

## Objective

Improve `CumulativeDeltaScalper_EURUSD_v1` for a minimum starting balance of USD 30 while avoiding grid, martingale, DCA, recovery, loss averaging, and hedging.

The optimization direction is not to maximize cosmetic win rate. The new priority is:

1. survival at USD 30 minimum balance;
2. month-to-month compounding potential;
3. controlled absolute loss per trade;
4. higher daily upside when conditions are favorable;
5. avoidance of weak recent-year regimes;
6. no blind 24h trading;
7. no unrestricted lot expansion.

## Store Comparison Summary

Common cTrader Store scalper features observed in similar products:

- ATR based SL/TP;
- breakeven;
- trailing stop;
- partial profit taking;
- daily drawdown and trade limits;
- spread filters;
- trend and volatility filters;
- in many cases, grid/martingale/shared basket TP or multiple-position management.

For USD 30 minimum balance, grid, martingale, shared basket TP, no fixed SL, and large multi-position logic are rejected because they amplify tail risk and margin stress.

## Internal Backtest Baseline

Current validated internal results:

- Candidate K: higher ROI, weaker risk cap.
- Candidate K.1: strongest current risk-controlled version.
- Candidate L: failed. Runner and all-day scan overfiltered and degraded expectancy.
- Candidate M: failed. Limited runner reduced loss size but destroyed expectancy and recent-year performance.

Therefore, Candidate N must not continue full Runner optimization. The correct direction is to return to K.1's profitable micro-scalping structure and optimize the missing parts around time, weekday, direction, volume, and profit lock.

## Candidate N Hypothesis

The K.1 report showed that:

- 0.01 lot trades were the most stable contributor.
- 0.02 and 0.03 lots degraded results.
- Monday was nearly flat and did not justify its risk contribution.
- Wednesday and Friday were the strongest days.
- Short side was much weaker than long side.
- Recent-year performance weakened, so recent 1Y validation is mandatory.

## Candidate N Matrix

Run four parameter families:

### N1 Conservative Compound

- K.1 core session.
- Disable Monday.
- Keep Tuesday, Wednesday, Friday.
- Max lot = 0.01.
- No Runner.
- No hard daily profit target.
- Use daily profit giveback lock instead.
- Goal: improve stability, PF, and recent 1Y without overfitting.

### N2 Wednesday Friday Quality

- Trade only Wednesday and Friday.
- Max lot = 0.01.
- No Runner.
- Daily profit lock enabled.
- Goal: test if removing weaker weekdays improves PF and drawdown.

### N3 Long Bias / Short Suppression

- Tuesday, Wednesday, Friday.
- Max lot = 0.01.
- Short entries effectively blocked through strict short filters.
- No Runner.
- Goal: test whether K.1's long-side edge can stand alone.

### N4 Controlled Upside

- Wednesday and Friday.
- Max lot = 0.02.
- No Runner.
- Daily profit lock enabled.
- Goal: test whether controlled limited scaling can increase monthly/daily upside without destroying drawdown.

## Promotion Gate

A Candidate N variant may only replace K.1 if it beats K.1 on risk-adjusted quality, not just on total ROI.

Minimum requirements:

- 2Y ROI > K.1 or at least close with clearly lower drawdown;
- Recent 1Y ROI materially better than K.1 recent 1Y;
- Profit factor >= 1.25;
- Recent 1Y profit factor >= 1.15;
- Max drawdown <= 10%;
- Largest loss <= USD 1.05;
- No negative recent 1Y;
- Enough trades to avoid false confidence.

## Execution

The workflow `cdscalper-eurusd-v1-candidate-n-matrix-30.yml` builds a fresh `.algo` from the current source and runs all N variants over:

- 2024-09-09 to 2026-09-09;
- 2025-09-09 to 2026-09-09.
