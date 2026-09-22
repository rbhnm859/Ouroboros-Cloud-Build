#!/usr/bin/env bash
set -euo pipefail
: "${CANDIDATE:?}"; : "${RUN_NAME:?}"; : "${START_DATE:?}"; : "${EVAL_DATE:?}"; : "${END_DATE:?}"
case "$CANDIDATE" in
 V56_EVIDENCE_EXPANSION_LEGACY_GRID) GRIDV4=false;;
 V56_EVIDENCE_EXPANSION_GRID_V4) GRIDV4=true;;
 *) echo "unsupported V56 candidate $CANDIDATE"; exit 31;;
esac
FAMNATIVE=false FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true \
IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true FAMQUAL=true FAMROUTE=true FAMCONFV2=true CTXBUS=true GRIDEXEC=true \
LIBERATE=true COREKEEP=true GRIDV3=false STATEGRID=false EVIDENCE=true COREPROT=true GRIDV4="$GRIDV4" EMIN=.64 ERMIN=.10 HAZMAX=.68 ABCDMIN=.76 \
PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false \
"$GITHUB_WORKSPACE/control/HarmonyBot-V56/tools/run_backtest.sh"
