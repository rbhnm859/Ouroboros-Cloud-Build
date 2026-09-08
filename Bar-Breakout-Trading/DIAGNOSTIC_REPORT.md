# DIAGNOSTIC REPORT

- 交易訊號使用已收盤 K 棒，避免 look-ahead bias。
- Buy/Sell 以 lookback 高低點 + buffer 判定突破。
- 每個 signal bar 每方向只允許一次訊號（去重 key）。
- 下單採 Market Order，建立後強制驗證 SL。
- 風險倉位以 Risk% 與 PipValue 計算並正規化至 broker volume 規則。
- 支援 max spread、max trades/day、max open positions、daily loss、equity drawdown、consecutive loss、cooldown。

## 補充：雲端回測失敗分類結論

- 失敗案例 `Run 34188549640` 的首個上游異常為 backtest 結果訊息格式損壞，後續才觸發 `BacktestReportSavingStateStrategy.DoEnter()` 的 `Message expected`。
- 分類為：cTrader CLI / report-output pipeline 問題，不是 Bar Breakout cBot 交易邏輯錯誤。
