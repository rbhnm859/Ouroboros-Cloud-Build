# cTrader cBot Workspace

这个 repository 依 cBot 项目分类，主分支只保留当前源码、必要构建链、有效回测/验证资料与可确认用途的成品。

## Bot 项目

- `FibonacciHarmonicSniperUltimate/`
  - 主线源码与项目文件
  - `versions/v0.3.0-fix5/`：目前保留的最新修正版
  - `research-archives/`：研究输入/封存
  - `reports/`：回测与诊断结果
- `GQ-Session-Scalper-v2/`
  - `src/`：源码
  - `presets/`：参数基线
  - `reports/`：候选与验证报告
  - `logs/`：构建/验证记录
  - `docs/`：Broker/Symbol 等技术资料
  - 主分支不再保存会被误认为原生编译成品的便携 `.algo` 包；需以真实 cTrader 编译结果为准
- `Keltner-Channels-Trader-v2/`
  - `source/`：可编译源码
- `Ouroboros/`
  - `builds/`：已保存的 Mobile/Cloud `.algo`
  - `handoff/`：交付封装与说明

## GitHub Actions

`.github/workflows/` 只保留仍有实际用途的构建、回测与工具流程。一次性修补、已失效诊断、旧版重复流程会从主分支移除。

## Backup

整理前状态均可从以下分支恢复：

- `backup/pre-reorg-2026-09-08`
- `backup/pre-deep-cleanup-2026-09-08`

## Cleanup policy

- 不删除当前交易源码与关键验证报告。
- 删除重复压缩包、失效 workflow、一次性补丁 workflow、误导性非原生成品与无关对话记录。
- 不修改 cBot 交易逻辑。
