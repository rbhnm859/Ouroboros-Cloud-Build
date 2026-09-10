#!/usr/bin/env bash
set -euo pipefail
ROOT='FibonacciHarmonicSniperUltimate/versions/xauusd_3'
WORK="$ROOT/validation-v40-risk"
REPORTS="$WORK/reports"
CACHE="$WORK/cache"
IMAGE='ghcr.io/spotware/ctrader-console:5.9.11'
: "${CTRADER_CTID:?CTRADER_CTID missing}"
: "${CTRADER_ACCOUNT:?CTRADER_ACCOUNT missing}"
: "${CTRADER_PASSWORD:?CTRADER_PASSWORD missing}"
rm -rf "$WORK"; mkdir -p "$REPORTS" "$CACHE"; printf '%s' "$CTRADER_PASSWORD" > "$WORK/ctrader.pwd"
docker pull "$IMAGE"
docker run --rm --entrypoint sh -v "$PWD:/repo" -w /repo "$IMAGE" -c "dotnet restore '$ROOT/FibonacciXAUUSD3.csproj' && dotnet build '$ROOT/FibonacciXAUUSD3.csproj' -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True"
ALGO="$(find "$ROOT" -type f -name '*.algo' ! -path '*/builds/*' ! -path '*/validation-*/*' -print -quit)"
test -n "$ALGO"; test -s "$ALGO"; cp "$ALGO" "$WORK/FibonacciXAUUSD3-CommercialRisk.algo"; sha256sum "$WORK/FibonacciXAUUSD3-CommercialRisk.algo" > "$WORK/algo.sha256"
run_bt(){ local risk="$1" period="$2" cost="$3" start="$4" end="$5" spread="$6" commission="$7"; local rname="r${risk/./p}"; local label="${rname}-${period}-${cost}"; echo "=== $label ==="; docker run --rm -v "$PWD/$WORK:/work" -e "CTID=$CTRADER_CTID" -e 'PWD-FILE=/work/ctrader.pwd' -e "ACCOUNT=$CTRADER_ACCOUNT" "$IMAGE" backtest /work/FibonacciXAUUSD3-CommercialRisk.algo --environment-variables --exit-on-stop --symbol=XAUUSD --period=m5 --start="$start" --end="$end" --balance=10000 --data-mode=m1 --data-dir=/work/cache --commission="$commission" --spread="$spread" --RiskPercent="$risk" --MaxDailyLossPercent=3 --MinimumRiskReward=1.5 --PreScoreMin=42 --FinalScoreMin=60 --M5PreScoreFloor=50 --M5RulesNeeded=2 --MinImpulseAtr=1.2 --MinStopAtr=0.20 --MaxAllowedRR=8 --BuyH1MinScore=18 --BlockLondonEntries=true --RequireH1AtrExpansion=true --H1AtrExpansionMin=1.15 --report="/work/reports/${label}.html" --report-json="/work/reports/${label}.json" 2>&1 | tee "$REPORTS/${label}.log"; test -s "$REPORTS/${label}.json"; }
for risk in 0.50 0.75 1.00 1.25 1.50; do
  run_bt "$risk" 3m standard 09/06/2026 09/09/2026 17.42 35
  run_bt "$risk" 3m harsh 09/06/2026 09/09/2026 30 50
  run_bt "$risk" 6m standard 09/03/2026 09/09/2026 17.42 35
  run_bt "$risk" 6m harsh 09/03/2026 09/09/2026 30 50
  run_bt "$risk" 1y standard 09/09/2025 09/09/2026 17.42 35
  run_bt "$risk" 1y harsh 09/09/2025 09/09/2026 30 50
done
python3 - <<'PY'
import json, math, datetime
from pathlib import Path
base=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_3/validation-v40-risk'); reports=base/'reports'; risks=['0p50','0p75','1p00','1p25','1p50']
rows=[]
for r in risks:
  for period in ['3m','6m','1y']:
    for cost in ['standard','harsh']:
      d=json.loads((reports/f'r{r}-{period}-{cost}.json').read_text()); ts=d['tradeStatistics']; main=d['main']; eq=d['equity']
      roi=float(main['roi']); gm=((1+roi/100)**(1/12)-1)*100 if period=='1y' and roi>-100 else 0
      rows.append(dict(r=r,period=period,cost=cost,trades=int(ts['totalTrades']['all']),net=float(main['netProfit']),roi=roi,pf=float(ts['profitFactor']['all']),dd=float(eq['maxEquityDrawdownPercent']),gm=gm))
def get(r,p,c): return next(x for x in rows if x['r']==r and x['period']==p and x['cost']==c)
balanced=[]; aggressive=[]
for r in risks:
  h=get(r,'1y','harsh'); s=get(r,'1y','standard'); h6=get(r,'6m','harsh'); h3=get(r,'3m','harsh')
  if h['roi']>0 and h6['roi']>0 and h3['roi']>0 and h['pf']>=1.25 and h['dd']<=10: balanced.append(r)
  if h['roi']>0 and h6['roi']>0 and h3['roi']>0 and h['pf']>=1.20 and h['dd']<=15: aggressive.append(r)
balanced_pick=max(balanced,key=lambda r:get(r,'1y','harsh')['roi']) if balanced else '0p50'
aggressive_pick=max(aggressive,key=lambda r:get(r,'1y','harsh')['roi']) if aggressive else balanced_pick
out=['# xauusd_3 Commercial Risk / Compound Validation','', '| Risk % | Period | Cost | Trades | Net | ROI % | PF | DD % | Geo monthly % |','|---:|---|---|---:|---:|---:|---:|---:|---:|']
for x in rows: out.append(f"| {x['r'].replace('p','.')} | {x['period']} | {x['cost']} | {x['trades']} | {x['net']:.2f} | {x['roi']:.2f} | {x['pf']:.2f} | {x['dd']:.2f} | {x['gm']:.2f} |")
out += ['',f'**Balanced commercial profile (Harsh PF >=1.25, DD <=10%): {balanced_pick.replace("p",".")}% risk/trade**',f'**Aggressive commercial profile (Harsh PF >=1.20, DD <=15%): {aggressive_pick.replace("p",".")}% risk/trade**','', 'The 7% cTrader Store monthly-display threshold is treated as an aspirational reporting benchmark, not as a promotion criterion. Risk is never increased merely to cross it.']
(base/'V40_RISK_COMPOUND_SUMMARY.md').write_text('\n'.join(out)+'\n'); print('\n'.join(out))
PY
