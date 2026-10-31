#!/usr/bin/env bash
set -euo pipefail
C="$PWD/control"; W="$C/HarmonyBot-V33/work"; O="$C/HarmonyBot-V33/output"; mkdir -p "$W/seal/algo" "$O"
cd "$C"; python3 HarmonyBot-V33/tools/static_audit.py HarmonyBot-V33/src/HarmonyBotV33.cs; cp V33_ARCHITECTURE_AUDIT.json "$O/"
dotnet restore HarmonyBot-V33/HarmonyBotV33.csproj
dotnet build HarmonyBot-V33/HarmonyBotV33.csproj -c Release --no-restore --nologo 2>&1 | tee "$O/V33_BUILD.log"
ALGO=$(find HarmonyBot-V33/bin/Release -type f -name '*.algo'|head -1); test -s "$ALGO"; cp "$ALGO" "$W/seal/algo/HarmonyBot_V33_Internal.algo"
cp HarmonyBot-V33/src/HarmonyBotV33.cs "$O/"; sha256sum HarmonyBot-V33/src/HarmonyBotV33.cs "$ALGO" > "$O/SHA256SUMS"
run(){ local n=$1 w=$2 st=$3 ev=$4 en=$5; (cd "$W"; RUN_NAME="$n" START_DATE="$st" EVAL_DATE="$ev" END_DATE="$en" "$C/HarmonyBot-V33/tools/run_backtest.sh"); python3 "$C/HarmonyBot-V33/tools/audit_report.py" --report "$W/seal/reports/$n.json" --log "$W/seal/logs/$n.log" --out "$O/$w.json" --window "$w" --years .5; }
run V33-DEV-A DEV-A 04/01/2021 2021-01-11T00:00:00Z 30/06/2021
run V33-DEV-B DEV-B 01/07/2021 2021-07-08T00:00:00Z 31/12/2021
run V33-DEV-C DEV-C 03/01/2022 2022-01-10T00:00:00Z 30/06/2022
mkdir -p "$O/raw-logs"; cp "$W/seal/logs/"*.log "$O/raw-logs/" || true
python3 - "$O" <<'PY'
import json,pathlib,sys
o=pathlib.Path(sys.argv[1]); r=[json.load(open(o/f"DEV-{x}.json")) for x in "ABC"]
n=sum(x["baskets"] for x in r); gp=sum(max(x["net"],0) for x in r); # aggregate PF below recomputed from per-window PF is not exact, keep window gates primary
hard=all(x["baskets"]>0 and x["pf"]>1 and x["net"]>0 and x["expectancy"]>0 for x in r)
hard=hard and max(x["max_dd_pct"] for x in r)<=10 and sum(x["execution_errors"] for x in r)==0 and n/1.5>=50
hard=hard and sum(x["grid_risk_violations"]+x["duplicate_grid_legs"]+x["orphan_pending_orders"]+x["stop_widening_violations"] for x in r)==0
out={"version":"HarmonyBot V33.0","windows":{x["window"]:x for x in r},"total_baskets":n,"annualized_frequency":n/1.5,
"max_dd_pct":max(x["max_dd_pct"] for x in r),"execution_errors":sum(x["execution_errors"] for x in r),
"stop_widening_violations":sum(x["stop_widening_violations"] for x in r),"development_pass":hard,
"next_stage":"HOLD_DATA_GOVERNANCE" if hard else "STRATEGY_ARCHITECTURE_LIMITATION"}
(o/"DEVELOPMENT_GATE.json").write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
PY
