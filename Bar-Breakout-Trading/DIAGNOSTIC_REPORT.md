# DIAGNOSTIC REPORT

- 交易訊號使用已收盤 K 棒，避免 look-ahead bias。
- Buy/Sell 以 lookback 高低點 + buffer 判定突破。
- 每個 signal bar 每方向只允許一次訊號（去重 key）。
- 下單採 Market Order，建立後強制驗證 SL。
- 風險倉位以 Risk% 與 PipValue 計算並正規化至 broker volume 規則。
- 支援 max spread、max trades/day、max open positions、daily loss、equity drawdown、consecutive loss、cooldown。
