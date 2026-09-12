# CumulativeDeltaScalper FX Commercial V3 — Commercial Freeze Gates

## Purpose
V3 is a hardening rewrite of Adaptive V2. Original K and V2 remain immutable baselines. A build is not called commercial/final unless every mandatory gate below is evidenced by cTrader reports.

## Non-negotiable architecture
- cTrader Automate / cAlgo, AccessRights.None, no external package dependency.
- Closed-bar entries only; no duplicate entries.
- One open position maximum for this bot; no hedging.
- No Grid, Martingale, DCA, Recovery, Loss Averaging or position averaging.
- Every market entry is submitted with SL and TP.
- Volume must be normalized with RoundingMode.Down and then re-validated against actual monetary stop risk.
- If broker minimum volume would exceed the hard monetary risk cap, the trade must be skipped (fail closed), never rounded up into excess risk.
- TradeResult and ModifyPosition results must be checked; protection failures are not ignored.

## Baseline test assumptions
- Broker: FxPro
- Deposit asset: USD
- Leverage: 1:500 when the test account supports it
- Primary screening: M1 and M5
- Starting capital: USD 100 for comparability with V2
- Commission: USD 35 / million USD volume
- Pair-specific fixed spread for base test; 1.5x spread for stress test
- Data mode: broker/server M1 bars

## Risk gates (mandatory)
- Requested risk per trade <= 0.50% equity by default.
- Hard estimated stop-risk cap <= 1.00% equity.
- Post-normalization estimated stop risk <= hard cap × 1.05 tolerance.
- Maximum daily realized loss <= 2.0% of start-of-day equity.
- One position maximum.
- No trade may be opened without valid broker-compatible SL/TP distances.
- Critical protection/modify failure must be logged and must not silently remove protection.

## Signal/exit hardening gates
- Directional signal must not rely on pressure threshold crossing alone.
- Entry requires pressure persistence + price structure confirmation + multi-timeframe trend/regime agreement.
- Cost-aware gate must use expected reward after spread + round-trip commission estimate.
- Adverse-pressure exit cannot immediately override a valid setup on a single noisy bar; opposite pressure must persist and/or price structure must invalidate.
- Breakeven must cover estimated transaction cost before moving stop to a nominal profit.
- Trailing cannot start before positive R is established.
- Time exit must distinguish stagnation from healthy trend continuation.

## Performance gates
A pair/timeframe is allowed into the commercial whitelist only if all applicable gates pass:

### In-sample / development window
- Net profit > 0 after configured spread and commission.
- Profit Factor >= 1.25.
- Max equity drawdown <= 12%.
- Minimum 50 closed trades when the period/liquidity allows; otherwise mark sample insufficient rather than pass.

### Out-of-sample window
- Net profit > 0 after costs.
- Profit Factor >= 1.10.
- Max equity drawdown <= 12%.
- No single month may account for more than 60% of total positive OOS PnL.

### Stress
- 1.5x base spread + same commission: Profit Factor >= 1.00 and net profit >= 0 preferred; if slightly negative, pair cannot be labeled robust/final.
- Key parameters ±10%: no cliff failure (no immediate collapse to PF < 0.90 or DD > 20%).

## Validation layout
- Full one-year benchmark: 2025-09-12 to 2026-09-12.
- Development/IS: 2025-09-12 to 2026-05-31.
- OOS: 2026-06-01 to 2026-09-12.
- Re-run winning candidates on at least one additional earlier period before freeze when broker history is available.

## Commercial whitelist policy
The code may recognize the standard 28 FX pairs, but production support is evidence-driven. Only pairs that pass the gates are enabled in the final commercial preset/whitelist. A pair with zero trades, insufficient sample, negative expectancy, or unstable stress performance is not presented as commercially supported.

## Freeze definition
`COMMERCIAL_FREEZE = true` only after:
1. source audit clean;
2. build clean;
3. broker API/runtime smoke clean;
4. base IS/OOS clean;
5. cost stress clean;
6. risk audit clean;
7. parameter sensitivity acceptable;
8. exact .algo hash and source commit recorded.
