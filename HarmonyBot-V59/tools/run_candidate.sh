#!/usr/bin/env bash
set -euo pipefail
: "${CANDIDATE:?}"; : "${RUN_NAME:?}"; : "${START_DATE:?}"; : "${EVAL_DATE:?}"; : "${END_DATE:?}"; : "${CALIBRATION_MANIFEST:?}"
case "$CANDIDATE" in
 V59_MANIFOLD_CAPTURE_L0) GRID=false;;
 V59_MANIFOLD_CAPTURE_LEGACY_GRID) GRID=true;;
 *) echo "unsupported V59 candidate $CANDIDATE"; exit 31;;
esac
CALMAN=$(tr -d '\n\r' < "$CALIBRATION_MANIFEST"); test -n "$CALMAN"
FAMNATIVE=false FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true \
IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true TRADING=true FAMILYBOOKS=true SHADOW=true CALADMIT=true FAMREP=true RESEARCHCONT=true \
ABCDLIVE=false V59GRID="$GRID" CALMIN=0.0 CALMAN="$CALMAN" MANIFOLD=true PUREPRZ=true DAG=true CAPRESEARCH=true CAPLIVE=true MATCHED=true PROJERR=.55 MSIG=1.0 \
PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false \
"$GITHUB_WORKSPACE/control/HarmonyBot-V59/tools/run_backtest.sh"
