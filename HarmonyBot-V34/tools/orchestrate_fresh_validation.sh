#!/usr/bin/env bash
set -euo pipefail
C="$PWD/control"; W="$C/HarmonyBot-V34/validation-work"; O="$C/HarmonyBot-V34/validation-output"
rm -rf "$W" "$O"
mkdir -p "$W/seal/algo" "$O/raw-logs"
progress(){ printf '%s [V34-VAL-PROGRESS] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$O/RUN_PROGRESS.log"; }
STAGE="BOOT"
trap 'rc=$?; if [ "$rc" -ne 0 ]; then progress "FAILED stage=${STAGE:-unknown} rc=$rc"; fi' EXIT

cd "$C"
progress "START preregistered fresh validation"
cp HarmonyBot-V34/validation/DATA_EXPOSURE_LEDGER_V34.json "$O/"
cp HarmonyBot-V34/validation/VALIDATION_RESERVATION.md "$O/"

STAGE="SOURCE_FREEZE"
EXPECTED_BLOB="f404767c70bdf5032b8d5c1fc2be9e81b9a97947"
ACTUAL_BLOB="$(git hash-object HarmonyBot-V34/src/HarmonyBotV34.cs)"
printf 'engineering_commit=%s\nexpected_source_blob=%s\nactual_source_blob=%s\n'   "bf277db05ce303a3e1184b6be8b28868cbe9e69a" "$EXPECTED_BLOB" "$ACTUAL_BLOB" | tee "$O/SOURCE_FREEZE.txt"
test "$ACTUAL_BLOB" = "$EXPECTED_BLOB"

python3 HarmonyBot-V34/tools/static_audit.py HarmonyBot-V34/src/HarmonyBotV34.cs
cp V34_ARCHITECTURE_AUDIT.json "$O/"
dotnet restore HarmonyBot-V34/HarmonyBotV34.csproj
dotnet build HarmonyBot-V34/HarmonyBotV34.csproj -c Release --no-restore --nologo 2>&1 | tee "$O/V34_VALIDATION_BUILD.log"
ALGO=$(find HarmonyBot-V34/bin/Release -type f -name '*.algo' | head -1)
test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" "$W/seal/algo/HarmonyBot_V34_Internal.algo"
sha256sum HarmonyBot-V34/src/HarmonyBotV34.cs "$ALGO" > "$O/SHA256SUMS"

run(){
  local n=$1 w=$2 bal=$3
  STAGE="$n"; progress "START stage=$n window=$w balance=$bal"
  (
    cd "$W"
    RUN_NAME="$n" START_DATE="02/01/2020" EVAL_DATE="2020-01-09T00:00:00Z" END_DATE="30/06/2020"       BALANCE="$bal" BACKTEST_TIMEOUT_SECONDS=2700 "$C/HarmonyBot-V34/tools/run_backtest.sh"
  )
  python3 "$C/HarmonyBot-V34/tools/audit_report.py"     --report "$W/seal/reports/$n.json" --log "$W/seal/logs/$n.log"     --out "$O/$w.json" --window "$w" --years 0.5 --balance "$bal"
  cp "$W/seal/logs/$n.log" "$O/raw-logs/$n.log"
  progress "DONE stage=$n"
}

run V34-FRESH-VAL-NORMAL FRESH-VAL-NORMAL 10000
run V34-FRESH-VAL-MICRO100 FRESH-VAL-MICRO100 100

STAGE="GATE"; progress "START stage=GATE"
python3 - "$O" <<'PY'
import json,pathlib,sys
o=pathlib.Path(sys.argv[1])
normal=json.load(open(o/"FRESH-VAL-NORMAL.json"))
micro=json.load(open(o/"FRESH-VAL-MICRO100.json"))
def classify(x):
    integrity=(x.get("engineering_clean") and x.get("broker_profile_present") and
               x.get("summary_present") and x.get("basket_activity_present"))
    if not integrity:
        return "ENGINEERING_INVALID"
    if x.get("baskets",0) < 10:
        return "INSUFFICIENT_SAMPLE"
    passed=(x.get("pf",0)>1.0 and x.get("net",0)>0 and x.get("expectancy",0)>0 and
            x.get("max_dd_pct",999)<=10.0)
    return "PASS" if passed else "FAIL"
ns=classify(normal); ms=classify(micro)
if "ENGINEERING_INVALID" in (ns,ms):
    final="VALIDATION_ENGINEERING_INVALID"
elif "INSUFFICIENT_SAMPLE" in (ns,ms):
    final="VALIDATION_INSUFFICIENT_SAMPLE"
elif ns=="PASS" and ms=="PASS":
    final="FRESH_VALIDATION_PASS"
elif ns=="FAIL":
    final="ALPHA_NOT_VALIDATED"
else:
    final="NORMAL_PASS_MICRO_VALIDATION_FAIL"
gate={
 "version":"HarmonyBot V34.0",
 "reservation_id":"V34-VAL-FRESH-2020H1",
 "source_blob":"f404767c70bdf5032b8d5c1fc2be9e81b9a97947",
 "date_range":"2020-01-02..2020-06-30",
 "retuning_from_validation_forbidden":True,
 "normal":{"status":ns,"metrics":normal},
 "micro100":{"status":ms,"metrics":micro},
 "final_status":final,
 "commercial_target_assessment":False,
 "next_stage":("RESERVE_FRESH_OOS_AND_ROBUSTNESS" if final=="FRESH_VALIDATION_PASS"
               else "DO_NOT_TUNE_ON_VALIDATION; ASSESS_ALPHA_ARCHITECTURE_OR_SAMPLE_ADEQUACY")
}
(o/"FRESH_VALIDATION_GATE.json").write_text(json.dumps(gate,indent=2))
print(json.dumps(gate,indent=2))
PY
progress "COMPLETE preregistered fresh validation"
