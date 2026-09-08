# Risk audit — source and compile verification, runtime acceptance pending

| Requirement | Implementation / limitation |
| --- | --- |
| EURUSD/suffix | Case-insensitive EURUSD prefix; parameter cannot enable unrelated symbols |
| M1/M5/M15/M30 | Any enabled supported period is accepted; no requirement that all are enabled |
| One position, no hedging | Account-wide positions and pending orders block entry regardless of label. Run only one instance on a dedicated account: other independent bots/manual orders cannot be atomically locked by this cBot |
| No grid/martingale/DCA/recovery | One synchronous market entry path; no pending-order creation or loss-based volume escalation |
| SL and TP | Positive finite distances on every entry; verify returned position and every managed tick. Missing protection latches entry block and requests emergency closure; broker rejection/disconnection can still prevent closure |
| Fixed Money Risk | VolumeForFixedRisk rounded down, capped, then AmountRisked checked against budget. Estimate excludes commission, gaps/slippage and currency-conversion error; not a guaranteed cash loss cap |
| Broker volume | Min/max, NormalizeVolumeInUnits with Down, positive step, non-finite checks, free-margin preflight. Below-minimum volume is skipped, never rounded up |
| Daily loss money/percent | Smaller enabled limit; zero disables that particular limit. Bot realized + floating net P/L triggers latch and managed-position close. Reset UTC midnight. Entry risk also checked against remaining daily budget |
| Daily percent base | Account balance reconstructed from available history at UTC midnight. Deposits/withdrawals are not historical trades and may distort this baseline |
| Daily profit target | Blocks new entries after realized daily bot profit reaches target; no profit guarantee |
| Consecutive losses | Today's ordered closed trades reconstructed at startup, closed events and new bars; reset daily |
| Cooldown | Most recent entry/loss recovered from history; time exit recovered from actual position.EntryTime |
| Debug Logging | Parameter controls diagnostic logs. Protection and daily-loss emergencies always print |
| Breakeven | Default off; tick-rounded stop, broker distance buffer, TP preserved, absolute protection type, five-second retry throttle |

History is no longer fully scanned on every tick. Daily statistics use bot label and exact broker symbol; changing the label changes the statistics scope. A floating-loss latch is in memory; restart recovery uses available realized history and current floating P/L, not a persisted intraday equity high/low. The original fixed M15 confirmation timeframe is preserved, including for M30 (not a higher timeframe in that case). The pre-existing Overlap Only parameter remains a compatibility setting with no effect; the explicit UTC session window controls trading.

Tick delta is an uptick/downtick proxy, not centralized exchange executed-volume delta. Baseline ATR/TP/SL multipliers and confirmation logic are retained, without optimization. Runtime duplicate/protection/InvalidRequest results remain unknown until actual CLI events are audited.
