# GQ Session Scalper v2 — Code Audit

## Provenance

- Upstream repo: `guetaquant-byte/guetaquant-tools`
- Upstream source: `ctrader/GQ_Session_Scalper.cs`
- Upstream introduction commit: `dd4b5a1782c7cb530961b469ff065d7e13add708`
- Upstream source blob at audit: `0ebb802aae6ccbfaf4a83548a04f76ba0865424d`
- Target repo: `rbhnm859/Ouroboros-Cloud-Build`
- Pre-audit target baseline commit: `cc993e1f8b65ae621ce635174980cee9524ff7d0`
- Pre-audit v2 source blob: `7ec00f620200b5472451d4876391bbcce1fba644`

## Upstream defects / risks

1. Entry is evaluated in `OnTick`, so one completed-bar signal can re-enter intrabar after a fast close or execution race.
2. `LotSize` is passed through `NormalizeVolumeInUnits`; lots and units are different domains and this can materially mis-size exposure.
3. EMA slope logic is directionally confusing in the original conditions and does not implement a clear HTF/LTF trend hierarchy.
4. No hard global one-position/no-hedging ownership rule across the bot label.
5. No equity-risk sizing, broker minimum stop-distance handling, cost-to-reward gate, daily loss stop, loss-cluster control, MAE/MFE or exit diagnostics.
6. ATR is calculated but only used as a loose pullback distance; no volatility regime exists.

## Pre-audit v2 defects / gaps

The existing v2 improved bar-close entry and proportional risk sizing, but still had material gaps:

- `CommissionPerLot` existed but was not consumed by the cost filter.
- Initial R was recomputed from the **current** `Position.StopLoss`. After breakeven/trailing moved the stop, R-multiple calculations became distorted and could approach division-by-zero behavior.
- Position ownership was one position per symbol/label rather than a hard one-position rule across the bot label.
- No broker `MinStopLossDistance`/`MinTakeProfitDistance` normalization.
- No min/max ATR regime or extreme-volatility rejection.
- No max trades/day, max session loss, max losing R/day, minimum equity, Friday cutoff/force close or loss-cluster cooldown.
- No MAE, MFE, holding-time, managed exit-reason, long/short or session diagnostics.
- No Grade A/B gate and no instrumentation needed for ablation/session analysis.
- Existing validation report explicitly used deterministic synthetic OHLC data; it is not broker Tick validation and cannot support a `PROFITABLE CANDIDATE` label.

## Hardening implemented on branch `gq-session-scalper-v2-robust-20260908`

- Entry remains exclusively in `OnBarClosed`; `OnTick` is management/emergency-risk only.
- Signal-bar and entry-bar de-duplication plus bar-based cooldowns.
- Equity-risk volume sizing with broker normalization and `AmountRisked` budget verification.
- Hard `MaxOpenPositions = 1` across the bot label; no stacking or hedging logic.
- HTF fast/slow EMA trend + HTF slope, LTF EMA slope, pullback, reversal and momentum confirmation.
- Grade A/B signal classification; B disabled by default pending positive OOS expectancy.
- ATR min/max and ATR%-based extreme-volatility rejection.
- ATR adaptive SL with configured min/max and broker minimum stop/take-profit distances.
- Spread/SL and total estimated cost/expected TP gates.
- Stable initial-risk state captured at entry; breakeven/trailing no longer mutate the R denominator.
- ATR, swing and Chandelier-style trailing modes.
- Optional time, stagnation, structural-failure and partial exits for controlled ablation.
- Daily/session/loss-cluster controls, Friday controls and optional post-profit risk reduction.
- MAE/MFE/holding time/exit reason/grade/session/long-short diagnostics printed for report parsing.

## Validation status

Source hardening is **not** profitability proof. The next gate is official cTrader compilation followed by real cTrader server-data IS/OOS backtests with explicit costs. Until those pass, status remains:

`PROFITABILITY VALIDATION FAILED`
