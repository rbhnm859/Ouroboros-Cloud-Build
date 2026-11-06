# HarmonyBot XAUUSD V1 — Official cTrader AI tooling

**Scope:** the isolated `feat/harmonybot-xauusd-core-v1-20261106` branch. This file changes developer/agent bootstrap only; it does not modify broker accounts or V74.

## Verified upstream references (2026-11-06)

- Spotware Skill source: https://github.com/spotware/ctrader-skills
- Exact Skill source revision: `01e93fec9a802a03fd55b14f1332207c496fe2d0` (pin, do not silently auto-update)
- Installer reference: https://github.com/vercel-labs/skills/blob/main/docs/commands.md
- Installer version selected for reproducibility: `skills@1.7.6`
- Official CLI setup: https://help.ctrader.com/ctrader-cli/setup/
- Official CLI Skill guide: https://help.ctrader.com/ctrader-cli/skills/
- Official CLI command reference: https://help.ctrader.com/ctrader-cli/

The Spotware repository contains proprietary, EULA-governed material. The repository does **not** vendor or redistribute its Skill files. The bootstrap fetches the pinned official source into the executing agent environment.

## Automatic agent bootstrap

Prerequisites: Git, Node.js >=22.20.0 and npx, network access to npm and GitHub. From the repository root, in a compatible Codex coding-agent environment, the agent runs:

```bash
bash HarmonyBot-XAUUSD-V1/tools/bootstrap_ctrader_cli_skill.sh
```

Effects: install the official `ctrader-cli` Skill into the **current environment's global Codex Skills**, verify that `ctrader-cli` appears in the Skills list, then perform the read-only `ctrader-cli --version` probe **only if the binary is already installed**. The bootstrap does not change this repository's tracked files or enable trading.

The Skill and cTrader CLI binary are separate requirements. On an environment without `ctrader-cli`, install the binary only via official Spotware installers (Homebrew, WinGet or official Docker image) after reviewing its platform requirements. For Windows use the official WinGet instructions; for Linux/macOS use the official Homebrew instructions or Spotware's container. Never replace an unavailable official binary with an unverified package.

## Evidence matrix

| Check | Acceptance evidence | Status until observed |
| --- | --- | --- |
| GitHub setup files | Isolated commit SHA and changed-path audit | NOT VERIFIED |
| Agent Skill installation | Current runner's successful Skills list includes `ctrader-cli` | NOT VERIFIED |
| CLI binary installed | `ctrader-cli --version` returns a real version | NOT VERIFIED |
| cBot compile | Actual native `.algo` and SHA256 from a build job | NOT VERIFIED for CLI toolchain |
| cTrader backtesting | Native, versioned report & data lineage | NOT RUN |
| Broker credentials / live orders | Not used at all | PROHIBITED |
| Commercial acceptance | Independent OOS + governance | NOT VERIFIED |

Node.js/Skills installation in one ephemeral environment does not persist to other GitHub Actions runners or ChatGPT sessions. The ChatGPT GitHub connector manages repository content; it is not the same as a connected shell and cannot install system executables on a remote runner merely by saving these files.

No scheduled checks, paid actions, extra workflows or historical performance claims are introduced. Existing V1 branch-scoped CI may run once upon a V1 source-path commit. The installation script is invoked by a compatible coding agent on demand rather than being run on every V1 CI build.

## Safety and recovery

No broker ID, passwords, tokens, real-money orders, trade modification, cTrader CLI backtest or Railway change is required for this tool bootstrap. If the installer is unavailable, state `BLOCKED` and preserve the existing V1 source untouched. To roll back this configuration, revert only the single dedicated toolchain commit on the V1 branch after review; do not reset V74.
