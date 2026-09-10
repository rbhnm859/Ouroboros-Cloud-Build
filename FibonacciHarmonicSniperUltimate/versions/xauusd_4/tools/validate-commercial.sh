#!/usr/bin/env bash
set -euo pipefail

ROOT='FibonacciHarmonicSniperUltimate/versions/xauusd_4'
WORK="$ROOT/validation-commercial"
REPORTS="$WORK/reports"
CACHE="$WORK/cache"
IMAGE='ghcr.io/spotware/ctrader-console:5.9.11'
V3='FibonacciHarmonicSniperUltimate/versions/xauusd_3/builds/FibonacciXAUUSD3-v3.6-Latest-Mobile.algo'

: "${CTRADER_CTID:?CTRADER_CTID missing}"
: "${CTRADER_ACCOUNT:?CTRADER_ACCOUNT missing}"
: "${CTRADER_PASSWORD:?CTRADER_PASSWORD missing}"

rm -rf "$WORK"
mkdir -p "$REPORTS" "$CACHE"
printf '%s' "$CTRADER_PASSWORD" > "$WORK/ctrader.pwd"

docker pull "$IMAGE"
docker run --rm --entrypoint sh -v "$PWD:/repo" -w /repo "$IMAGE" -c \
  "dotnet restore '$ROOT/FibonacciXAUUSD4.csproj' && dotnet build '$ROOT/FibonacciXAUUSD4.csproj' -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True"

ALGO="$(find "$ROOT" -type f -name '*.algo' ! -path '*/validation-*/*' -print -quit)"
test -n "$ALGO"
test -s "$ALGO"
cp "$ALGO" "$WORK/Fibonacci-Harmonic-Gold-Pro-v4.0.0.algo"
cp "$ROOT/src/FibonacciXAUUSD4.cs" "$WORK/FibonacciXAUUSD4.cs"
sha256sum "$WORK/Fibonacci-Harmonic-Gold-Pro-v4.0.0.algo" > "$WORK/algo.sha256"

test -s "$V3"
cp "$V3" "$WORK/FibonacciXAUUSD3-v3.6-Latest-Mobile.algo"

run_v4() {
  local variant="$1" period="$2" cost="$3" start="$4" end="$5" spread="$6" commission="$7"
  local score='64' geom='31' rr='1.50' harmonic='true' fib='true'
  case "$variant" in
    balanced) ;;
    strict) score='68'; geom='34' ;;
    harmonic) score='62'; geom='28'; fib='false' ;;
    frequency) score='60'; geom='28' ;;
    rr18) rr='1.80' ;;
    *) echo "Unknown variant $variant"; exit 2 ;;
  esac
  local label="v4-${variant}-${period}-${cost}"
  echo "=== $label ==="
  docker run --rm \
    -v "$PWD/$WORK:/work" \
    -e "CTID=$CTRADER_CTID" \
    -e 'PWD-FILE=/work/ctrader.pwd' \
    -e "ACCOUNT=$CTRADER_ACCOUNT" \
    "$IMAGE" backtest /work/Fibonacci-Harmonic-Gold-Pro-v4.0.0.algo \
    --environment-variables --exit-on-stop \
    --symbol=XAUUSD --period=m5 --start="$start" --end="$end" \
    --balance=10000 --data-mode=m1 --data-dir=/work/cache \
    --commission="$commission" --spread="$spread" \
    --RiskPercent=0.50 --MaxDailyLossPercent=3 --MaxTradesPerDay=8 --MaxConsecutiveLosses=3 \
    --MinimumRiskReward="$rr" --MaxAllowedRR=6 \
    --EnableHarmonics="$harmonic" --EnableFibPullback="$fib" \
    --FinalScoreMin="$score" --HarmonicGeometryMin="$geom" \
    --PivotLeft=2 --PivotRight=1 --PivotLookback=420 --MaxPatternAgeM15Bars=16 \
    --MinXaAtr=2.0 --MinImpulseAtr=1.2 --RatioTolerancePercent=8 \
    --PrzAtrHalfWidth=0.18 --MaxProjectionDispersionAtr=1.75 --TargetAdFib=0.618 \
    --FibShallow=0.50 --FibDeep=0.786 --StopFib=0.886 \
    --SlAtrBuffer=0.18 --MinStopAtr=0.20 --MaxSpreadAtrRatio=0.05 --MaxEntryDistanceAtr=0.45 --MarginSafetyPercent=85 \
    --CandidateLifeM5Bars=96 --CooldownM5Bars=9 --M5RulesNeeded=2 --M5BreakLookback=3 --M5WickMinRatio=0.22 --M5BodyMinRatio=0.42 \
    --BlockLondonEntries=true --BlockFridayLate=true --FridayBlockUtcHour=18 \
    --report="/work/reports/${label}.html" --report-json="/work/reports/${label}.json" \
    2>&1 | tee "$REPORTS/${label}.log"
  test -s "$REPORTS/${label}.json"
}

run_v3() {
  local period="$1" cost="$2" start="$3" end="$4" spread="$5" commission="$6"
  local label="v3.6-${period}-${cost}"
  echo "=== $label ==="
  docker run --rm \
    -v "$PWD/$WORK:/work" \
    -e "CTID=$CTRADER_CTID" \
    -e 'PWD-FILE=/work/ctrader.pwd' \
    -e "ACCOUNT=$CTRADER_ACCOUNT" \
    "$IMAGE" backtest /work/FibonacciXAUUSD3-v3.6-Latest-Mobile.algo \
    --environment-variables --exit-on-stop \
    --symbol=XAUUSD --period=m5 --start="$start" --end="$end" \
    --balance=10000 --data-mode=m1 --data-dir=/work/cache \
    --commission="$commission" --spread="$spread" \
    --RiskPercent=0.50 --MaxDailyLossPercent=3 --MinimumRiskReward=1.5 \
    --PreScoreMin=42 --FinalScoreMin=60 --M5PreScoreFloor=50 --M5RulesNeeded=2 \
    --MinImpulseAtr=1.2 --MinStopAtr=0.20 --MaxAllowedRR=8 --BuyH1MinScore=18 \
    --BlockLondonEntries=true --RequireH1AtrExpansion=true --H1AtrExpansionMin=1.15 \
    --report="/work/reports/${label}.html" --report-json="/work/reports/${label}.json" \
    2>&1 | tee "$REPORTS/${label}.log"
  test -s "$REPORTS/${label}.json"
}

# Architecture selection uses only the most recent 3M window.
for v in balanced strict harmonic frequency rr18; do
  run_v4 "$v" 3m standard 09/06/2026 09/09/2026 17.42 35
  run_v4 "$v" 3m harsh    09/06/2026 09/09/2026 30 50
done

python3 - <<'PY'
import json
from pathlib import Path
root=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_4/validation-commercial')
reports=root/'reports'
variants=['balanced','strict','harmonic','frequency','rr18']
rows=[]
for v in variants:
    pair=[]
    for cost in ['standard','harsh']:
        d=json.loads((reports/f'v4-{v}-3m-{cost}.json').read_text())
        ts=d['tradeStatistics']; main=d['main']; eq=d['equity']
        r={
            'cost':cost,
            'trades':int(ts['totalTrades']['all']),
            'roi':float(main['roi']),
            'net':float(main['netProfit']),
            'pf':float(ts['profitFactor']['all']),
            'dd':float(eq['maxEquityDrawdownPercent'])
        }
        pair.append(r)
    minroi=min(x['roi'] for x in pair)
    minpf=min(x['pf'] for x in pair)
    maxdd=max(x['dd'] for x in pair)
    mintrades=min(x['trades'] for x in pair)
    # Reward positive expectancy and adequate sample size; penalize DD above 6%.
    score=minroi + 2.0*(minpf-1.0) + min(mintrades,30)*0.04 - max(0.0,maxdd-6.0)*0.8
    viable=(minroi>0 and minpf>1.0 and mintrades>=5)
    rows.append((viable,score,v,pair))
rows.sort(key=lambda x:(x[0],x[1]),reverse=True)
winner=rows[0][2]
(root/'winner.txt').write_text(winner+'\n')
out=['# v4 3M Architecture Screen','', '| Variant | Cost | Trades | Net | ROI % | PF | DD % |','|---|---|---:|---:|---:|---:|---:|']
for viable,score,v,pair in rows:
    for r in pair:
        out.append(f"| {v} | {r['cost']} | {r['trades']} | {r['net']:.2f} | {r['roi']:.2f} | {r['pf']:.2f} | {r['dd']:.2f} |")
    out.append(f'<!-- {v}: viable={viable} rank_score={score:.3f} -->')
out += ['',f'**Selected architecture: {winner}**']
(root/'V4_COMMERCIAL_VALIDATION.md').write_text('\n'.join(out)+'\n')
print('\n'.join(out))
PY

WINNER="$(cat "$WORK/winner.txt")"

# Genuine out-of-sample block: nine months immediately BEFORE the 3M selection window.
run_v4 "$WINNER" oos9m standard 09/09/2025 09/06/2026 17.42 35
run_v4 "$WINNER" oos9m harsh    09/09/2025 09/06/2026 30 50

# Stability windows and full-year aggregate.
run_v4 "$WINNER" 6m standard 09/03/2026 09/09/2026 17.42 35
run_v4 "$WINNER" 6m harsh    09/03/2026 09/09/2026 30 50
run_v4 "$WINNER" 1y standard 09/09/2025 09/09/2026 17.42 35
run_v4 "$WINNER" 1y harsh    09/09/2025 09/09/2026 30 50

# Apples-to-apples commercial benchmark versus formal v3.6 on the same 1Y window/costs.
run_v3 1y standard 09/09/2025 09/09/2026 17.42 35
run_v3 1y harsh    09/09/2025 09/09/2026 30 50

python3 - <<'PY'
import datetime, json, math
from collections import defaultdict
from pathlib import Path
root=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_4/validation-commercial')
reports=root/'reports'
winner=(root/'winner.txt').read_text().strip()

def metrics(path):
    d=json.loads(path.read_text())
    ts=d['tradeStatistics']; main=d['main']; eq=d['equity']
    hist=d.get('history',{}).get('items',[])
    return d, {
        'trades':int(ts['totalTrades']['all']),
        'net':float(main['netProfit']),
        'roi':float(main['roi']),
        'pf':float(ts['profitFactor']['all']),
        'dd':float(eq['maxEquityDrawdownPercent']),
        'hist':hist
    }

rows=[]
for period in ['3m','oos9m','6m','1y']:
    for cost in ['standard','harsh']:
        _,m=metrics(reports/f'v4-{winner}-{period}-{cost}.json')
        rows.append((period,cost,m))
bench=[]
for cost in ['standard','harsh']:
    _,m=metrics(reports/f'v3.6-1y-{cost}.json')
    bench.append((cost,m))

# Safety audit on the full-year v4 histories.
safety=[]
for cost in ['standard','harsh']:
    _,m=metrics(reports/f'v4-{winner}-1y-{cost}.json')
    spans=sorted((int(x['entryTime']),int(x['closeTime']),x['direction']) for x in m['hist'])
    overlap=hedge=0
    for i,a in enumerate(spans):
        for b in spans[i+1:]:
            if b[0]>=a[1]: break
            overlap+=1
            hedge+=int(a[2]!=b[2])
    london=sum(1 for x in m['hist'] if 7<=datetime.datetime.fromtimestamp(int(x['entryTime'])/1000,datetime.timezone.utc).hour<13)
    friday_late=sum(1 for x in m['hist'] if (lambda dt: dt.weekday()==4 and dt.hour>=18)(datetime.datetime.fromtimestamp(int(x['entryTime'])/1000,datetime.timezone.utc)))
    safety.append((cost,overlap,hedge,london,friday_late))

# Month-by-month realized net returns from the 1Y standard and harsh histories.
monthly_tables={}
geo={}
positive_ratio={}
for cost in ['standard','harsh']:
    _,m=metrics(reports/f'v4-{winner}-1y-{cost}.json')
    by=defaultdict(float)
    for x in m['hist']:
        dt=datetime.datetime.fromtimestamp(int(x['closeTime'])/1000,datetime.timezone.utc)
        by[dt.strftime('%Y-%m')]+=float(x.get('netProfit',0.0))
    balance=10000.0
    table=[]
    for month in sorted(by):
        pnl=by[month]
        ret=100.0*pnl/balance if balance else 0.0
        table.append((month,pnl,ret))
        balance+=pnl
    monthly_tables[cost]=table
    positive_ratio[cost]=100.0*sum(1 for _,_,r in table if r>0)/len(table) if table else 0.0
    roi=m['roi']/100.0
    geo[cost]=(math.pow(max(0.000001,1.0+roi),1.0/12.0)-1.0)*100.0

std=next(m for p,c,m in rows if p=='1y' and c=='standard')
har=next(m for p,c,m in rows if p=='1y' and c=='harsh')
oos_std=next(m for p,c,m in rows if p=='oos9m' and c=='standard')
oos_har=next(m for p,c,m in rows if p=='oos9m' and c=='harsh')
safety_pass=all(o==0 and h==0 and l==0 and f==0 for _,o,h,l,f in safety)
commercial_pass=(
    std['roi']>=30.0 and har['roi']>=15.0 and
    std['pf']>=1.50 and har['pf']>=1.25 and
    max(std['dd'],har['dd'])<=10.0 and
    min(std['trades'],har['trades'])>=36 and
    geo['standard']>=2.20 and geo['harsh']>=1.15 and
    oos_std['net']>0 and oos_har['net']>0 and oos_std['pf']>1.0 and oos_har['pf']>1.0 and
    positive_ratio['standard']>=60.0 and safety_pass
)

p=root/'V4_COMMERCIAL_VALIDATION.md'
out=['','## Multi-period validation','', '| Period | Cost | Trades | Net | ROI % | PF | DD % |','|---|---|---:|---:|---:|---:|---:|']
for period,cost,m in rows:
    out.append(f"| {period} | {cost} | {m['trades']} | {m['net']:.2f} | {m['roi']:.2f} | {m['pf']:.2f} | {m['dd']:.2f} |")
out += ['','## v3.6 benchmark','', '| Cost | Trades | Net | ROI % | PF | DD % |','|---|---:|---:|---:|---:|---:|']
for cost,m in bench:
    out.append(f"| {cost} | {m['trades']} | {m['net']:.2f} | {m['roi']:.2f} | {m['pf']:.2f} | {m['dd']:.2f} |")
out += ['','## Monthly compounding','']
for cost in ['standard','harsh']:
    out.append(f"### {cost}")
    out.append(f"Geometric monthly return from 1Y ROI: **{geo[cost]:.2f}%**; positive realized months: **{positive_ratio[cost]:.1f}%**")
    out.append('')
    out.append('| Month | Realized net | Approx. month return % |')
    out.append('|---|---:|---:|')
    for month,pnl,ret in monthly_tables[cost]:
        out.append(f'| {month} | {pnl:.2f} | {ret:.2f} |')
    out.append('')
out += ['## Safety audit','', '| Cost | Overlap | Opposite-direction overlap | London entries | Friday late entries |','|---|---:|---:|---:|---:|']
for cost,o,h,l,f in safety:
    out.append(f'| {cost} | {o} | {h} | {l} | {f} |')
out += ['','## Commercial gate','',
        '- Standard 1Y ROI >= 30%',
        '- Harsh 1Y ROI >= 15%',
        '- Standard PF >= 1.50; Harsh PF >= 1.25',
        '- Max 1Y DD <= 10%',
        '- >= 36 trades/year under both cost models',
        '- Geometric monthly >= 2.20% Standard and >= 1.15% Harsh',
        '- Prior 9M OOS remains profitable under both costs',
        '- >= 60% positive realized months Standard',
        '- no overlap/hedging/London/Friday-late violations',
        '',f'**Commercial validation verdict: {"PASS" if commercial_pass else "NOT YET PASS"}**']
p.write_text(p.read_text()+'\n'.join(out)+'\n')
(root/'commercial_verdict.txt').write_text(('PASS' if commercial_pass else 'NOT_YET_PASS')+'\n')
print('\n'.join(out))
PY
