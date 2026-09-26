#!/usr/bin/env bash
set -euo pipefail
: "${1:?window}"; : "${2:?start}"; : "${3:?eval}"; : "${4:?end}"; : "${5:?years}"
WIN="$1"; START="$2"; EVAL="$3"; END="$4"; YEARS="$5"
C="$PWD/control"
chmod +x "$C/HarmonyBot-V52/tools/"*.sh
"$C/HarmonyBot-V52/tools/run_window.sh" FAMILY_IDENTITY_RECONSTRUCTION "$WIN" "$START" "$EVAL" "$END"
SRC="$C/HarmonyBot-V52/output-FAMILY_IDENTITY_RECONSTRUCTION-$WIN"
DST="$C/HarmonyBot-V68/output-A_V52_EXACT_CONTROL-$WIN"
rm -rf "$DST"; mkdir -p "$DST/raw-logs"
cp "$SRC/FAMILY_IDENTITY_RECONSTRUCTION-$WIN.json" "$DST/A_V52_EXACT_CONTROL-$WIN.json"
if [ -d "$SRC/raw-logs" ]; then cp "$SRC/raw-logs/"* "$DST/raw-logs/" || true; fi
