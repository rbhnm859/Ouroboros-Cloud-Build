#!/usr/bin/env bash
set -euo pipefail

ID="${1:?id}"
START="${2:?start}"
END="${3:?end}"
COMMISSION="${4:?commission}"
SPREAD="${5:?spread}"

mkdir -p work/src work/build work/cache "work/$ID/control" "work/$ID/balanced"

python3 - <<'PYCODE'
from pathlib import Path
import base64,gzip,hashlib
root=Path('FibonacciHarmonicSniperUltimate/versions/v0.17.0-btc-round18-diagnostics')
parts=sorted(root.glob('source_payload.part*'))
if not parts:
    raise SystemExit('Round18 source payload missing')
data=gzip.decompress(base64.b64decode(''.join(p.read_text().strip() for p in parts)))
expected='5f2b7f31c4b8f0d60f52c4c15869aa75df4ff07d7224af971784137716bc8b93'
actual=hashlib.sha256(data).hexdigest()
if actual != expected:
    raise SystemExit(f'Round18 anchor SHA mismatch: {actual}')
Path('work/src/Round18.cs').write_bytes(data)
PYCODE

python3 FibonacciHarmonicSniperUltimate/versions/v0.20.0-btc-round21-selective-bypass/round21_transform.py work/src/Round18.cs work/src/Round21.cs
python3 FibonacciHarmonicSniperUltimate/versions/v0.21.0-btc-round22-capital-efficiency/round22_transform.py work/src/Round21.cs work/src/FibonacciHarmonicSniperUltimate-BTC-Round22-CapitalEfficiency.cs
rm -f work/src/Round18.cs work/src/Round21.cs

cat > work/src/FibonacciHarmonicSniperUltimate-BTC-Round22-CapitalEfficiency.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
    <ImplicitUsings>disable</ImplicitUsings>
    <Nullable>disable</Nullable>
    <RootNamespace>cAlgo.Robots</RootNamespace>
    <AlgoName>FibonacciHarmonicSniperUltimate-BTC-Round22-CapitalEfficiency</AlgoName>
  </PropertyGroup>
  <ItemGroup><PackageReference Include="cTrader.Automate" Version="1.*-*" /></ItemGroup>
</Project>
EOF

dotnet restore work/src/FibonacciHarmonicSniperUltimate-BTC-Round22-CapitalEfficiency.csproj
dotnet build work/src/FibonacciHarmonicSniperUltimate-BTC-Round22-CapitalEfficiency.csproj -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True
ALGO=$(find work/src/bin/Release -type f -name '*.algo' | head -n1)
test -n "$ALGO"
cp "$ALGO" work/build/Round22.algo
sha256sum work/build/Round22.algo > work/build/SHA256SUMS.txt

printf '%s' "${CTRADER_PASSWORD:?missing password}" | tr -d '\r\n' > work/ctrader.pwd
chmod 600 work/ctrader.pwd
docker pull ghcr.io/spotware/ctrader-console:5.9.11

run_case() {
  local MODE="$1"
  shift
  docker run --rm \
    -v "$PWD/work:/work" \
    -e "CTID=${CTRADER_CTID:?missing ctid}" \
    -e 'PWD-FILE=/work/ctrader.pwd' \
    -e "ACCOUNT=${CTRADER_ACCOUNT:?missing account}" \
    ghcr.io/spotware/ctrader-console:5.9.11 \
    backtest /work/build/Round22.algo \
    --environment-variables --exit-on-stop --symbol=BITCOIN --period=h1 \
    --start="$START" --end="$END" --balance=10000 --data-mode=m1 --data-dir=/work/cache \
    --commission="$COMMISSION" --spread="$SPREAD" \
    --RiskPercent=1.0 --Round17M30RiskPercent=0.50 --Round18CandidateDiagnostics=false \
    --MaxOpenPositions=1 --MaxTradesPerDay=6 --MaxDailyLossPercent=5 \
    --EnabledPatterns='Reciprocal ABCD' --PivotLeft=2 --PivotRight=2 --RatioTolerancePercent=6 --MinPatternScore=84 \
    --MaxPatternAgeBars=16 --MaxEntryDistanceAtr=1.80 --ConfirmationMoveAtr=0.05 --UseCandleConfirmation=true \
    --CooldownBars=2 --FallbackRiskReward=1.80 --MinimumRiskReward=1.50 --StopAnchorMode=LegacyD --TargetRiskRewardPolicy=LegacyFallback \
    --Round5Mode=ObserveOnly --MtfMode=Off --Round6RequireM30SellConfirm=false --Round7VetoM30SellAlignment=false \
    --Round8LogExcursions=false --Round9ShadowTpContinuation=false --Round10LogFunnel=false \
    --Round15EnableM30Engine=true --Round16H1HealthGate=true --DebugLogging=false \
    "$@" \
    --report="/work/$ID/$MODE/report.html" --report-json="/work/$ID/$MODE/report.json" \
    2>&1 | tee "work/$ID/$MODE/report.log"
}

run_case control \
  --Round21SelectiveHealthBypass=false --Round21ReserveH1AtHour=false \
  --Round22H1BuyRiskPercent=1.00 --Round22H1SellRiskPercent=1.00 --Round22M30BuyRiskPercent=0.50 --Round22M30SellRiskPercent=0.50

run_case balanced \
  --Round21SelectiveHealthBypass=true --Round21BypassMinScore=93 --Round21SameDirH1MaxAgeHours=2 --Round21BypassRiskPercent=0.10 --Round21ReserveH1AtHour=true \
  --Round22H1BuyRiskPercent=1.15 --Round22H1SellRiskPercent=0.80 --Round22M30BuyRiskPercent=0.40 --Round22M30SellRiskPercent=0.50

python3 - "$ID" "$START" "$END" "$COMMISSION" "$SPREAD" <<'PYCODE'
import json,sys
from pathlib import Path
id_,start,end,commission,spread=sys.argv[1:]
root=Path('work')/id_
def metrics(name):
    r=json.loads((root/name/'report.json').read_text())
    return {
        'trades':int(r['tradeStatistics']['totalTrades']['all']),
        'roi':float(r['main']['roi']),
        'net':float(r['main']['netProfit']),
        'pf':float(r['tradeStatistics']['profitFactor']['all']),
        'dd':float(r['equity']['maxEquityDrawdownPercent'])
    }
c=metrics('control'); b=metrics('balanced')
out={
  'id':id_, 'period':{'start':start,'end':end}, 'costs':{'commission':int(commission),'spread':int(spread)},
  'round17_control':c, 'round22_balanced':b,
  'delta':{'trades':b['trades']-c['trades'],'roi':b['roi']-c['roi'],'pf':b['pf']-c['pf'],'dd':b['dd']-c['dd']}
}
(root/'comparison.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
PYCODE

rm -f work/ctrader.pwd
