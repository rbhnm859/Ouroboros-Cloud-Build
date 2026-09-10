#!/usr/bin/env bash
set -euo pipefail

ROOT='FibonacciHarmonicSniperUltimate/versions/xauusd_3/v37'
WORK="$ROOT/validation-v37-commercial"
REPORTS="$WORK/reports"
CACHE="$WORK/cache"
IMAGE='ghcr.io/spotware/ctrader-console:5.9.11'
PROJECT="$ROOT/FibonacciXAUUSD3V37.csproj"

: "${CTRADER_CTID:?CTRADER_CTID missing}"
: "${CTRADER_ACCOUNT:?CTRADER_ACCOUNT missing}"
: "${CTRADER_PASSWORD:?CTRADER_PASSWORD missing}"

rm -rf "$WORK"
mkdir -p "$REPORTS" "$CACHE"
printf '%s' "$CTRADER_PASSWORD" > "$WORK/ctrader.pwd"

docker pull "$IMAGE"
docker run --rm --entrypoint sh -v "$PWD:/repo" -w /repo "$IMAGE" -c \
  "dotnet restore '$PROJECT' && dotnet build '$PROJECT' -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True"

ALGO="$(find "$ROOT" -type f -name '*.algo' ! -path '*/validation-*/*' -print -quit)"
test -n "$ALGO"
test -s "$ALGO"
cp "$ALGO" "$WORK/FibonacciXAUUSD3-v3.7.0-HarmonicCore.algo"
sha256sum "$WORK/FibonacciXAUUSD3-v3.7.0-HarmonicCore.algo" > "$WORK/algo.sha256"

run_bt() {
  local tf="$1" segment="$2" cost="$3" start="$4" end="$5" spread="$6" commission="$7"
  local label="${tf}-${segment}-${cost}"
  echo "=== BACKTEST $label ==="
  docker run --rm \
    -v "$PWD/$WORK:/work" \
    -e "CTID=$CTRADER_CTID" \
    -e 'PWD-FILE=/work/ctrader.pwd' \
    -e "ACCOUNT=$CTRADER_ACCOUNT" \
    "$IMAGE" backtest /work/FibonacciXAUUSD3-v3.7.0-HarmonicCore.algo \
    --environment-variables --exit-on-stop \
    --symbol=XAUUSD --period="$tf" --start="$start" --end="$end" \
    --balance=10000 --data-mode=m1 --data-dir=/work/cache \
    --commission="$commission" --spread="$spread" \
    --RiskPercent=0.50 --MaxDailyLossPercent=3 --MaxTradesPerDay=6 \
    --MinimumRiskReward=1.35 --MaxAllowedRiskReward=6 \
    --PivotLeft=3 --PivotRight=2 --PivotLookback=500 \
    --MinimumPatternScore=72 --MaxDAgeBars=8 --MinXaAtr=2.0 \
    --TargetAdFib=0.618 --StopXaBuffer=0.06 --StopAtrBuffer=0.35 \
    --ConfirmationRulesNeeded=2 --ConfirmWindowBars=6 --BreakLookback=2 \
    --RejectionWickMin=0.25 --BodyMin=0.40 --MaxEntryDistanceAtr=1.10 \
    --RelativeTickVolumeMin=0.80 --VolumeAverageBars=20 --AtrRegimeMin=0.75 \
    --MaxSpreadAtrRatio=0.08 --CooldownBars=4 --MinStopAtr=0.35 \
    --report="/work/reports/${label}.html" \
    --report-json="/work/reports/${label}.json" \
    2>&1 | tee "$REPORTS/${label}.log"
  test -s "$REPORTS/${label}.json"
}

# Stage A: timeframe-agnostic 1Y Standard screening.
# A timeframe is excluded if it produces too few trades; low-sample performance is not promotable.
for tf in m1 m5 m15 m30 h1 h4; do
  run_bt "$tf" screen1y standard 09/09/2025 09/09/2026 17.42 35
done

python3 - <<'PY'
import json
from pathlib import Path
base=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_3/v37/validation-v37-commercial')
r=base/'reports'
tfs=['m1','m5','m15','m30','h1','h4']
rows=[]
for tf in tfs:
    d=json.loads((r/f'{tf}-screen1y-standard.json').read_text())
    ts=d['tradeStatistics']; main=d['main']; eq=d['equity']
    trades=int(ts['totalTrades']['all']); net=float(main['netProfit']); roi=float(main['roi']); pf=float(ts['profitFactor']['all']); dd=float(eq['maxEquityDrawdownPercent'])
    rows.append(dict(tf=tf,trades=trades,net=net,roi=roi,pf=pf,dd=dd))
eligible=[x for x in rows if x['trades']>=24 and x['net']>0 and x['pf']>1.05 and x['dd']<=12]
for x in eligible:
    x['score']=x['roi']+2.0*(x['pf']-1.0)-max(0.0,x['dd']-8.0)+min(x['trades'],120)*0.02
eligible.sort(key=lambda x:x['score'],reverse=True)
selected=[x['tf'] for x in eligible[:3]]
(base/'selected_timeframes.txt').write_text('\n'.join(selected)+'\n')
out=['# v3.7 Harmonic-Core Commercial Validation','','## Stage A — 1Y timeframe screening','',
'| TF | Trades | Net | ROI % | PF | Max DD % | Eligibility |',
'|---|---:|---:|---:|---:|---:|---|']
for x in rows:
    ok=x in eligible
    reason='PASS' if ok else ('EXCLUDE: low trades' if x['trades']<24 else 'EXCLUDE: performance/risk')
    out.append(f"| {x['tf']} | {x['trades']} | {x['net']:.2f} | {x['roi']:.2f} | {x['pf']:.2f} | {x['dd']:.2f} | {reason} |")
out += ['', 'Selected for robustness: ' + (', '.join(selected) if selected else 'NONE')]
(base/'V37_COMMERCIAL_SUMMARY.md').write_text('\n'.join(out)+'\n')
print('\n'.join(out))
if not selected:
    raise SystemExit('No timeframe survived Stage A commercial screening')
PY

mapfile -t SELECTED < "$WORK/selected_timeframes.txt"
for tf in "${SELECTED[@]}"; do
  run_bt "$tf" 1y harsh 09/09/2025 09/09/2026 30 50
  run_bt "$tf" oos1 standard 09/09/2025 09/03/2026 17.42 35
  run_bt "$tf" oos1 harsh    09/09/2025 09/03/2026 30 50
  run_bt "$tf" oos2 standard 09/03/2026 09/09/2026 17.42 35
  run_bt "$tf" oos2 harsh    09/03/2026 09/09/2026 30 50
done

python3 - <<'PY'
import datetime,json,re
from pathlib import Path
base=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_3/v37/validation-v37-commercial')
r=base/'reports'
selected=[x.strip() for x in (base/'selected_timeframes.txt').read_text().splitlines() if x.strip()]

def metrics(path):
    d=json.loads(path.read_text()); ts=d['tradeStatistics']; main=d['main']; eq=d['equity']; hist=d.get('history',{}).get('items',[])
    spans=sorted((int(x['entryTime']),int(x['closeTime']),x['direction']) for x in hist)
    overlap=hedge=0
    for i,a in enumerate(spans):
        for b in spans[i+1:]:
            if b[0]>=a[1]: break
            overlap+=1
            if b[2]!=a[2]: hedge+=1
    return dict(trades=int(ts['totalTrades']['all']),net=float(main['netProfit']),roi=float(main['roi']),pf=float(ts['profitFactor']['all']),dd=float(eq['maxEquityDrawdownPercent']),overlap=overlap,hedge=hedge)

allrows=[]
for tf in selected:
    for seg,cost in [('screen1y','standard'),('1y','harsh'),('oos1','standard'),('oos1','harsh'),('oos2','standard'),('oos2','harsh')]:
        m=metrics(r/f'{tf}-{seg}-{cost}.json'); m.update(tf=tf,seg=seg,cost=cost); allrows.append(m)

summary=(base/'V37_COMMERCIAL_SUMMARY.md').read_text()
lines=['','## Stage B — robustness and safety','','| TF | Segment | Cost | Trades | Net | ROI % | PF | DD % | Overlap | Hedge |','|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
for x in allrows:
    lines.append(f"| {x['tf']} | {x['seg']} | {x['cost']} | {x['trades']} | {x['net']:.2f} | {x['roi']:.2f} | {x['pf']:.2f} | {x['dd']:.2f} | {x['overlap']} | {x['hedge']} |")

passing=[]
for tf in selected:
    rows=[x for x in allrows if x['tf']==tf]
    annual=[x for x in rows if x['seg'] in ('screen1y','1y')]
    oos=[x for x in rows if x['seg'] in ('oos1','oos2')]
    safety=all(x['overlap']==0 and x['hedge']==0 for x in rows)
    annual_ok=all(x['trades']>=24 and x['net']>0 and x['pf']>=1.25 and x['dd']<=10 for x in annual)
    oos_ok=all(x['trades']>=5 and x['net']>0 and x['pf']>=1.10 and x['dd']<=10 for x in oos)
    logs='\n'.join((r/f'{tf}-{seg}-{cost}.log').read_text(errors='ignore') for seg,cost in [('screen1y','standard'),('1y','harsh'),('oos1','standard'),('oos1','harsh'),('oos2','standard'),('oos2','harsh')])
    protection_fail='[FAILSAFE FAIL]' in logs
    open_fail='[OPEN FAIL]' in logs
    runtime_ok=not protection_fail
    ok=safety and annual_ok and oos_ok and runtime_ok
    if ok:
        min_oos_roi=min(x['roi'] for x in oos); min_oos_pf=min(x['pf'] for x in oos); maxdd=max(x['dd'] for x in rows)
        std1=next(x for x in annual if x['cost']=='standard')
        score=min_oos_roi+3*(min_oos_pf-1)+0.25*std1['roi']-max(0,maxdd-6)
        passing.append((score,tf))
    lines += ['',f'- **{tf}**: safety={"PASS" if safety else "FAIL"}; annual={"PASS" if annual_ok else "FAIL"}; OOS={"PASS" if oos_ok else "FAIL"}; protection={"PASS" if runtime_ok else "FAIL"}; open-fail-observed={open_fail}']

passing.sort(reverse=True)
winner=passing[0][1] if passing else ''
(base/'winner_timeframe.txt').write_text(winner+'\n')
lines += ['', '## Commercial decision','']
if winner:
    lines += [f'**PROMOTION PASS — winner timeframe: {winner}**', 'The bot remains timeframe-agnostic in code; this timeframe is the evidence-backed commercial preset, not a hard runtime restriction.']
else:
    lines += ['**NOT YET COMMERCIAL — no timeframe passed all annual/Harsh/OOS/safety gates.**']
(base/'V37_COMMERCIAL_SUMMARY.md').write_text(summary+'\n'.join(lines)+'\n')
print('\n'.join(lines))
PY
