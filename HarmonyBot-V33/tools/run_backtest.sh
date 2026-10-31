#!/usr/bin/env bash
set -euo pipefail
: "${CTRADER_PASSWORD:?}"; : "${CTRADER_CTID:?}"; : "${CTRADER_ACCOUNT:?}"
: "${RUN_NAME:?}"; : "${START_DATE:?}"; : "${END_DATE:?}"; : "${EVAL_DATE:?}"
ALGO="${ALGO:-seal/algo/HarmonyBot_V33_Internal.algo}"
mkdir -p seal/{reports,logs,data}; printf '%s' "$CTRADER_PASSWORD" > seal/ctrader.pwd; chmod 600 seal/ctrader.pwd
docker pull ghcr.io/spotware/ctrader-console:5.9.11 >/dev/null
docker run --rm -v "$PWD/seal:/work" ghcr.io/spotware/ctrader-console:5.9.11 accounts --ctid="$CTRADER_CTID" --pwd-file=/work/ctrader.pwd > seal/accounts.json
ACCT=$(python3 - <<'PY'
import json,os
a=json.load(open('seal/accounts.json',encoding='utf-8-sig')); e=os.environ['CTRADER_ACCOUNT'].strip()
m=next((x for x in a if str(x.get('Number',''))==e or str(x.get('Id',''))==e),None)
if not m or m.get('Broker','').lower()!='fxpro' or m.get('Live') is not False or m.get('DepositCurrency')!='USD' or int(m.get('Leverage',0))!=500: raise SystemExit('FxPro demo USD 1:500 mismatch')
print(m['Number'])
PY
)
CNAME="v33-$(echo "$RUN_NAME"|tr '[:upper:]_' '[:lower:]-')-$GITHUB_RUN_ID"
docker run --name "$CNAME" -v "$PWD/seal:/work" ghcr.io/spotware/ctrader-console:5.9.11 backtest "/work/${ALGO#seal/}"  --ctid="$CTRADER_CTID" --pwd-file=/work/ctrader.pwd --account="$ACCT" --symbol=XAUUSD --period=m1  --start="$START_DATE" --end="$END_DATE" --balance=10000 --data-mode=m1 --data-dir=/work/data --commission=35 --spread=1  --SymbolName=XAUUSD --TradingEnabled=true --BasketRiskPercent=1.0 --MaxDrawdownPercent=10 --DailyLossLimitPercent=3  --MaxSpreadPips=60 --RoundTurnCommissionPips=0.5 --SlippageStressPips=0.3 --MinimumNetRR=2.0 --MinStopLossPips=10 --MinFreeMarginRiskMultiple=5  --M15SwingDepth=3 --M15SwingLookback=320 --H1SwingDepth=3 --H4SwingDepth=2 --PortfolioMaxCandidates=8 --CandidateTtlM15Bars=8  --MinGeometryQuality=0.55 --MinPrzConfluence=0.55 --GridCancelMfeR=0.50 --NoMfeProofR=0.15 --NoMfeKillR=0.80 --NoMfeMinAgeMinutes=3  --BreakEvenTriggerR=1.0 --BreakEvenLockR=0.10 --TrailTriggerR=1.50 --TrailDistanceR=0.75 --EvaluationStartUtcIso="$EVAL_DATE"  --report="/work/reports/$RUN_NAME.html" --report-json="/work/reports/$RUN_NAME.json" --exit-on-stop > "seal/logs/$RUN_NAME.log" 2>&1 &
PID=$!; DONE=0
for ((i=0;i<14400;i+=5)); do
 if test -s "seal/reports/$RUN_NAME.json" && python3 - <<PY
import json
m=json.load(open("seal/reports/$RUN_NAME.json",encoding="utf-8-sig")).get("main",{})
raise SystemExit(0 if "endingEquity" in m and "netProfit" in m else 1)
PY
 then DONE=1; break; fi
 if ! kill -0 "$PID" 2>/dev/null; then break; fi; sleep 5
done
docker stop --time 3 "$CNAME" >/dev/null 2>&1 || true; docker rm -f "$CNAME" >/dev/null 2>&1 || true; wait "$PID" 2>/dev/null || true
rm -f seal/ctrader.pwd seal/accounts.json
test "$DONE" = 1 || { tail -300 "seal/logs/$RUN_NAME.log" || true; exit 20; }
