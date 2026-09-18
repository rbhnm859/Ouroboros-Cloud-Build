#!/usr/bin/env bash
set -euo pipefail
C="$PWD/control"; W="$C/HarmonyBot-V35.1/work"; O="$C/HarmonyBot-V35.1/output"
rm -rf "$W" "$O"; mkdir -p "$W/seal/algo" "$O/raw-logs"
STAGE="BOOT"
progress(){ printf '%s [V351-PROGRESS] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$O/RUN_PROGRESS.log"; }
trap 'rc=$?; if [ "$rc" -ne 0 ]; then progress "FAILED stage=${STAGE:-unknown} rc=$rc"; fi' EXIT
cd "$C"; progress "START V35.1 monotonic veto ablation"
python3 HarmonyBot-V35.1/tools/static_audit.py HarmonyBot-V35.1/src/HarmonyBotV351.cs
cp V351_ARCHITECTURE_AUDIT.json "$O/"
cp HarmonyBot-V35.1/docs/ROOT_CAUSE_ATTRIBUTION.md "$O/"
dotnet restore HarmonyBot-V35.1/HarmonyBotV351.csproj
dotnet build HarmonyBot-V35.1/HarmonyBotV351.csproj -c Release --no-restore --nologo 2>&1 | tee "$O/V351_BUILD.log"
! grep -Eq '(^|[^0-9])error (CS|MSB|NETSDK)[0-9]+' "$O/V351_BUILD.log"
ALGO=$(find HarmonyBot-V35.1/bin/Release -type f -name '*.algo' | head -1); test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" "$W/seal/algo/HarmonyBot_V351_MonotonicAlpha_Research_RC.algo"
sha256sum HarmonyBot-V35.1/src/HarmonyBotV351.cs "$ALGO" > "$O/SHA256SUMS"
printf '%s\n' "$GITHUB_SHA" > "$O/SOURCE_COMMIT.txt"
run(){
 local fam=$1 suf=$2 st=$3 ev=$4 en=$5 tr=$6 ex=$7 mv=$8
 local n="V351-${fam}-${suf}" w="${fam}-${suf}"
 STAGE="$n"; progress "START stage=$n transition=$tr exhaustion=$ex m1veto=$mv"
 (cd "$W"; RUN_NAME="$n" START_DATE="$st" EVAL_DATE="$ev" END_DATE="$en" BALANCE=10000  TRANSITION="$tr" EXHAUSTION="$ex" M1VETO="$mv" BACKTEST_TIMEOUT_SECONDS=2700 "$C/HarmonyBot-V35.1/tools/run_backtest.sh")
 python3 "$C/HarmonyBot-V35.1/tools/audit_report.py" --report "$W/seal/reports/$n.json" --log "$W/seal/logs/$n.log"  --out "$O/$w.json" --window "$suf" --family "$fam" --years .5 --balance 10000
 cp "$W/seal/logs/$n.log" "$O/raw-logs/$n.log"; progress "DONE stage=$n"
}
family(){
 local fam=$1 tr=$2 ex=$3 mv=$4
 run "$fam" A 04/01/2021 2021-01-11T00:00:00Z 30/06/2021 "$tr" "$ex" "$mv"
 run "$fam" B 01/07/2021 2021-07-08T00:00:00Z 31/12/2021 "$tr" "$ex" "$mv"
 run "$fam" C 03/01/2022 2022-01-10T00:00:00Z 30/06/2022 "$tr" "$ex" "$mv"
}
family BASE_V34 false false false
family TRANSITION_VETO_ONLY true false false
family EXHAUSTION_VETO_ONLY false true false
family M1_VETO_ONLY false false true
family FULL_V351 true true true

STAGE="GATE"; progress "START stage=GATE"
python3 - "$O" <<'PY'
import json,pathlib,sys
o=pathlib.Path(sys.argv[1]); fams=["BASE_V34","TRANSITION_VETO_ONLY","EXHAUSTION_VETO_ONLY","M1_VETO_ONLY","FULL_V351"]
def read(f,w): return json.load(open(o/f"{f}-{w}.json"))
def agg(f):
 xs=[read(f,w) for w in "ABC"]; gp=sum(x["gross_profit"] for x in xs); gl=sum(x["gross_loss"] for x in xs)
 n=sum(x["baskets"] for x in xs); net=sum(x["net"] for x in xs); pf=gp/gl if gl else (999 if gp else 0)
 return {"baskets":n,"pf":pf,"net":net,"expectancy":net/n if n else 0,
 "positive_windows":sum(x["net"]>=0 for x in xs),"worst_window_pf":min(x["pf"] for x in xs),
 "max_dd_pct":max(x["max_dd_pct"] for x in xs),
 "engineering_clean":all(x["engineering_clean"] and x["broker_profile_present"] and x["summary_present"] for x in xs),
 "transition_veto_events":sum(x["transition_veto_events"] for x in xs),
 "exhaustion_veto_events":sum(x["exhaustion_veto_events"] for x in xs),
 "m1_veto_events":sum(x["m1_veto_events"] for x in xs)}
a={f:agg(f) for f in fams}; b=a["BASE_V34"]
for f,v in a.items():
 if f=="BASE_V34": v["relative_advance"]=False; continue
 enough=v["baskets"]>=max(30,int(.70*b["baskets"]))
 v["relative_advance"]=(v["engineering_clean"] and enough and v["net"]>0 and
   v["pf"]>b["pf"] and v["expectancy"]>b["expectancy"] and
   v["worst_window_pf"]>=b["worst_window_pf"] and
   v["positive_windows"]>=b["positive_windows"] and v["max_dd_pct"]<=10)
cands=[(v["worst_window_pf"],v["pf"],v["expectancy"],f) for f,v in a.items() if v["relative_advance"]]
cands.sort(reverse=True); winner=cands[0][3] if cands else None
out={"version":"HarmonyBot V35.1","purpose":"EXPOSED_DEV_MONOTONIC_VETO_ABLATION_ONLY",
"base":"BASE_V34","families":a,"development_candidate":winner,
"final_status":"CANDIDATE_READY_FOR_NEW_FRESH_VALIDATION_RESERVATION" if winner else "NO_RELATIVE_ALPHA_IMPROVEMENT",
"next_stage":"CAPITAL_COMPATIBILITY_STUDY_THEN_NEW_FRESH_VALIDATION_GOVERNANCE" if winner else "REASSESS_ALPHA_HYPOTHESIS_WITHOUT_USING_2020H1"}
(o/"V351_DEVELOPMENT_DECISION.json").write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
PY
progress "COMPLETE V35.1 monotonic veto ablation"
