#!/usr/bin/env bash
set -euo pipefail
mkdir -p work/r26-src work/store-src work/build work/cache work/r26-3y work/store-3y work/r26-1y work/store-1y
python3 - <<'PYCODE'
from pathlib import Path
import base64,gzip,hashlib
root=Path('FibonacciHarmonicSniperUltimate/versions/v0.17.0-btc-round18-diagnostics')
data=gzip.decompress(base64.b64decode(''.join(p.read_text().strip() for p in sorted(root.glob('source_payload.part*')))))
if hashlib.sha256(data).hexdigest()!='5f2b7f31c4b8f0d60f52c4c15869aa75df4ff07d7224af971784137716bc8b93': raise SystemExit('Round18 SHA mismatch')
Path('work/Round18.cs').write_bytes(data)
PYCODE
python3 FibonacciHarmonicSniperUltimate/versions/v0.20.0-btc-round21-selective-bypass/round21_transform.py work/Round18.cs work/Round21.cs
python3 FibonacciHarmonicSniperUltimate/versions/v0.21.0-btc-round22-capital-efficiency/round22_transform.py work/Round21.cs work/Round22.cs
cp work/Round22.cs work/r26-src/Round22.cs
python3 FibonacciHarmonicSniperUltimate/versions/v0.23.0-btc-round26-core-refactor/round26_transform.py work/Round22.cs work/r26-src/BTC-Harmonic-Control.cs
rm -f work/r26-src/Round22.cs
cp work/r26-src/*.cs work/store-src/
python3 FibonacciHarmonicSniperUltimate/store-v1/store_v1_transform.py work/store-src/BTC-Harmonic-Control.cs work/store-src/BTC-Harmonic-Guard.cs
rm -f work/store-src/BTC-Harmonic-Control.cs
python3 .ci/store_v1_unified_risk_patch.py work/store-src
rm -f work/Round18.cs work/Round21.cs work/Round22.cs

cat > work/r26-src/Control.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net6.0</TargetFramework><ImplicitUsings>disable</ImplicitUsings><Nullable>disable</Nullable><RootNamespace>cAlgo.Robots</RootNamespace><AlgoName>BTC-Harmonic-Control</AlgoName></PropertyGroup><ItemGroup><PackageReference Include="cTrader.Automate" Version="1.0.19" /></ItemGroup></Project>
EOF
cat > work/store-src/Store.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net6.0</TargetFramework><ImplicitUsings>disable</ImplicitUsings><Nullable>disable</Nullable><RootNamespace>cAlgo.Robots</RootNamespace><AlgoName>BTC-Harmonic-Guard</AlgoName></PropertyGroup><ItemGroup><PackageReference Include="cTrader.Automate" Version="1.0.19" /></ItemGroup></Project>
EOF

dotnet restore work/r26-src/Control.csproj >/dev/null
dotnet build work/r26-src/Control.csproj -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True
dotnet restore work/store-src/Store.csproj >/dev/null
dotnet build work/store-src/Store.csproj -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True
cp "$(find work/r26-src/bin/Release -name '*.algo' | head -n1)" work/build/BTC-Harmonic-Control.algo
cp "$(find work/store-src/bin/Release -name '*.algo' | head -n1)" work/build/BTC-Harmonic-Guard-Store-v1b.algo
sha256sum work/build/*.algo > work/build/SHA256SUMS.txt

: "${CTRADER_CTID:?}"; : "${CTRADER_ACCOUNT:?}"; : "${CTRADER_PASSWORD:?}"
printf '%s' "$CTRADER_PASSWORD" | tr -d '\r\n' > work/ctrader.pwd; chmod 600 work/ctrader.pwd
docker pull ghcr.io/spotware/ctrader-console:5.9.11 >/dev/null

common_control=(--RiskPercent=1.0 --Round17M30RiskPercent=0.50 --Round18CandidateDiagnostics=false --Round21SelectiveHealthBypass=true --Round21BypassMinScore=93 --Round21SameDirH1MaxAgeHours=2 --Round21BypassRiskPercent=0.10 --Round21ReserveH1AtHour=true --Round22H1BuyRiskPercent=1.15 --Round22H1SellRiskPercent=0.80 --Round22M30BuyRiskPercent=0.40 --Round22M30SellRiskPercent=0.50 --MaxOpenPositions=1 --MaxTradesPerDay=6 --MaxDailyLossPercent=5 --EnabledPatterns='Reciprocal ABCD' --PivotLeft=2 --PivotRight=2 --RatioTolerancePercent=6 --MinPatternScore=84 --MaxPatternAgeBars=16 --MaxEntryDistanceAtr=1.80 --ConfirmationMoveAtr=0.05 --UseCandleConfirmation=true --CooldownBars=2 --FallbackRiskReward=1.80 --MinimumRiskReward=1.50 --StopAnchorMode=LegacyD --TargetRiskRewardPolicy=LegacyFallback --Round5Mode=ObserveOnly --MtfMode=Off --Round6RequireM30SellConfirm=false --Round7VetoM30SellAlignment=false --Round8LogExcursions=false --Round9ShadowTpContinuation=false --Round10LogFunnel=false --Round15EnableM30Engine=true --Round16H1HealthGate=true --DebugLogging=false)
run_one(){ out="$1"; algo="$2"; start="$3"; end="$4"; shift 4; docker run --rm -v "$PWD/work:/work" -e "CTID=$CTRADER_CTID" -e 'PWD-FILE=/work/ctrader.pwd' -e "ACCOUNT=$CTRADER_ACCOUNT" ghcr.io/spotware/ctrader-console:5.9.11 backtest "$algo" --environment-variables --exit-on-stop --symbol=BITCOIN --period=h1 --start="$start" --end="$end" --balance=10000 --data-mode=m1 --data-dir=/work/cache --commission=65 --spread=0 "$@" --report="/work/$out/report.html" --report-json="/work/$out/report.json" > "work/$out/report.log" 2>&1; }
run_one r26-3y /work/build/BTC-Harmonic-Control.algo '08/09/2023 00:00' '08/09/2026 00:00' "${common_control[@]}"
run_one store-3y /work/build/BTC-Harmonic-Guard-Store-v1b.algo '08/09/2023 00:00' '08/09/2026 00:00'
run_one r26-1y /work/build/BTC-Harmonic-Control.algo '08/09/2025 00:00' '08/09/2026 00:00' "${common_control[@]}"
run_one store-1y /work/build/BTC-Harmonic-Guard-Store-v1b.algo '08/09/2025 00:00' '08/09/2026 00:00'

python3 - <<'PYCODE'
import json,hashlib,re
from pathlib import Path

def load(p): return json.loads(Path(p).read_text())
def key(x): return (x['entryTime'],x['direction'],x.get('comment',''))
def metric(r): return {'trades':len(r['history']['items']),'roi':float(r['main']['roi']),'net':float(r['main']['netProfit']),'pf':float(r['tradeStatistics']['profitFactor']['all']),'dd_equity':float(r['equity']['maxEquityDrawdownPercent']),'dd_balance':float(r['equity']['maxBalanceDrawdownPercent'])}
def digest(items):
 n=[{'direction':x['direction'],'entryTime':x['entryTime'],'closeTime':x['closeTime'],'entryPrice':round(float(x['entryPrice']),8),'closePrice':round(float(x['closePrice']),8),'volume':round(float(x['volume']),8),'net':round(float(x['net']),8),'pips':round(float(x['pips']),8),'comment':x.get('comment','')} for x in items]
 return hashlib.sha256(json.dumps(n,sort_keys=True).encode()).hexdigest(),n
summary={'version':'BTC Harmonic Guard Store v1b','periods':{},'hardening_passed':False}
for label in ('3y','1y'):
 a=load(f'work/r26-{label}/report.json'); b=load(f'work/store-{label}/report.json'); ha,na=digest(a['history']['items']); hb,nb=digest(b['history']['items'])
 ka={key(x):x for x in a['history']['items']}; kb={key(x):x for x in b['history']['items']}; missing=[ka[k] for k in ka.keys()-kb.keys()]; extra=[kb[k] for k in kb.keys()-ka.keys()]
 ma,mb=metric(a),metric(b)
 exact=(na==nb)
 safety=(not extra and len(missing)<=3 and all((x.get('comment') or '').startswith('R21M30|') for x in missing) and abs(mb['roi']-ma['roi'])<=0.10 and abs(mb['pf']-ma['pf'])<=0.02 and mb['dd_equity']<=ma['dd_equity']+0.15)
 summary['periods'][label]={'control':ma,'store':mb,'control_hash':ha,'store_hash':hb,'exact_trade_parity':exact,'safety_equivalent_parity':exact or safety,'missing_control_trades':missing,'extra_store_trades':extra}
 if not (exact or safety): Path('work/Store-v1b-Summary.json').write_text(json.dumps(summary,indent=2)); raise SystemExit(f'Unsafe Store delta {label}')
# Recent 1Y must remain exact; long-run may differ only via risk-budget safety rejects.
if not summary['periods']['1y']['exact_trade_parity']: raise SystemExit('Recent 1Y exact parity required')
log=Path('work/store-3y/report.log').read_text(errors='ignore')
if summary['periods']['3y']['missing_control_trades'] and 'reason=risk_budget' not in log and '[STORE RISK SIZE REJECT]' not in log: raise SystemExit('Missing trade not evidenced by risk-budget safety rejection')
summary['hardening_passed']=True
Path('work/Store-v1b-Summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
PYCODE
