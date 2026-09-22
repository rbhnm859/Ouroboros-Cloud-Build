#!/usr/bin/env bash
set -euo pipefail
: "${CANDIDATE:?}"; : "${RUN_NAME:?}"; : "${START_DATE:?}"; : "${EVAL_DATE:?}"; : "${END_DATE:?}"; : "${CALIBRATION_MANIFEST:?}"
case "$CANDIDATE" in
 V57_CALIBRATED_L0) V57GRID=false;;
 V57_CALIBRATED_LEGACY_GRID) V57GRID=true;;
 *) echo "unsupported V57 candidate $CANDIDATE"; exit 31;;
esac
CALMAN=$(tr -d '\n\r' < "$CALIBRATION_MANIFEST")
test -n "$CALMAN" || { echo "[V57-CANDIDATE-MANIFEST-EMPTY]"; exit 32; }
FAMNATIVE=false FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true \
IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true TRADING=true FAMILYBOOKS=true SHADOW=true CALADMIT=true FAMREP=true RESEARCHCONT=true \
ABCDLIVE=false V57GRID="$V57GRID" CALMIN=0.0 CALMAN="$CALMAN" PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false \
"$GITHUB_WORKSPACE/control/HarmonyBot-V57/tools/run_backtest.sh"
