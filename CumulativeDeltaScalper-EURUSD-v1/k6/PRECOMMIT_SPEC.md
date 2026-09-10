# K6 Session-Range Sweep Rejection — FINAL Precommitted Commercial Research Specification

## Campaign status
Research Only. K3, K4 and K5 are closed C-FAIL hypotheses. K6 is the FINAL permitted architecture candidate evaluated on the already-used corrected IS window in this commercialization campaign. This specification is committed before any K6 source code or K6 backtest.

If the exact first corrected K6 IS candidate fails any hard gate, the entire current campaign is sealed as NOT COMMERCIAL-READY. No K7/K8 or other new architecture may be tested on the same IS window. Reopening requires a new campaign pre-registration and a genuinely untouched research dataset/window.

## Independent economic hypothesis
K6 is not a threshold retune of K3/K4/K5. It tests a distinct market-microstructure hypothesis: a completed overnight/session range creates visible liquidity at its extremes; during the London transition a one-sided excursion beyond an established extreme that fails to hold and closes back inside the range represents a liquidity sweep/rejection. A short-horizon reversal toward the range interior is tradable only when the rejection bar itself shows adequate displacement relative to transaction cost.

Cumulative/tick delta may be logged as telemetry but is forbidden from changing K6 entry, exit, sizing, stop, target or direction. This prevents recycling the failed flow-first family.

## Timeframes and completed-bar policy
- Execution chart: EURUSD M1.
- Decisions use completed M1 bars only.
- Range is constructed only from completed bars.
- No live/incomplete-bar decision.
- No M5/M15 trend vote, EMA, RSI, MACD, Bollinger, Fibonacci, ML or other strategy module.

## Fixed UTC session architecture
- Range build window: 00:00 through 06:59 UTC.
- Entry window: 07:00 through 11:59 UTC.
- Monday through Friday only.
- At 07:00 the completed overnight range is frozen for that UTC date.
- No entries before the range is frozen.
- Maximum one executed trade per UTC date.

## Fixed range admission
- At least 300 completed M1 observations must contribute to the range.
- Frozen range width must be at least 4.0 pips and at most 35.0 pips.
- These are operational sanity bounds and may not be optimized after first IS.

## Fixed long architecture
1. Frozen overnight range exists and passes range admission.
2. A completed M1 bar trades below the frozen range low by at least 1.0 pip.
3. The same completed bar closes back above the frozen range low.
4. Its close must be in the upper 50% of its own high-low range.
5. Its body magnitude must be at least 25% of its own range.
6. Its total range must be at least 2.0 × the locked estimated round-trip transaction cost in price-distance terms.
7. Entry is Buy only after that bar is completed and all account/risk guards pass.

## Fixed short architecture
Exact symmetric opposite:
1. Frozen overnight range exists and passes admission.
2. Completed M1 bar trades above frozen range high by at least 1.0 pip.
3. Same completed bar closes back below frozen range high.
4. Close in lower 50% of own range.
5. Body magnitude at least 25% of own range.
6. Total range at least 2.0 × locked estimated round-trip transaction cost.
7. Entry Sell only after bar completion and all guards pass.

## Setup lifecycle / duplicate prevention
- No pending multi-bar setup state: the completed sweep-rejection bar is the entire signal.
- A bar can produce at most one direction; ambiguous dual-extreme bars are rejected.
- Maximum one position across the whole symbol, not merely this bot label.
- Maximum one entry per UTC date.
- No same-bar duplicate entry.
- No hedge or opposite concurrent position.

## Locked transaction-cost model
- Commercial validation CLI spread: 0.43 pip.
- Commission: 35 USD per million USD volume.
- Runtime estimated round-trip cost = current spread + round-trip commission equivalent + 0.20 pip execution-safety buffer.
- Entry rejected unless planned reward / estimated total cost >= 2.50.

## Fixed stop and target
- Mandatory entry-time SL and TP.
- Long structural stop: 0.50 pip below the sweep bar low.
- Short structural stop: 0.50 pip above the sweep bar high.
- Broker minimum stop/take-profit distances must be enforced explicitly.
- Planned target is the frozen overnight range midpoint, but only if reward/risk >= 1.20 and reward/cost >= 2.50.
- If midpoint does not satisfy both floors, no trade.
- No alternative TP fallback.
- No breakeven, trailing, scale-in, scale-out, partial close, averaging, recovery or adverse-delta exit.
- Maximum holding time: 180 minutes; then market-close and log `time_stop_180m`.

## Fixed money/risk controls
- Initial validation balance: USD 30.
- Expected leverage: 1:500; runtime mismatch stops trading.
- Risk per trade: min(1.0% of balance, USD 0.30).
- Volume normalized to Symbol.VolumeInUnitsMin/Max/Step and capped at 0.05 lots equivalent.
- Maximum one trade per UTC day.
- Maximum daily closed loss USD 0.60.
- Maximum daily equity drawdown USD 1.20.
- Maximum floating loss USD 0.90.
- Maximum account equity drawdown from runtime peak 12%.
- Maximum consecutive losses 2.
- Mandatory hard protection; failed SL/TP placement is not accepted as a valid position state.

## Broker/platform requirements
- cTrader/cAlgo, net6.0.
- AccessRights.None.
- EURUSD prefix compatibility for FxPro symbol naming.
- ExecuteMarketOrder with mandatory SL/TP.
- Explicit broker min-distance handling and volume normalization.
- No external packages beyond cTrader Automate dependency.
- Research builds must never be labeled Commercial / Store / Production / Release.
- Mobile/Cloud commercial packaging is permitted only after every promotion gate passes.

## Locked corrected validation contract
- EURUSD M1.
- Initial balance USD 30.
- Leverage 1:500.
- Server tick historical data.
- IS: 09/09/2024 00:00 UTC through 08/09/2025 23:59 UTC.
- Spread 0.43 pip.
- Commission 35 USD per million USD volume.
- CLI date semantics DD/MM/YYYY.

## First-IS hard gates
Freeze is permitted only if ALL are true:
- ROI > 0.
- Profit Factor >= 1.15.
- Trades >= 50.
- Max equity DD <= 15%.
- Largest losing trade >= -USD 1.00.
- Post-cost average trade > 0.
- No account/risk/protection invariant violation.

## Freeze rule
Only after all first-IS gates pass:
- create k6/FREEZE_MANIFEST.json with exact source/project/workflow SHA, cTrader image digest, validation contract and IS metrics;
- strategy source/preset becomes immutable;
- only then may OOS execute.

## OOS gates
OOS 09/09/2025 00:00 UTC through 09/09/2026 23:59 UTC. ALL required:
- ROI > 0;
- PF >= 1.20;
- trades >= 50;
- max DD <= 15%;
- largest loss >= -USD 1.00;
- post-cost expectancy > 0;
- PF degradation >25% versus IS must be flagged; no OOS retuning.

## FULL gates
FULL 09/09/2024 00:00 UTC through 09/09/2026 23:59 UTC. ALL required:
- ROI >= 10%;
- PF >= 1.20;
- trades >= 100;
- max DD <= 15%;
- net profit > 0;
- post-cost expectancy > 0.

## Stress gates
Frozen candidate only. Run 1.25x and 1.50x transaction-cost assumptions. At 1.50x require:
- PF >= 1.00;
- net >= 0;
- DD <= 20%;
- monotonic/credible degradation with no implementation discontinuity.

## Robustness diagnostics
Only after OOS/FULL/stress pass. One-neighbor-at-a-time diagnostics, never optimization:
- sweep distance ±10%;
- range width bounds ±10%;
- rejection close-location threshold ±10% relative;
- structural stop buffer ±10%;
- entry-window start/end ±30 minutes.
No isolated sharp optimum is acceptable.

## Monte Carlo
Only after robustness survives:
- trade-order reshuffle;
- spread perturbation;
- slippage perturbation;
- missed-trade simulation;
- one-bar execution-delay simulation.
Report median ROI/net, 5th-percentile outcome, 95th-percentile DD, probability of loss, probability DD>20%, risk-of-ruin proxy.

## Final-campaign stop/seal rule
If the exact first corrected K6 IS candidate fails ANY first-IS hard gate:
1. classify K6 C-FAIL;
2. do not create FREEZE_MANIFEST.json;
3. do not run K6 OOS/FULL/stress/robustness/Monte Carlo;
4. do not create a commercial Mobile/Cloud .algo;
5. create `CumulativeDeltaScalper-EURUSD-v1/reports/COMMERCIALIZATION_REVIEW_SEAL.md` declaring this K3–K6 campaign closed and NOT COMMERCIAL-READY;
6. prohibit any K7/K8/new architecture from using this same IS as discovery evidence.

If K6 passes IS, the campaign may continue only through the fixed sequential gates above. Commercial-ready may be declared only after Freeze + OOS + FULL + 1.25x/1.5x stress + robustness + Monte Carlo + final Mobile/Cloud package integrity checks all pass.

## Prohibited techniques
Grid, Martingale, DCA, Recovery, Loss Averaging, averaging down, reverse recovery, Hedging, parameter sweep, genetic optimization, post-hoc weekday/direction/session mining, and repeated architecture invention on this same IS after K6 are prohibited.
