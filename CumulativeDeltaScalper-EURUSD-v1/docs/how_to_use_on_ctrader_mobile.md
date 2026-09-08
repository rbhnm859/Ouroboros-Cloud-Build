# CumulativeDeltaScalper-EURUSD-v1 on cTrader Mobile

## Scope

This build is restricted to **EURUSD** and only allows **M1, M5, M15, or M30** charts.

## Upload and start

1. Compile or import `builds/CumulativeDeltaScalper_EURUSD_v1.algo` into your cTrader workspace.
2. Open a EURUSD chart in cTrader Automate / Cloud.
3. Select one supported timeframe: M1, M5, M15, or M30.
4. Attach `CumulativeDeltaScalper_EURUSD_v1`.
5. Load the matching conservative preset from `presets/`.
6. Confirm broker volume minimum, maximum, and step on the symbol before going live.
7. Start the bot and monitor the Automate log from mobile.

## Risk behavior

- Every trade is sent with both Stop Loss and Take Profit.
- The bot will not open a new trade if any EURUSD position already exists.
- Grid, martingale, DCA, recovery, and loss averaging are not implemented.
- Position sizing uses `FixedMoneyRisk` and broker min/max/step checks.
- Trading halts when daily loss or daily profit limits are reached.
- Trading also halts after the configured consecutive-loss cap until the next trading day.
- Cooldown blocks re-entry for the configured number of minutes after a managed exit.

## Mobile operation notes

- Mobile can monitor and control a running cloud bot, but source editing and local compilation should still be done from desktop or cloud workflows.
- Turn on `DebugLogging` only when diagnosing behavior; it increases log noise.
- If the bot stops on startup, verify the chart symbol is EURUSD and the timeframe is one of the four allowed values.
