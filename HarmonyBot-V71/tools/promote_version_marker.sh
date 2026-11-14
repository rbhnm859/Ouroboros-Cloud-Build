#!/usr/bin/env bash
set -euo pipefail
: "${1:?version}"; : "${2:?branch}"; : "${3:?evidence}"
VER="$1"; BR="$2"; EVIDENCE="$3"
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
if git ls-remote --exit-code --heads origin "$BR" >/dev/null 2>&1; then
  echo "[VERSION-MARKER] branch already exists: $BR"
  exit 0
fi
git checkout -b "$BR"
mkdir -p "HarmonyBot-$VER"
cat > "HarmonyBot-$VER/${VER}_QUALIFIED_HANDOFF.md" <<EOF
# HarmonyBot $VER — Qualified Evidence Handoff

Source commit: $GITHUB_SHA
Source workflow run: $GITHUB_RUN_ID
Repository: $GITHUB_REPOSITORY

Promotion evidence:

$EVIDENCE

This branch was created automatically only after its preregistered fail-closed gate passed.
A version marker is evidence of a completed capability milestone, not a promise of future market performance.
EOF
git add "HarmonyBot-$VER/${VER}_QUALIFIED_HANDOFF.md"
git commit -m "promote(${VER,,}): qualified evidence milestone"
git push origin "$BR"
echo "[VERSION-MARKER] created $BR"
