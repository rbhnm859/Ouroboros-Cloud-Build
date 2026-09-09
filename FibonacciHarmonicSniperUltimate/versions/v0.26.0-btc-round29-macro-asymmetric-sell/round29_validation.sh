#!/usr/bin/env bash
set -euo pipefail

mkdir -p work/r26-src work/r29-src work/build work/cache \
  work/control work/mild work/balanced work/defensive \
  work/y1 work/y2 work/y3 work/harsh-3y work/harsh-y3

python3 - <<'PYCODE'
from pathlib import Path
import base64,gzip,hashlib
root=Path('FibonacciHarmonicSniperUltimate/versions/v0.17.0-btc-round18-diagnostics')
parts=sorted(root.glob('source_payload.part*'))
data=gzip.decompress(base64.b64decode(''.join(p.read_text().strip() for p in parts)))
expected='5f2b7f31c4b8f0d60f52c4c15869aa75df4ff07d7224af971784137716bc8b93'
actual=hashlib.sha256(data).hexdigest()
if actual != expected: raise SystemExit(f'Round18 anchor SHA mismatch: {actual}')
Path('work/Round18.cs').write_bytes(data)
PYCODE

python3 FibonacciHarmonicSniperUltimate/versions/v0.20.0-btc-round21-selective-bypass/round21_transform.py work/Round18.cs work/Round21.cs
python3 FibonacciHarmonicSniperUltimate/versions/v0.21.0-btc-round22-capital-efficiency/round22_transform.py work/Round21.cs work/Round22.cs
python3 FibonacciHarmonicSniperUltimate/versions/v0.23.0-btc-round26-core-refactor/round26_transform.py work/Round22.cs work/r26-src/FibonacciHarmonicSniperUltimate-BTC-Round26-CoreRefactor.cs
python3 FibonacciHarmonicSniperUltimate/versions/v0.26.0-btc-round29-macro-asymmetric-sell/round29_transform.py work/r26-src work/r29-src
rm -f work/Round18.cs work/Round21.cs work/Round22.cs

cat > work/r29-src/Round29-MacroSell.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
    <ImplicitUsings>disable</ImplicitUsings>
    <Nullable>disable</Nullable>
    <RootNamespace>cAlgo.Robots</RootNamespace>
    <AlgoName>FibonacciHarmonicSniperUltimate-BTC-Round29-MacroSell</AlgoName>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="cTrader.Automate" Version="1.0.19" />
  </ItemGroup>
</Project>
EOF

dotnet restore work/r29-src/Round29-MacroSell.csproj
dotnet build work/r29-src/Round29-MacroSell.csproj -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True
ALGO=$(find work/r29-src/bin/Release -type f -name '*.algo' | head -n1)
test -n "$ALGO"
cp "$ALGO" work/build/FibonacciHarmonicSniperUltimate-BTC-Round29-MacroSell.algo
test $(stat -c%s work/build/FibonacciHarmonicSniperUltimate-BTC-Round29-MacroSell.algo) -gt 50000
sha256sum work/build/*.algo > work/build/SHA256SUMS.txt

: "${CTRADER_CTID:?missing CTRADER_CTID}"
: "${CTRADER_ACCOUNT:?missing CTRADER_ACCOUNT}"
: "${CTRADER_PASSWORD:?missing CTRADER_PASSWORD}"
printf '%s' "$CTRADER_PASSWORD" | tr -d '\r\n' > work/ctrader.pwd
chmod 600 work/ctrader.pwd

docker pull ghcr.io/spotware/ctrader-console:5.9.11

run_case() {
  name="$1"; start="$2"; end="$3"; commission="$4"; spread="$5"; moderate="$6"; strong="$7"
  docker run --rm -v "$PWD/work:/work" \
    -e "CTID=$CTRADER_CTID" -e 'PWD-FILE=/work/ctrader.pwd' -e "ACCOUNT=$CTRADER_ACCOUNT" \
    ghcr.io/spotware/ctrader-console:5.9.11 backtest /work/build/FibonacciHarmonicSniperUltimate-BTC-Round29-MacroSell.algo \
    --environment-variables --exit-on-stop --symbol=BITCOIN --period=h1 --start="$start" --end="$end" --balance=10000 --data-mode=m1 --data-dir=/work/cache \
    --commission="$commission" --spread="$spread" --RiskPercent=1.0 --Round17M30RiskPercent=0.50 --Round18CandidateDiagnostics=false \
    --Round21SelectiveHealthBypass=true --Round21BypassMinScore=93 --Round21SameDirH1MaxAgeHours=2 --Round21BypassRiskPercent=0.10 --Round21ReserveH1AtHour=true \
    --Round22H1BuyRiskPercent=1.15 --Round22H1SellRiskPercent=0.80 --Round22M30BuyRiskPercent=0.40 --Round22M30SellRiskPercent=0.50 \
    --Round29ModerateBullSellScale="$moderate" --Round29StrongBullSellScale="$strong" \
    --MaxOpenPositions=1 --MaxTradesPerDay=6 --MaxDailyLossPercent=5 --EnabledPatterns='Reciprocal ABCD' --PivotLeft=2 --PivotRight=2 --RatioTolerancePercent=6 --MinPatternScore=84 \
    --MaxPatternAgeBars=16 --MaxEntryDistanceAtr=1.80 --ConfirmationMoveAtr=0.05 --UseCandleConfirmation=true --CooldownBars=2 --FallbackRiskReward=1.80 --MinimumRiskReward=1.50 \
    --StopAnchorMode=LegacyD --TargetRiskRewardPolicy=LegacyFallback --Round5Mode=ObserveOnly --MtfMode=Off --Round6RequireM30SellConfirm=false --Round7VetoM30SellAlignment=false \
    --Round8LogExcursions=false --Round9ShadowTpContinuation=false --Round10LogFunnel=false --Round15EnableM30Engine=true --Round16H1HealthGate=true --DebugLogging=false \
    --report="/work/$name/report.html" --report-json="/work/$name/report.json" 2>&1 | tee "work/$name/report.log"
}

# Frozen profiles before seeing results.
run_case control   '08/09/2023 00:00' '08/09/2026 00:00' 65 0 1.00 1.00
run_case mild      '08/09/2023 00:00' '08/09/2026 00:00' 65 0 0.85 0.65
run_case balanced  '08/09/2023 00:00' '08/09/2026 00:00' 65 0 0.75 0.50
run_case defensive '08/09/2023 00:00' '08/09/2026 00:00' 65 0 0.60 0.35

python3 - <<'PYCODE'
import json
from pathlib import Path

def metric(path):
    r=json.loads(Path(path).read_text())
    return {
        'trades':int(r['tradeStatistics']['totalTrades']['all']),
        'roi':float(r['main']['roi']),
        'net':float(r['main']['netProfit']),
        'pf':float(r['tradeStatistics']['profitFactor']['all']),
        'dd':float(r['equity']['maxEquityDrawdownPercent']),
        'balance_dd':float(r['balance']['maxBalanceDrawdownPercent']) if 'balance' in r and 'maxBalanceDrawdownPercent' in r['balance'] else None
    }

control=metric('work/control/report.json')
if control['trades'] != 256 or abs(control['roi']-26.55)>0.05 or abs(control['pf']-1.22)>0.03 or abs(control['dd']-21.893009225762995)>0.12:
    raise SystemExit(f'Round29 control drifted from Round22/Round26: {control}')

configs={
    'mild':{'moderate':0.85,'strong':0.65},
    'balanced':{'moderate':0.75,'strong':0.50},
    'defensive':{'moderate':0.60,'strong':0.35}
}
rows=[]
for name,cfg in configs.items():
    m=metric(f'work/{name}/report.json')
    gates={
        'trades_ge_250':m['trades']>=250,
        'roi_gt_control':m['roi']>control['roi'],
        'pf_ge_1_30':m['pf']>=1.30,
        'dd_le_18':m['dd']<=18.0
    }
    rows.append({'profile':name,'config':cfg,'metrics':m,'gates':gates,'gate_count':sum(gates.values()),'pass_all':all(gates.values())})
rows.sort(key=lambda x:(x['pass_all'],x['gate_count'],x['metrics']['pf'],x['metrics']['roi'],-x['metrics']['dd'],x['metrics']['trades']),reverse=True)
selected=rows[0]
out={'version':'Round29 Macro-Asymmetric H1 Sell','control_3y':control,'profiles':rows,'selected':selected,
     'frozen_gate':{'trades':250,'roi':'greater than control','pf':1.30,'dd':18.0}}
Path('work/Round29-3Y-Screen.json').write_text(json.dumps(out,indent=2))
Path('work/selected-config.json').write_text(json.dumps(selected['config']))
print(json.dumps(out,indent=2))
PYCODE

moderate=$(python3 -c "import json; print(json.load(open('work/selected-config.json'))['moderate'])")
strong=$(python3 -c "import json; print(json.load(open('work/selected-config.json'))['strong'])")

run_case y1       '08/09/2023 00:00' '08/09/2024 00:00' 65 0 "$moderate" "$strong"
run_case y2       '08/09/2024 00:00' '08/09/2025 00:00' 65 0 "$moderate" "$strong"
run_case y3       '08/09/2025 00:00' '08/09/2026 00:00' 65 0 "$moderate" "$strong"
run_case harsh-3y '08/09/2023 00:00' '08/09/2026 00:00' 100 1500 "$moderate" "$strong"
run_case harsh-y3 '08/09/2025 00:00' '08/09/2026 00:00' 100 1500 "$moderate" "$strong"

python3 - <<'PYCODE'
import json
from pathlib import Path

def metric(path):
    r=json.loads(Path(path).read_text())
    return {
        'trades':int(r['tradeStatistics']['totalTrades']['all']),
        'roi':float(r['main']['roi']),
        'net':float(r['main']['netProfit']),
        'pf':float(r['tradeStatistics']['profitFactor']['all']),
        'dd':float(r['equity']['maxEquityDrawdownPercent']),
        'balance_dd':float(r['balance']['maxBalanceDrawdownPercent']) if 'balance' in r and 'maxBalanceDrawdownPercent' in r['balance'] else None
    }

screen=json.loads(Path('work/Round29-3Y-Screen.json').read_text())
annual={'y1':metric('work/y1/report.json'),'y2':metric('work/y2/report.json'),'y3':metric('work/y3/report.json')}
harsh3=metric('work/harsh-3y/report.json')
harshy3=metric('work/harsh-y3/report.json')
recent_gates={
    'trades_ge_90':annual['y3']['trades']>=90,
    'roi_ge_35':annual['y3']['roi']>=35.0,
    'pf_ge_1_80':annual['y3']['pf']>=1.80,
    'dd_le_6':annual['y3']['dd']<=6.0
}
robustness={
    'at_least_2_positive_years':sum(1 for x in annual.values() if x['net']>0)>=2,
    'worst_year_pf_ge_0_90':min(x['pf'] for x in annual.values())>=0.90
}
harsh_gates={
    'full_3y_harsh_nonnegative_roi':harsh3['roi']>=0.0,
    'full_3y_harsh_pf_ge_1':harsh3['pf']>=1.0,
    'recent_harsh_pf_ge_1_35':harshy3['pf']>=1.35,
    'recent_harsh_dd_le_6_8':harshy3['dd']<=6.8
}
promotion=screen['selected']['pass_all'] and all(recent_gates.values()) and all(robustness.values()) and all(harsh_gates.values())
out={
    'version':'Round29 Macro-Asymmetric H1 Sell',
    'selected':screen['selected'],
    'annual':annual,
    'harsh_3y':harsh3,
    'harsh_recent_1y':harshy3,
    'recent_gates':recent_gates,
    'robustness_gates':robustness,
    'harsh_gates':harsh_gates,
    'promotion_eligible':promotion,
    'decision':'PROMOTE' if promotion else 'DO_NOT_PROMOTE'
}
Path('work/Round29-Final-Summary.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
PYCODE
