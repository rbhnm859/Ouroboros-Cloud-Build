# Bar Breakout Trading

- source: `source/Bar Breakout Trading.cs`
- project: `source/Bar Breakout Trading.csproj`
- compiled algo: `compiled/release/BarBreakoutTrading.algo`
- reports: `reports/backtests/`

此版本使用已收盤 Bar (`OnBarClosed`) 執行突破判定，並包含風險控管、交易成本過濾、SL/TP 與可選 Breakeven/Trailing。
