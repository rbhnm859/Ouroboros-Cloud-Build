# EURUSD M1 Sanity Backtest 摘要

## 執行範圍

- 策略：CumulativeDeltaScalper_EURUSD_v1
- 商品：EURUSD
- 週期：M1
- 期間：2025-09-09 至 2026-09-09（UTC，結束日不含）
- 參數：presets/eurusd_m1_conservative.json
- 輸出 JSON：backtests/EURUSD_M1_2025-09-09_to_2026-09-09.json

## 編譯與平台

原始碼已檢查並保留既有交易邏輯與風控限制；在本次檢查中未發現需要為了提交而改寫策略的明確錯誤。Replit sandbox 只有 GitHub 讀寫能力，沒有 cTrader Desktop/Automate、cTrader CLI、cTrader API assemblies 或 broker historical data，因此無法完成真正的 .algo 編譯，也無法執行具備市場資料的 cTrader backtest。

因此本次結果標記為 **未執行（環境不可用）**，不是零交易、不是零損益，也不是通過測試。所有績效欄位在 JSON 中保持 null；沒有虛構的盈利、勝率、Profit Factor 或最大回撤。

## 風控檢查摘要

原始碼保留以下限制：

- EURUSD 前綴與 M1/M5/M15/M30 週期驗證
- 每根完成 K 棒最多作一次進場判斷
- 同一 symbol + label 單持倉，沒有對沖、網格、馬丁格爾、DCA 或虧損攤平
- 每次市價單送出 SL 與 TP
- 預設 FixedMoneyRisk；固定金額風險、風險百分比、固定手數三種模式
- 券商最小／最大／步進交易量檢查與向下正規化
- 最大每日交易數、每日虧損百分比／金額、每日獲利目標、最大連敗、交易間隔與虧損冷卻
- ATR、點差、交易時段、M15 EMA／斜率、ADX 與 cumulative delta 確認條件

這些是程式碼層面的保護，不代表在未執行 backtest 前已證明能在任何券商資料上有效。

## 錯誤與後續步驟

失敗原因是執行環境缺少 cTrader build runtime 與歷史行情，不是已確認的策略編譯錯誤。應在 cTrader Desktop Automate 中 Build；若成功，再用同一份參數與日期範圍執行 EURUSD M1 sanity backtest，將原生報告的交易數、淨利、Profit Factor、勝率、最大回撤、交易拒絕與風控觸發結果填入 JSON。

## 最佳化適用性

本檔只能作為**待執行的 sanity-test 設定與可追溯失敗紀錄**，不適合作為最佳化結果或盈利能力證明。在編譯、資料品質、點差／佣金／滑點模型和基本安全檢查完成前，不應進行參數掃描；即使日後完成 sanity backtest，也應先做 out-of-sample、不同券商資料與壓力測試，並避免把單一期間的結果外推成未來收益承諾。
