#!/usr/bin/env bash
set -euo pipefail
C="$PWD/control"; W="$C/HarmonyBot-V35/work"; O="$C/HarmonyBot-V35/output"
rm -rf "$W" "$O"; mkdir -p "$W/seal/algo" "$O/raw-logs"
STAGE="BOOT"
progress(){ printf '%s [V35-PROGRESS] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$O/RUN_PROGRESS.log"; }
trap 'rc=$?; if [ "$rc" -ne 0 ]; then progress "FAILED stage=${STAGE:-unknown} rc=$rc"; fi' EXIT
cd "$C"
progress "START V35 architecture ablation"
python3 HarmonyBot-V35/tools/static_audit.py HarmonyBot-V35/src/HarmonyBotV35.cs
cp V35_ARCHITECTURE_AUDIT.json "$O/"
dotnet restore HarmonyBot-V35/HarmonyBotV35.csproj
dotnet build HarmonyBot-V35/HarmonyBotV35.csproj -c Release --no-restore --nologo 2>&1 | tee "$O/V35_BUILD.log"
! grep -Eq '(^|[^0-9])error (CS|MSB|NETSDK)[0-9]+' "$O/V35_BUILD.log"
ALGO=$(find HarmonyBot-V35/bin/Release -type f -name '*.algo' | head -1); test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" "$W/seal/algo/HarmonyBot_V35_RegimeAware_Research_RC.algo"
cp HarmonyBot-V35/src/HarmonyBotV35.cs "$O/"
sha256sum HarmonyBot-V35/src/HarmonyBotV35.cs "$ALGO" > "$O/SHA256SUMS"
printf '%s\n' "$GITHUB_SHA" > "$O/SOURCE_COMMIT.txt"

run(){
 local family=$1 suffix=$2 st=$3 ev=$4 en=$5 bal=$6 q=$7 r=$8 c=$9 cap=${10}
 local n="V35-${family}-${suffix}" w="${family}-${suffix}"
 STAGE="$n"; progress "START stage=$n balance=$bal q=$q r=$r c=$c cap=$cap"
 (cd "$W"; RUN_NAME="$n" START_DATE="$st" EVAL_DATE="$ev" END_DATE="$en" BALANCE="$bal"     QUALITY="$q" REGIME="$r" CONFIRM="$c" CAPITAL_GATE="$cap" BACKTEST_TIMEOUT_SECONDS=2700     "$C/HarmonyBot-V35/tools/run_backtest.sh")
 python3 "$C/HarmonyBot-V35/tools/audit_report.py" --report "$W/seal/reports/$n.json" --log "$W/seal/logs/$n.log"     --out "$O/$w.json" --window "$suffix" --family "$family" --years .5 --balance "$bal"
 cp "$W/seal/logs/$n.log" "$O/raw-logs/$n.log"
 progress "DONE stage=$n"
}
dev_family(){
 local fam=$1 q=$2 r=$3 c=$4 cap=$5
 run "$fam" A 04/01/2021 2021-01-11T00:00:00Z 30/06/2021 10000 "$q" "$r" "$c" "$cap"
 run "$fam" B 01/07/2021 2021-07-08T00:00:00Z 31/12/2021 10000 "$q" "$r" "$c" "$cap"
 run "$fam" C 03/01/2022 2022-01-10T00:00:00Z 30/06/2022 10000 "$q" "$r" "$c" "$cap"
}
dev_family BASE_V34 false false false false
dev_family QUALITY_ONLY true false false false
dev_family REGIME_ONLY false true false false
dev_family CONFIRM_ONLY false false true false
dev_family FULL_V35 true true true true

# Micro feasibility is engineering/development evidence only.
run MICRO_FULL A 04/01/2021 2021-01-11T00:00:00Z 30/06/2021 100 true true true true
run MICRO_FULL B 01/07/2021 2021-07-08T00:00:00Z 31/12/2021 100 true true true true
run MICRO_FULL C 03/01/2022 2022-01-10T00:00:00Z 30/06/2022 100 true true true true

STAGE="GATE"; progress "START stage=GATE"
python3 - "$O" <<'PY'
import json,pathlib,sys
o=pathlib.Path(sys.argv[1]); families=["BASE_V34","QUALITY_ONLY","REGIME_ONLY","CONFIRM_ONLY","FULL_V35"]
def read(f,w): return json.load(open(o/f"{f}-{w}.json"))
summary={}
for f in families:
 xs=[read(f,w) for w in "ABC"]
 gp=sum(x["gross_profit"] for x in xs); gl=sum(x["gross_loss"] for x in xs)
 n=sum(x["baskets"] for x in xs); net=sum(x["net"] for x in xs)
 clean=all(x["engineering_clean"] and x["broker_profile_present"] and x["summary_present"] for x in xs)
 positive=sum(1 for x in xs if x["net"]>=0)
 pf=gp/gl if gl else (999 if gp else 0)
 exp=net/n if n else 0
 advance=clean and n>=30 and pf>1 and net>0 and exp>0 and positive>=2 and max(x["max_dd_pct"] for x in xs)<=10
 summary[f]={"baskets":n,"pf":pf,"net":net,"expectancy":exp,"positive_windows":positive,
             "worst_window_pf":min(x["pf"] for x in xs),"max_dd_pct":max(x["max_dd_pct"] for x in xs),
             "engineering_clean":clean,"advance":advance,
             "alpha_rejections":{"quality":sum(x["quality_rejected"] for x in xs),
                                 "regime":sum(x["regime_rejected"] for x in xs),
                                 "confirmation":sum(x["confirmation_rejected"] for x in xs),
                                 "capital_infeasible":sum(x["capital_infeasible"] for x in xs)}}
survivors=[(v["worst_window_pf"],v["pf"],k) for k,v in summary.items() if v["advance"] and k!="BASE_V34"]
survivors.sort(reverse=True)
winner=survivors[0][2] if survivors else None
mic=[read("MICRO_FULL",w) for w in "ABC"]
micro={"baskets":sum(x["baskets"] for x in mic),"capital_infeasible":sum(x["capital_infeasible"] for x in mic),
       "capital_rejected_baskets":sum(x["capital_rejected_baskets"] for x in mic),
       "micro_mode_baskets":sum(x["micro_mode_baskets"] for x in mic),
       "engineering_clean":all(x["engineering_clean"] for x in mic)}
out={"version":"HarmonyBot V35.0","purpose":"EXPOSED_DEVELOPMENT_ARCHITECTURE_ABLATION_ONLY",
     "fresh_2020H1_used_for_tuning":False,"families":summary,"micro100_engineering":micro,
     "development_candidate":winner,
     "final_status":"CANDIDATE_READY_FOR_FRESH_VALIDATION_RESERVATION" if winner else "ALPHA_ARCHITECTURE_LIMITATION",
     "next_stage":"PROVE_AND_RESERVE_NEW_FRESH_VALIDATION_RANGE" if winner else "REASSESS_ALPHA_HYPOTHESIS_WITHOUT_USING_VALIDATION_DATA"}
(o/"V35_DEVELOPMENT_DECISION.json").write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
PY
progress "COMPLETE V35 architecture ablation"
