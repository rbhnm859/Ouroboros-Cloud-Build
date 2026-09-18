#!/usr/bin/env bash
set -euo pipefail
C="$PWD/control"; W="$C/HarmonyBot-V34/work"; O="$C/HarmonyBot-V34/output"
rm -rf "$W" "$O"
mkdir -p "$W/seal/algo" "$O"
CURRENT_STAGE="BOOT"
progress(){ printf '%s [V34-PROGRESS] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$O/RUN_PROGRESS.log"; }
trap 'rc=$?; if [ "$rc" -ne 0 ]; then progress "FAILED stage=${CURRENT_STAGE:-unknown} rc=$rc"; fi' EXIT
cd "$C"
progress "START clean regression"
python3 HarmonyBot-V34/tools/static_audit.py HarmonyBot-V34/src/HarmonyBotV34.cs
cp V34_ARCHITECTURE_AUDIT.json "$O/"
dotnet restore HarmonyBot-V34/HarmonyBotV34.csproj
dotnet build HarmonyBot-V34/HarmonyBotV34.csproj -c Release --no-restore --nologo 2>&1 | tee "$O/V34_BUILD.log"
ALGO=$(find HarmonyBot-V34/bin/Release -type f -name '*.algo'|head -1); test -s "$ALGO"
cp "$ALGO" "$W/seal/algo/HarmonyBot_V34_Internal.algo"
cp HarmonyBot-V34/src/HarmonyBotV34.cs "$O/"
sha256sum HarmonyBot-V34/src/HarmonyBotV34.cs "$ALGO" > "$O/SHA256SUMS"

run(){
 local n=$1 w=$2 st=$3 ev=$4 en=$5 bal=$6
 CURRENT_STAGE="$n"; progress "START stage=$n window=$w balance=$bal"
 (cd "$W"; RUN_NAME="$n" START_DATE="$st" EVAL_DATE="$ev" END_DATE="$en" BALANCE="$bal" BACKTEST_TIMEOUT_SECONDS=2700    "$C/HarmonyBot-V34/tools/run_backtest.sh")
 python3 "$C/HarmonyBot-V34/tools/audit_report.py" --report "$W/seal/reports/$n.json" --log "$W/seal/logs/$n.log"    --out "$O/$w.json" --window "$w" --years .5 --balance "$bal"
 progress "DONE stage=$n"
}

# Exposed windows: engineering regression only. Never use these metrics for tuning.
run V34-ENG-DEV-A ENG-DEV-A 04/01/2021 2021-01-11T00:00:00Z 30/06/2021 10000
run V34-ENG-DEV-B ENG-DEV-B 01/07/2021 2021-07-08T00:00:00Z 31/12/2021 10000
run V34-ENG-DEV-C ENG-DEV-C 03/01/2022 2022-01-10T00:00:00Z 30/06/2022 10000

# USD100 Micro-Capital engineering track on the same exposed windows.
run V34-MICRO100-A MICRO100-A 04/01/2021 2021-01-11T00:00:00Z 30/06/2021 100
run V34-MICRO100-B MICRO100-B 01/07/2021 2021-07-08T00:00:00Z 31/12/2021 100
run V34-MICRO100-C MICRO100-C 03/01/2022 2022-01-10T00:00:00Z 30/06/2022 100

mkdir -p "$O/raw-logs"; cp "$W/seal/logs/"*.log "$O/raw-logs/" || true

CURRENT_STAGE="GATE"; progress "START stage=GATE"
python3 - "$O" <<'PY'
import json,pathlib,sys
o=pathlib.Path(sys.argv[1])
eng=[json.load(open(o/f"ENG-DEV-{x}.json")) for x in "ABC"]
mic=[json.load(open(o/f"MICRO100-{x}.json")) for x in "ABC"]
engineering_clean=all(x["engineering_clean"] and x["broker_profile_present"] for x in eng)
micro_clean=all(x["engineering_clean"] and x["broker_profile_present"] for x in mic)
micro_baskets=sum(x["baskets"] for x in mic)
micro_mode_baskets=sum(x["micro_mode_baskets"] for x in mic)
micro_operational=micro_clean and micro_baskets>0 and micro_mode_baskets>0 and sum(x["capital_compat_events"] for x in mic)>0
eng_gate={"version":"HarmonyBot V34.0","purpose":"ENGINEERING_REGRESSION_ONLY","performance_metrics_are_tuning_evidence":False,
          "windows":{x["window"]:x for x in eng},"engineering_clean":engineering_clean,
          "gap_through_invalidations_contained":sum(x["gap_through_invalidations"] for x in eng),
          "next_stage":"MICRO100_ENGINEERING_GATE" if engineering_clean else "ENGINEERING_REMEDIATION_REQUIRED"}
mic_gate={"version":"HarmonyBot V34.0","purpose":"USD100_MICRO_CAPITAL_ENGINEERING_ONLY","performance_metrics_are_tuning_evidence":False,
          "windows":{x["window"]:x for x in mic},"micro_clean":micro_clean,"micro_operational":micro_operational,
          "total_baskets":micro_baskets,"micro_mode_baskets":micro_mode_baskets,
          "next_stage":"FRESH_VALIDATION_DATA_GOVERNANCE" if engineering_clean and micro_operational else "MICRO_CAPITAL_REMEDIATION_REQUIRED"}
decision={"version":"HarmonyBot V34.0","engineering_clean":engineering_clean,"micro100_operational":micro_operational,
          "fresh_performance_validation_run":False,
          "final_status":"READY_TO_PROVE_UNUSED_VALIDATION_RANGE" if engineering_clean and micro_operational else
                         ("ENGINEERING_REMEDIATION_REQUIRED" if not engineering_clean else "MICRO_CAPITAL_NOT_YET_VIABLE"),
          "note":"DEV-A/B/C and MICRO100 A/B/C are exposed engineering data; no commercial performance conclusion is permitted."}
(o/"ENGINEERING_CLEAN_GATE.json").write_text(json.dumps(eng_gate,indent=2))
(o/"MICRO_100_GATE.json").write_text(json.dumps(mic_gate,indent=2))
(o/"V34_STAGE_DECISION.json").write_text(json.dumps(decision,indent=2))
print(json.dumps(decision,indent=2))
PY

progress "COMPLETE all engineering and micro gates"
