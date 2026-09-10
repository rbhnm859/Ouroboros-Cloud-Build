#!/usr/bin/env bash
set -euo pipefail

ROOT='FibonacciHarmonicSniperUltimate/versions/xauusd_3'
SRC="$ROOT/src/FibonacciXAUUSD3.cs"
WORK="$ROOT/validation-v36-tp"
REPORTS="$WORK/reports"
CACHE="$WORK/cache"
IMAGE='ghcr.io/spotware/ctrader-console:5.9.11'

: "${CTRADER_CTID:?CTRADER_CTID missing}"
: "${CTRADER_ACCOUNT:?CTRADER_ACCOUNT missing}"
: "${CTRADER_PASSWORD:?CTRADER_PASSWORD missing}"

rm -rf "$WORK"
mkdir -p "$REPORTS" "$CACHE"
printf '%s' "$CTRADER_PASSWORD" > "$WORK/ctrader.pwd"

python3 - <<'PY'
from pathlib import Path
p=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_3/src/FibonacciXAUUSD3.cs')
s=p.read_text()
old='Print("VERSION xauusd_3 v3.6.0-safety-hardening");'
new='Print("VERSION xauusd_3 v3.6.1-tp-resilience-candidate");'
assert s.count(old)==1, 'expected formal v3.6 version marker exactly once'
s=s.replace(old,new,1)
marker='''        [Parameter("H1 ATR14/ATR50 Min", DefaultValue = 1.15, MinValue = 1.00, MaxValue = 2.00, Group = "Regime")]\n        public double H1AtrExpansionMin { get; set; }\n'''
addition='''\n        [Parameter("TP Distance Multiplier", DefaultValue = 1.0, MinValue = 1.0, MaxValue = 1.4, Group = "Exit")]
        public double TakeProfitMultiplier { get; set; }
'''
assert s.count(marker)==1, 'H1 ATR marker mismatch'
assert 'TP Distance Multiplier' not in s, 'TP multiplier already present'
s=s.replace(marker,marker+addition,1)
oldtp='                double tpPips = tpDistance / Symbol.PipSize;'
newtp='                double tpPips = (tpDistance / Symbol.PipSize) * TakeProfitMultiplier;'
assert s.count(oldtp)==1, 'TP calculation marker mismatch'
s=s.replace(oldtp,newtp,1)
p.write_text(s)
PY

grep -q 'v3.6.1-tp-resilience-candidate' "$SRC"
grep -q 'TP Distance Multiplier' "$SRC"
grep -q 'RestoreDailyStateFromHistory' "$SRC"
grep -q 'EnsureProtectionIntegrity' "$SRC"
grep -q 'CurrentBotFloatingNet' "$SRC"
grep -q 'HasAnySymbolExposure' "$SRC"

docker pull "$IMAGE"
docker run --rm --entrypoint sh -v "$PWD:/repo" -w /repo "$IMAGE" -c \
  "dotnet restore '$ROOT/FibonacciXAUUSD3.csproj' && dotnet build '$ROOT/FibonacciXAUUSD3.csproj' -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True"

ALGO="$(find "$ROOT" -type f -name '*.algo' ! -path '*/builds/*' ! -path '*/validation-*/*' -print -quit)"
test -n "$ALGO"
test -s "$ALGO"
cp "$ALGO" "$WORK/FibonacciXAUUSD3-v3.6.1-TPResilience.algo"
cp "$SRC" "$WORK/FibonacciXAUUSD3-v3.6.1.cs"
sha256sum "$WORK/FibonacciXAUUSD3-v3.6.1-TPResilience.algo" > "$WORK/algo.sha256"

run_bt() {
  local variant="$1" tp="$2" period="$3" cost="$4" start="$5" end="$6" spread="$7" commission="$8"
  local label="${variant}-${period}-${cost}"
  echo "=== BACKTEST $label TP=$tp ==="
  docker run --rm \
    -v "$PWD/$WORK:/work" \
    -e "CTID=$CTRADER_CTID" \
    -e 'PWD-FILE=/work/ctrader.pwd' \
    -e "ACCOUNT=$CTRADER_ACCOUNT" \
    "$IMAGE" backtest /work/FibonacciXAUUSD3-v3.6.1-TPResilience.algo \
    --environment-variables --exit-on-stop \
    --symbol=XAUUSD --period=m5 --start="$start" --end="$end" \
    --balance=10000 --data-mode=m1 --data-dir=/work/cache \
    --commission="$commission" --spread="$spread" \
    --RiskPercent=0.50 --MaxDailyLossPercent=3 --MinimumRiskReward=1.5 \
    --PreScoreMin=42 --FinalScoreMin=60 --M5PreScoreFloor=50 --M5RulesNeeded=2 \
    --MinImpulseAtr=1.2 --MinStopAtr=0.20 --MaxAllowedRR=8 \
    --BuyH1MinScore=18 --BlockLondonEntries=true \
    --RequireH1AtrExpansion=true --H1AtrExpansionMin=1.15 \
    --TakeProfitMultiplier="$tp" \
    --report="/work/reports/${label}.html" \
    --report-json="/work/reports/${label}.json" \
    2>&1 | tee "$REPORTS/${label}.log"
  test -s "$REPORTS/${label}.json"
}

# Fixed entry logic, fixed 0.5% risk. Only TP distance changes.
for spec in 'base 1.00' 'tp110 1.10' 'tp120 1.20' 'tp130 1.30'; do
  set -- $spec
  v="$1"; tp="$2"
  run_bt "$v" "$tp" 3m standard 09/06/2026 09/09/2026 17.42 35
  run_bt "$v" "$tp" 3m harsh    09/06/2026 09/09/2026 30 50
  run_bt "$v" "$tp" 6m standard 09/03/2026 09/09/2026 17.42 35
  run_bt "$v" "$tp" 6m harsh    09/03/2026 09/09/2026 30 50
  run_bt "$v" "$tp" 1y standard 09/09/2025 09/09/2026 17.42 35
  run_bt "$v" "$tp" 1y harsh    09/09/2025 09/09/2026 30 50
done

python3 - <<'PY'
import datetime, json
from pathlib import Path
base=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_3/validation-v36-tp')
reports=base/'reports'
variants=['base','tp110','tp120','tp130']
periods=['3m','6m','1y']
costs=['standard','harsh']
rows=[]
safety_fail=False

def f(x):
    try: return float(x)
    except: return 0.0

for v in variants:
    for period in periods:
        for cost in costs:
            d=json.loads((reports/f'{v}-{period}-{cost}.json').read_text())
            ts=d['tradeStatistics']; main=d['main']; eq=d['equity']
            hist=d.get('history',{}).get('items',[])
            spans=sorted((int(x['entryTime']),int(x['closeTime']),x['direction']) for x in hist)
            overlap=hedge=0
            for i,a in enumerate(spans):
                for b in spans[i+1:]:
                    if b[0]>=a[1]: break
                    overlap+=1
                    hedge+=int(b[2]!=a[2])
            london=sum(1 for x in hist if 7<=datetime.datetime.fromtimestamp(int(x['entryTime'])/1000,datetime.timezone.utc).hour<13)
            trades=int(ts['totalTrades']['all'])
            net=f(main['netProfit']); roi=f(main['roi']); pf=f(ts['profitFactor']['all']); dd=f(eq['maxEquityDrawdownPercent'])
            safety_fail |= bool(overlap or hedge or london)
            rows.append(dict(v=v,period=period,cost=cost,trades=trades,net=net,roi=roi,pf=pf,dd=dd,overlap=overlap,hedge=hedge,london=london))

def period_rows(v,p): return [r for r in rows if r['v']==v and r['period']==p]
ranking=[]
for v in variants:
    r3=period_rows(v,'3m'); r6=period_rows(v,'6m'); r1=period_rows(v,'1y')
    min3=min(x['roi'] for x in r3); min6=min(x['roi'] for x in r6); min1=min(x['roi'] for x in r1)
    minpf=min(x['pf'] for x in r1); maxdd=max(x['dd'] for x in r1)
    score=min1+0.50*min6+0.20*min3+2.0*(minpf-1.0)-max(0.0,maxdd-6.0)
    ranking.append((score,v,min3,min6,min1,minpf,maxdd))
ranking.sort(reverse=True)
base_rank=next(x for x in ranking if x[1]=='base')
best=ranking[0]
if best[1]!='base':
    promote=(best[4]>base_rank[4] and best[5]>=base_rank[5]-0.02 and best[6]<=base_rank[6]+0.50 and best[3]>0 and best[4]>0)
    winner=best[1] if promote else 'base'
else:
    winner='base'
tpmap={'base':'1.00','tp110':'1.10','tp120':'1.20','tp130':'1.30'}
(base/'winner.txt').write_text(winner+'\n')
(base/'winner_tp.txt').write_text(tpmap[winner]+'\n')
out=['# xauusd_3 v3.6 TP Robustness Validation','',
     '| Variant | Period | Cost | Trades | Net | ROI % | PF | DD % | Overlap | Hedge | London |',
     '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
    out.append(f"| {r['v']} | {r['period']} | {r['cost']} | {r['trades']} | {r['net']:.2f} | {r['roi']:.2f} | {r['pf']:.2f} | {r['dd']:.2f} | {r['overlap']} | {r['hedge']} | {r['london']} |")
out += ['', '## Robustness ranking','']
for score,v,min3,min6,min1,minpf,maxdd in ranking:
    out.append(f'- {v}: score={score:.2f}; min3MROI={min3:.2f}%; min6MROI={min6:.2f}%; min1YROI={min1:.2f}%; min1YPF={minpf:.2f}; max1YDD={maxdd:.2f}%')
out += ['',f'**Winner for split validation: {winner} (TP multiplier {tpmap[winner]})**',f'**Safety precheck: {"FAIL" if safety_fail else "PASS"}**']
(base/'V36_TP_VALIDATION_SUMMARY.md').write_text('\n'.join(out)+'\n')
print('\n'.join(out))
PY

WINNER="$(cat "$WORK/winner.txt")"
TP="$(cat "$WORK/winner_tp.txt")"
run_bt "$WINNER" "$TP" oos1 standard 09/09/2025 09/03/2026 17.42 35
run_bt "$WINNER" "$TP" oos1 harsh    09/09/2025 09/03/2026 30 50
run_bt "$WINNER" "$TP" oos2 standard 09/03/2026 09/09/2026 17.42 35
run_bt "$WINNER" "$TP" oos2 harsh    09/03/2026 09/09/2026 30 50

python3 - <<'PY'
import json
from pathlib import Path
base=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_3/validation-v36-tp')
reports=base/'reports'
winner=(base/'winner.txt').read_text().strip()
lines=['','## Chronological split validation','', '| Segment | Cost | Trades | Net | ROI % | PF | DD % |', '|---|---|---:|---:|---:|---:|---:|']
pass_all=True
for seg in ['oos1','oos2']:
    for cost in ['standard','harsh']:
        d=json.loads((reports/f'{winner}-{seg}-{cost}.json').read_text())
        ts=d['tradeStatistics']; main=d['main']; eq=d['equity']
        trades=int(ts['totalTrades']['all']); net=float(main['netProfit']); roi=float(main['roi']); pf=float(ts['profitFactor']['all']); dd=float(eq['maxEquityDrawdownPercent'])
        lines.append(f'| {seg} | {cost} | {trades} | {net:.2f} | {roi:.2f} | {pf:.2f} | {dd:.2f} |')
        if trades<5 or net<=0 or pf<=1.0: pass_all=False
lines += ['', f'**Final robustness verdict: {"PASS" if pass_all else "NOT YET PASS"}**', 'Promotion requires both chronological halves to stay profitable under Standard and Harsh costs with at least 5 trades per segment.']
p=base/'V36_TP_VALIDATION_SUMMARY.md'
p.write_text(p.read_text()+'\n'.join(lines)+'\n')
print('\n'.join(lines))
PY
