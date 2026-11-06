#!/usr/bin/env bash
# Install only Spotware's official cTrader CLI agent skill for Codex.
# No broker login, no trade commands, no deployments, no cBot backtests.
set -Eeuo pipefail

upstream="spotware/ctrader-skills@01e93fec9a802a03fd55b14f1332207c496fe2d0"
skills_cli="skills@1.7.6"
skill_name="ctrader-cli"

error() { printf '[HBXAU-TOOLING] BLOCKED: %s\n' "$*" >&2; exit 2; }
[[ "$#" -eq 0 ]] || error "No arguments supported; review this script before changing behaviour."
command -v git >/dev/null 2>&1 || error "git is required."
root="$(git rev-parse --show-toplevel 2>/dev/null)" || error "Not inside a Git repository."
[[ -f "$root/HarmonyBot-XAUUSD-V1/docs/ISOLATION_CHARTER_V1.md" ]] || error "Expected isolated XAUUSD V1 project not found."
command -v node >/dev/null 2>&1 || error "Install Node.js >=22.20.0 first."
command -v npx >/dev/null 2>&1 || error "npx is unavailable."
node -e 'const [maj,min]=process.versions.node.split(".").map(Number);process.exit(maj>22||(maj===22&&min>=20)?0:1)' ||
  error "Node.js 22.20.0 or newer is required."

printf '[HBXAU-TOOLING] Installing the pinned official skill for Codex (global agent scope; no repository source changes).\n'
npx --yes "$skills_cli" add "$upstream" --agent codex --skill "$skill_name" --yes --global
installed="$(npx --yes "$skills_cli" ls -g)" || error "Cannot verify installed skills."
printf '%s\n' "$installed" | grep -Fq "$skill_name" ||
  error "ctrader-cli did not appear in installed global skills."
printf '[HBXAU-TOOLING] PASS: official ctrader-cli agent skill installed for this environment.\n'

if command -v ctrader-cli >/dev/null 2>&1; then
  ctrader-cli --version || error "cTrader CLI binary exists but --version failed."
  printf '[HBXAU-TOOLING] PASS: cTrader CLI executable version command.\n'
else
  printf '[HBXAU-TOOLING] NOT VERIFIED: cTrader CLI executable is not on PATH.\n'
  printf '[HBXAU-TOOLING] Install it from https://help.ctrader.com/ctrader-cli/setup/ before building or backtesting.\n'
fi
printf '[HBXAU-TOOLING] Trading, broker login, backtesting and live deployment were NOT performed.\n'
