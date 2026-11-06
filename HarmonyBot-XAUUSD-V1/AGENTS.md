# HarmonyBot XAUUSD V1 — scoped coding-agent instructions

Scope: `HarmonyBot-XAUUSD-V1/` only. Keep the separate V74/R18 research and its protected branch unchanged. Read `docs/ISOLATION_CHARTER_V1.md` and `docs/ENGINEERING_PLAN_V1.md` before changing any code.

## cTrader tooling bootstrap

When a user request actually requires cTrader CLI, a new agent environment should first run, from the repository root:

```bash
bash HarmonyBot-XAUUSD-V1/tools/bootstrap_ctrader_cli_skill.sh
```

This installs **only** the pinned, official Spotware `ctrader-cli` Skill for Codex via the published `skills` installer. This is environment-local tooling installation, **not** installation into the ChatGPT app/plugin directory. Read the installed Skill before producing CLI commands. A new disposable cloud workspace may need to run the bootstrap again.

If the script returns BLOCKED, fix only the missing prerequisite and retry once; do not silently install alternative packages or unverified cTrader binaries. If `ctrader-cli --version` is NOT VERIFIED, do not claim CLI build/backtest functionality is available.

## Absolute execution restrictions

- Research-only adapter: `TradingApproved=false`. Never place, modify, cancel, close or submit broker orders, even in a demo account, in this phase.
- No credentials or cTrader ID in logs, files or URLs. No secret exfiltration, no account connection by default.
- No production deployment, broker configuration edits, Railway/LibreChat changes, or paid backtests.
- Keep changes limited to this V1 directory and the existing V1-only workflow file; preserve the pinned branch-isolation baseline and all V74/R18 evidence.
- CI compilation and synthetic tests are not evidence of trading performance, genuine tick backtesting, broker compatibility or commercial acceptance.
- Check version output first if the official CLI executable is present. Do not improvise CLI syntax; use official documentation and the pinned Skill.
- A new GitHub Actions runner or Codex cloud session is ephemeral. Never claim persistent ChatGPT-wide installation from a single runner's Skill receipt.

See `docs/CTRADER_AI_TOOLCHAIN.md` for precise setup and acceptance scope.
