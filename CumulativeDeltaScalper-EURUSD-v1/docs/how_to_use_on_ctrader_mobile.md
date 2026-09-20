# How to use on cTrader Mobile / Cloud

## Important

cTrader Mobile normally cannot compile raw C# cBot source by itself. You need cTrader Desktop Automate, cTrader Cloud sync, or another working build environment to produce or sync the bot.

## Desktop build flow

1. Open cTrader Desktop.
2. Go to Automate.
3. Create a new cBot named `CumulativeDeltaScalper_EURUSD_v1`.
4. Open the GitHub file:
   `CumulativeDeltaScalper-EURUSD-v1/src/CumulativeDeltaScalper_EURUSD_v1.cs`
5. Copy all code into the new cBot.
6. Click Build.
7. Fix any API-version compile errors if cTrader reports them.
8. After Build succeeds, run backtests on EURUSD M1/M5/M15/M30.

## Cloud / Mobile flow

1. Log in to the same cTrader ID on Desktop and Mobile.
2. After the bot builds successfully, sync it to cTrader Cloud.
3. Open cTrader Mobile.
4. Select EURUSD or your broker's EURUSD suffix symbol.
5. Select M1, M5, M15 or M30.
6. Attach the cBot.
7. Use conservative presets first.

## Parameters not to increase blindly

- Fixed Money Risk
- Max Lot Size
- Max Daily Trades
- Max Daily Loss Money
- Max Daily Loss Percent
- Delta Threshold
- SL/TP ATR Multipliers

## Recommended first test order

1. EURUSD M5
2. EURUSD M15
3. EURUSD M30
4. EURUSD M1

M1 can create more noise and cost pressure, so it should not be treated as safest just because it is faster.
