# Risk Check

## Default risk mode

`FixedMoneyRisk`

Default fixed money risk: `1.00`

## Why fixed money risk

Small accounts can be destroyed by fixed lot sizing. This branch calculates volume from the stop-loss distance and the selected money risk, then checks broker minimum and maximum volume.

## Safety limits

- Max Daily Trades: 3
- Max Daily Loss Percent: 2.0
- Max Daily Loss Money: 3.00
- Daily Profit Target Money: 5.00
- Max Consecutive Losses: 2
- Min Seconds Between Trades: 900
- Loss Cooldown Minutes: 15

## Prohibited mechanisms

- Grid: not implemented
- Martingale: not implemented
- DCA: not implemented
- Recovery: not implemented
- Loss Averaging: not implemented
- Hedging: blocked through one-position guard
