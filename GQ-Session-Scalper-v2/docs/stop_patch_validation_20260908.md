# GQ v2 Stop-Management Patch Validation

Source patch commit: `c61f2c87383379640d348ab7bcff4aaad540d4eb`

Purpose:
- suppress duplicate Breakeven/Trailing stop modification requests when the broker-side Position.StopLoss snapshot is temporarily stale;
- require at least one tick (or 0.1 pip, whichever is larger) of protective improvement before sending another stop modification;
- persist the last successfully applied stop price in PositionState;
- preserve one-position, no-hedging behavior.

Validation gate:
1. Native cTrader build must return 0 errors.
2. Correct-date EURUSD M15 smoke backtest must still complete.
3. A target-period diagnostic with profitable excursions must show no repeated identical successful stop updates and no duplicate-stop error cluster before optimization begins.
