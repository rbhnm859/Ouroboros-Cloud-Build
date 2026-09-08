# GQ Session Scalper v2

独立的 cTrader cBot 开发版本。

## 目录

- `src/`：当前 C# 源码
- `presets/`：baseline 参数
- `reports/`：候选比较与验证报告
- `logs/`：构建/验证记录
- `docs/`：Broker 与 Symbol 映射资料

## Build status

当前仓库没有保存可验证为 cTrader 原生编译产物的 `.algo`。之前的便携 `.algo` 包仅为源码封装，并非 cTrader 生成的二进制成品，因此已从主分支移除，避免误用。

现有验证记录显示 profitability gate 尚未通过；后续应以真实 cTrader 编译、Broker 实际品种映射及 IS/OOS 回测结果为准。
