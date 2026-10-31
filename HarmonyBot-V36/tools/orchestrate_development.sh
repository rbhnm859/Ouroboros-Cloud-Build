#!/usr/bin/env bash
set -euo pipefail
C="$PWD/control"; W="$C/HarmonyBot-V36/work"; O="$C/HarmonyBot-V36/output"
rm -rf "$W" "$O"; mkdir -p "$W/seal/algo" "$O/raw-logs"
STAGE="BOOT"
progress(){ printf '%s [V36-PROGRESS] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$O/RUN_PROGRESS.log"; }
trap 'rc=$?; if [ "$rc" -ne 0 ]; then progress "FAILED stage=${STAGE:-unknown} rc=$rc"; fi' EXIT

cd "$C"
progress "START V36 high-frequency harmonic portfolio development"
python3 HarmonyBot-V36/tools/static_audit.py HarmonyBot-V36/src/HarmonyBotV36.cs
cp V36_ARCHITECTURE_AUDIT.json "$O/"
dotnet restore HarmonyBot-V36/HarmonyBotV36.csproj
dotnet build HarmonyBot-V36/HarmonyBotV36.csproj -c Release --no-restore --nologo 2>&1 | tee "$O/V36_BUILD.log"
! grep -Eq '(^|[^0-9])error (CS|MSB|NETSDK)[0-9]+' "$O/V36_BUILD.log"
ALGO=$(find HarmonyBot-V36/bin/Release -type f -name '*.algo' | head -1)
test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" "$W/seal/algo/HarmonyBot_V36_HighFrequency_Harmonic_Portfolio_RC.algo"
sha256sum HarmonyBot-V36/src/HarmonyBotV36.cs "$ALGO" > "$O/SHA256SUMS"
printf '%s\n' "$GITHUB_SHA" > "$O/SOURCE_COMMIT.txt"

run(){
 local fam=$1 suf=$2 st=$3 ev=$4 en=$5 ret=$6 aging=$7 recall=$8 ttl=$9 maxc=${10}
 local n="V36-${fam}-${suf}" w="${fam}-${suf}"
 STAGE="$n"
 progress "START stage=$n retention=$ret aging=$aging recall=$recall ttl=$ttl maxCandidates=$maxc"
 (cd "$W"; RUN_NAME="$n" START_DATE="$st" EVAL_DATE="$ev" END_DATE="$en" BALANCE=10000 \
   RETENTION="$ret" AGING="$aging" RECALL="$recall" TTL="$ttl" MAXCAND="$maxc" BACKTEST_TIMEOUT_SECONDS=2700 \
   "$C/HarmonyBot-V36/tools/run_backtest.sh")
 python3 "$C/HarmonyBot-V36/tools/audit_report.py" \
   --report "$W/seal/reports/$n.json" --log "$W/seal/logs/$n.log" --out "$O/$w.json" \
   --window "$suf" --family "$fam" --years .5 --balance 10000
 cp "$W/seal/logs/$n.log" "$O/raw-logs/$n.log"
 progress "DONE stage=$n"
}

family(){
 local fam=$1 ret=$2 aging=$3 recall=$4 ttl=$5 maxc=$6
 run "$fam" A 04/01/2021 2021-01-11T00:00:00Z 30/06/2021 "$ret" "$aging" "$recall" "$ttl" "$maxc"
 run "$fam" B 01/07/2021 2021-07-08T00:00:00Z 31/12/2021 "$ret" "$aging" "$recall" "$ttl" "$maxc"
 run "$fam" C 03/01/2022 2022-01-10T00:00:00Z 30/06/2022 "$ret" "$aging" "$recall" "$ttl" "$maxc"
}

# CONTROL must reproduce V35.1 EXHAUSTION_VETO_ONLY behavior before V36 promotion is allowed.
family CONTROL_V351 false false false 8 8
# Structural throughput family: keep valid armed candidates alive instead of destroying them when another basket wins arbitration.
family RETAINED_PORTFOLIO true true false 8 12
# Lifecycle family: same alpha, but gives valid candidates a longer opportunity to execute after temporary single-basket contention.
family LIFECYCLE_EXTENDED true true false 12 12
# Major recall family: bounded high-quality V34-rejected harmonics may be admitted only under strict non-conflict/context constraints.
family STRUCTURED_RECALL true true true 12 12

STAGE="FREQUENCY_FRONTIER"
progress "START stage=FREQUENCY_FRONTIER"
python3 - "$O" <<'PY'
import json,pathlib,sys,math
o=pathlib.Path(sys.argv[1])
fams=["CONTROL_V351","RETAINED_PORTFOLIO","LIFECYCLE_EXTENDED","STRUCTURED_RECALL"]
def read(f,w): return json.load(open(o/f"{f}-{w}.json"))
def agg(f):
 xs=[read(f,w) for w in "ABC"]
 gp=sum(x["gross_profit"] for x in xs); gl=sum(x["gross_loss"] for x in xs)
 n=sum(x["baskets"] for x in xs); net=sum(x["net"] for x in xs)
 pf=gp/gl if gl else (999 if gp else 0)
 return {
  "baskets":n,
  "executable_baskets_per_year":n/1.5,
  "pf":pf,
  "net":net,
  "expectancy":net/n if n else 0,
  "wins":sum(x["wins"] for x in xs),
  "losses":sum(x["losses"] for x in xs),
  "win_rate":sum(x["wins"] for x in xs)/n if n else 0,
  "positive_windows":sum(x["net"]>0 for x in xs),
  "worst_window_pf":min(x["pf"] for x in xs),
  "max_dd_pct":max(x["max_dd_pct"] for x in xs),
  "engineering_clean":all(x["engineering_clean"] and x["broker_profile_present"] and x["summary_present"] for x in xs),
  "scheduler_deferred":sum(x.get("scheduler_deferred",0) for x in xs),
  "scheduler_recovered_executions":sum(x.get("scheduler_recovered_executions",0) for x in xs),
  "structured_recall_admitted":sum(x.get("structured_recall_admitted",0) for x in xs),
  "mean_mfe_r":sum(x["mean_mfe_r"]*x["baskets"] for x in xs)/n if n else 0,
  "mean_mae_r":sum(x["mean_mae_r"]*x["baskets"] for x in xs)/n if n else 0,
  "windows":{w:read(f,w) for w in "ABC"}
 }
a={f:agg(f) for f in fams}; c=a["CONTROL_V351"]
# Control reproduction tolerance against confirmed V35.1 EXHAUSTION evidence.
c["control_reproduction"]={
 "expected_baskets":66,"expected_pf":1.1669391825879287,"expected_net":492.11,
 "basket_match":c["baskets"]==66,
 "pf_abs_delta":abs(c["pf"]-1.1669391825879287),
 "net_abs_delta":abs(c["net"]-492.11)
}
c["control_reproduction"]["pass"]=(c["baskets"]==66 and c["control_reproduction"]["pf_abs_delta"]<=0.01 and c["control_reproduction"]["net_abs_delta"]<=25.0 and c["engineering_clean"])
for f,v in a.items():
 v["frequency_multiple_vs_control"]=v["executable_baskets_per_year"]/c["executable_baskets_per_year"] if c["executable_baskets_per_year"] else 0
 v["robust_positive_edge"]=(v["engineering_clean"] and v["net"]>0 and v["expectancy"]>0 and v["pf"]>=1.0 and
                            v["positive_windows"]>=2 and v["worst_window_pf"]>=0.75 and v["max_dd_pct"]<=10)
 v["relative_frequency_advance"]=(f!="CONTROL_V351" and v["robust_positive_edge"] and
                                  v["executable_baskets_per_year"]>=1.25*c["executable_baskets_per_year"])
 v["major_breakthrough"]=(v["robust_positive_edge"] and
                          (v["executable_baskets_per_year"]>=100 or v["frequency_multiple_vs_control"]>=2.0))
eligible=[(v["executable_baskets_per_year"],v["worst_window_pf"],v["pf"],v["expectancy"],f)
          for f,v in a.items() if f!="CONTROL_V351" and v["relative_frequency_advance"]]
eligible.sort(reverse=True)
winner=eligible[0][-1] if eligible and c["control_reproduction"]["pass"] else None
frontier={
 "version":"HarmonyBot V36",
 "purpose":"EXPOSED_DEV_HIGH_FREQUENCY_ARCHITECTURE_ABLATION",
 "control":"CONTROL_V351",
 "families":a,
 "development_candidate":winner,
 "major_breakthrough":bool(winner and a[winner]["major_breakthrough"]),
 "status":"MAJOR_BREAKTHROUGH" if winner and a[winner]["major_breakthrough"] else ("RELATIVE_FREQUENCY_ADVANCE" if winner else "NO_PROMOTABLE_FREQUENCY_ADVANCE"),
 "fresh_validation_used":False,
 "evidence_scope":"DEV-A/B/C only; no fresh validation data used for tuning"
}
(o/"V36_FREQUENCY_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
(o/"V36_ARCHITECTURE_ABLATION.json").write_text(json.dumps(frontier,indent=2))
decision={
 "version":"HarmonyBot V36",
 "control_reproduction_pass":c["control_reproduction"]["pass"],
 "development_candidate":winner,
 "major_breakthrough":frontier["major_breakthrough"],
 "status":frontier["status"],
 "next_stage":"ALPHA_FREEZE_THEN_EXIT_RISK_AND_CAPITAL_COMPATIBILITY" if winner else "REASSESS_FREQUENCY_BOTTLENECKS_WITHOUT_FRESH_DATA",
 "do_not_use_fresh_for_tuning":True
}
(o/"V36_PROMOTION_DECISION.json").write_text(json.dumps(decision,indent=2))
print(json.dumps(frontier,indent=2))
print(json.dumps(decision,indent=2))
PY

# Build a machine-readable funnel summary from the raw logs without claiming rejected-trade expectancy that was not observed.
python3 - "$O" <<'PY'
import json,pathlib,re,sys
o=pathlib.Path(sys.argv[1])
families=["CONTROL_V351","RETAINED_PORTFOLIO","LIFECYCLE_EXTENDED","STRUCTURED_RECALL"]
out={"version":"HarmonyBot V36","scope":"DEV-A/B/C","families":{}}
for f in families:
 z={"detected":0,"validated":0,"routed":0,"prz":0,"confirming":0,"armed":0,"basket_planned":0,"executed":0,
    "rejected":0,"expired":0,"invalidated":0,"scheduler_deferred_events":0,"recall_admit_events":0}
 for w in "ABC":
  t=(o/"raw-logs"/f"V36-{f}-{w}.log").read_text(errors="ignore")
  for m in re.finditer(r"\[V36-PIPELINE\].*?detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+armed=(\d+)\s+basketPlanned=(\d+).*?executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)",t):
   vals=list(map(int,m.groups()))
   for k,v in zip(["detected","validated","routed","prz","confirming","armed","basket_planned","executed","expired","rejected","invalidated"],vals): z[k]+=v
  z["scheduler_deferred_events"]+=len(re.findall("SCHEDULER_DEFERRED_KEEP_ALIVE",t))
  z["recall_admit_events"]+=len(re.findall(r"\[V36-RECALL-ADMIT\]",t))
 out["families"][f]=z
(o/"V36_SIGNAL_TRADE_FUNNEL.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
PY

progress "COMPLETE V36 high-frequency architecture ablation"
