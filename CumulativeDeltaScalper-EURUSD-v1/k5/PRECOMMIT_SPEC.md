# K5 Impulse-Pullback-Reclaim — Precommitted Commercial Research Specification

## Status
Research Only. This specification is committed before any K5 source backtest. K4 is already C-FAIL and is not retuned.

## Research hypothesis
The prior K/K2/K3/K4 family entered from noisy M1 threshold/breakout events and repeatedly failed after realistic EURUSD transaction costs. K5 tests a genuinely different hypothesis: a larger completed M5 directional impulse establishes intent, a controlled M1 pullback proves price can retrace without invalidating the impulse, and a completed M1 reclaim provides the entry trigger. Tick/cumulative delta is telemetry only and is not an entry vote or veto.

## Timeframes
- Robot execution chart: EURUSD M1.
- Primary event: completed M5 bars.
- Entry timing: completed M1 bars.
- Higher-timeframe context: completed M15 bars.
- No live/incomplete bar may be used for a decision.

## Fixed long architecture
1. A completed M5 impulse bar must be bullish.
2. Its range must be >= 1.25 × completed M5 ATR(14).
3. Its body must be >= 60% of its own range.
4. Its close must be in the upper 25% of its range.
5. The last completed M15 close must be above completed M15 EMA50, and completed EMA50 must be above its value three completed M15 bars earlier.
6. After the impulse closes, allow at most the next 6 completed M1 bars to form a pullback.
7. The pullback must trade into the 33%–66% retracement zone of the impulse range.
8. No completed M1 pullback bar may close below the impulse midpoint. A close below the midpoint invalidates the setup.
9. After a valid pullback, a completed bullish M1 reclaim bar must close above the impulse 66% level and close above its own open.
10. Entry occurs only after that reclaim bar is completed and all guards pass.

## Fixed short architecture
Exactly symmetric:
- bearish completed M5 impulse;
- same 1.25 ATR, 60% body and lower-25% close rules;
- completed M15 close below EMA50 with negative three-bar EMA slope;
- next 6 completed M1 bars may pull back into the 33%–66% retracement zone;
- no completed pullback bar may close above the impulse midpoint;
- completed bearish reclaim bar must close below the impulse 33% level and below its own open;
- entry only after the reclaim bar is completed.

## Setup lifecycle
- Only one active setup may exist at a time.
- A newer opposite M5 impulse invalidates the current setup.
- Setup expires after 6 completed M1 bars if no valid pullback/reclaim occurs.
- No same-bar duplicate entry.
- After an entry, the setup is cleared.

## Delta/tick data policy
- Existing tick-direction / fallback delta may be logged for diagnostics only.
- Delta is forbidden from changing K5 entry, exit, sizing, stop, target or direction.
- No DeltaThreshold parameter exists in K5.

## Fixed trading session
- Monday through Friday enabled.
- Trading window: 07:00–16:30 UTC (London through London/New York overlap).
- No weekday-specific exclusions.
- No post-hoc session optimization is permitted on this IS window.

## Fixed spread/cost admission
- Commercial validation CLI spread: 0.43 pip.
- Commission: 35 USD per million USD volume.
- Runtime estimated round-trip cost = current spread + round-trip commission equivalent + 0.20 pip execution safety buffer.
- A setup may enter only if planned TP distance / estimated total cost >= 2.50.
- This is an economic safety floor, not a ranking/optimizer score.

## Fixed risk and exits
- Maximum one position per symbol/label; no opposite concurrent position.
- Mandatory entry-time SL and TP.
- Structural SL: beyond the pullback extreme by 0.10 × completed M1 ATR(14).
- Stop distance must also be at least broker minimum stop distance.
- TP = 1.80R from actual planned stop distance.
- No breakeven.
- No trailing stop.
- No adverse-delta exit.
- Maximum holding time = 90 minutes; if still open, close at market and log `time_stop_90m`.
- No scale-in, scale-out, averaging, recovery or re-entry layering.

## Fixed money/risk controls
- Initial validation balance: USD 30.
- Expected leverage: 1:500; runtime mismatch stops the bot.
- Risk per trade: min(1.0% of balance, USD 0.30).
- Volume must be normalized to Symbol.VolumeInUnitsMin/Max/Step and must not exceed 0.05 lots equivalent.
- Maximum 3 trades per UTC day.
- Maximum daily closed loss: USD 0.90.
- Maximum daily equity drawdown: USD 1.20.
- Maximum floating loss: USD 0.90.
- Maximum account equity drawdown from runtime peak: 12%.
- Maximum consecutive losses: 2.
- Minimum 15 minutes between entries.
- After a loss, 45-minute cooldown.
- Hard equity/risk guards are never disabled for promotion tests.

## Broker/platform requirements
- cTrader/cAlgo, net6.0.
- `AccessRights.None`.
- EURUSD symbol prefix compatibility for FxPro naming.
- `ExecuteMarketOrder` entry with mandatory protection.
- Broker min stop/take-profit and normalized volume handled explicitly.
- Mobile/Cloud-compatible `.algo` packaging only after commercial PASS.
- Research builds must never be labeled Commercial / Store / Production / Release.

## Locked validation contract
- EURUSD M1.
- Initial balance USD 30.
- Leverage 1:500.
- Server tick historical data.
- IS: 09/09/2024 00:00 UTC through 08/09/2025 23:59 UTC.
- Spread 0.43 pip.
- Commission 35 USD per million USD volume.
- CLI date semantics use DD/MM/YYYY.

## First-IS hard gates
Freeze is permitted only if ALL are true:
- ROI > 0.
- Profit Factor >= 1.15.
- Trades >= 50.
- Max equity DD <= 15%.
- Largest losing trade >= -USD 1.00.
- Post-cost average trade > 0.
- No risk/protection invariant violation.

## Freeze rule
If and only if every first-IS gate passes:
- create `k5/FREEZE_MANIFEST.json` containing exact source SHA, project SHA, workflow SHA, cTrader image digest, validation contract and IS metrics;
- no strategy source or preset may change after freeze;
- only then may OOS run.

## OOS gates
OOS: 09/09/2025 00:00 UTC through 09/09/2026 23:59 UTC.
ALL required:
- ROI > 0;
- PF >= 1.20;
- trades >= 50;
- max DD <= 15%;
- largest loss >= -USD 1.00;
- post-cost expectancy > 0;
- flag PF degradation >25% versus IS; no OOS retuning allowed.

## FULL gates
FULL: 09/09/2024 00:00 UTC through 09/09/2026 23:59 UTC.
ALL required:
- ROI >= 10%;
- PF >= 1.20;
- trades >= 100;
- max DD <= 15%;
- net profit > 0;
- post-cost expectancy > 0.

## Stress gates
Run frozen candidate at 1.25× and 1.50× transaction-cost assumptions.
At 1.50× require:
- PF >= 1.00;
- net >= 0;
- DD <= 20%;
- degradation must be monotonic/credible rather than discontinuous due to implementation defects.

## Robustness
Only after OOS/FULL/stress pass. One-neighbor-at-a-time diagnostic perturbations, not optimization:
- impulse ATR threshold ±10%;
- retracement boundaries ±10% relative;
- TP R multiple ±10%;
- session start/end ±30 minutes;
- M15 EMA period ±10%.
No isolated sharp optimum is acceptable.

## Monte Carlo
Only after robustness survives:
- trade-order reshuffle;
- spread perturbation;
- slippage perturbation;
- missed-trade simulation;
- one-bar execution-delay simulation.
Report median net/ROI, 5th-percentile outcome, 95th-percentile DD, probability of loss, probability DD>20%, and risk-of-ruin proxy.

## Stop rule
If the exact first K5 IS candidate materially fails the hard gates, classify K5 C-FAIL and stop this hypothesis. Do not tune impulse threshold, pullback zone, reclaim level, EMA, session, weekday, SL, TP, time stop, direction-specific parameters or delta using the same IS result. Do not run OOS for a failed K5 candidate.

## Prohibited techniques
Grid, Martingale, DCA, Recovery, Loss Averaging, averaging down, reverse recovery and Hedging are prohibited. No Fibonacci, RSI, MACD, Bollinger, ML or new technical-indicator strategy modules are introduced.
