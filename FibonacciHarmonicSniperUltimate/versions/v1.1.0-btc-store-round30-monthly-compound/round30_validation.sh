#!/usr/bin/env bash
set -euo pipefail
V=FibonacciHarmonicSniperUltimate/versions/v1.1.0-btc-store-round30-monthly-compound
mkdir -p work/r26-src work/store-src work/r30-src work/build work/cache \
  work/control-3y work/balanced-3y work/conservative-3y \
  work/control-1y work/balanced-1y work/conservative-1y \
  work/y1 work/y2 work/y3 work/harsh-3y work/harsh-1y

python3 - <<'PYCODE'
from pathlib import Path
import base64,gzip,hashlib
root=Path('FibonacciHarmonicSniperUltimate/versions/v0.17.0-btc-round18-diagnostics')
data=gzip.decompress(base64.b64decode(''.join(p.read_text().strip() for p in sorted(root.glob('source_payload.part*')))))
expected='5f2b7f31c4b8f0d60f52c4c15869aa75df4ff07d7224af971784137716bc8b93'
actual=hashlib.sha256(data).hexdigest()
if actual!=expected: raise SystemExit(f'Round18 SHA mismatch {actual}')
Path('work/Round18.cs').write_bytes(data)
PYCODE
python3 FibonacciHarmonicSniperUltimate/versions/v0.20.0-btc-round21-selective-bypass/round21_transform.py work/Round18.cs work/Round21.cs
python3 FibonacciHarmonicSniperUltimate/versions/v0.21.0-btc-round22-capital-efficiency/round22_transform.py work/Round21.cs work/Round22.cs
cp work/Round22.cs work/r26-src/Round22.cs
python3 FibonacciHarmonicSniperUltimate/versions/v0.23.0-btc-round26-core-refactor/round26_transform.py work/Round22.cs work/r26-src/BTC-Harmonic-Guard-Control.cs
rm -f work/r26-src/Round22.cs
cp work/r26-src/*.cs work/store-src/
python3 FibonacciHarmonicSniperUltimate/store-v1/store_v1_transform.py work/store-src/BTC-Harmonic-Guard-Control.cs work/store-src/BTC-Harmonic-Guard.cs
rm -f work/store-src/BTC-Harmonic-Guard-Control.cs
python3 "$V/round30_compound_transform.py" work/store-src work/r30-src
rm -f work/Round18.cs work/Round21.cs work/Round22.cs

cat > work/r30-src/Round30.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><TargetFramework>net6.0</TargetFramework><ImplicitUsings>disable</ImplicitUsings><Nullable>disable</Nullable><RootNamespace>cAlgo.Robots</RootNamespace><AlgoName>BTC-Harmonic-Guard-Compound</AlgoName></PropertyGroup>
  <ItemGroup><PackageReference Include="cTrader.Automate" Version="1.0.19" /></ItemGroup>
</Project>
EOF

dotnet restore work/r30-src/Round30.csproj
dotnet build work/r30-src/Round30.csproj -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True
ALGO=$(find work/r30-src/bin/Release -type f -name '*.algo' | head -n1)
test -n "$ALGO"
cp "$ALGO" work/build/BTC-Harmonic-Guard-Compound.algo
test $(stat -c%s work/build/BTC-Harmonic-Guard-Compound.algo) -gt 50000
sha256sum work/build/*.algo > work/build/SHA256SUMS.txt

: "${CTRADER_CTID:?missing CTRADER_CTID}"; : "${CTRADER_ACCOUNT:?missing CTRADER_ACCOUNT}"; : "${CTRADER_PASSWORD:?missing CTRADER_PASSWORD}"
printf '%s' "$CTRADER_PASSWORD" | tr -d '\r\n' > work/ctrader.pwd; chmod 600 work/ctrader.pwd
docker pull ghcr.io/spotware/ctrader-console:5.9.11

run_case() {
  name="$1"; start="$2"; end="$3"; commission="$4"; spread="$5"; enabled="$6"; low="$7"; high="$8"
  docker run --rm -v "$PWD/work:/work" -e "CTID=$CTRADER_CTID" -e 'PWD-FILE=/work/ctrader.pwd' -e "ACCOUNT=$CTRADER_ACCOUNT" \
    ghcr.io/spotware/ctrader-console:5.9.11 backtest /work/build/BTC-Harmonic-Guard-Compound.algo \
    --environment-variables --exit-on-stop --symbol=BITCOIN --period=h1 --start="$start" --end="$end" --balance=10000 --data-mode=m1 --data-dir=/work/cache \
    --commission="$commission" --spread="$spread" --R30CompoundEnabled="$enabled" --R30LowQualityScale="$low" --R30HighQualityScale="$high" --R30LowQualityThreshold=0.45 --R30HighQualityThreshold=0.75 \
    --report="/work/$name/report.html" --report-json="/work/$name/report.json" > "work/$name/report.log" 2>&1
  python3 "$V/monthly_report_json.py" "work/$name/report.json" "work/$name/monthly.json"
}

# Frozen profiles. No brute-force search.
run_case control-3y      '08/09/2023 00:00' '08/09/2026 00:00' 65 0 false 1.00 1.00
run_case balanced-3y     '08/09/2023 00:00' '08/09/2026 00:00' 65 0 true  0.75 1.10
run_case conservative-3y '08/09/2023 00:00' '08/09/2026 00:00' 65 0 true  0.60 1.05
run_case control-1y      '08/09/2025 00:00' '08/09/2026 00:00' 65 0 false 1.00 1.00
run_case balanced-1y     '08/09/2025 00:00' '08/09/2026 00:00' 65 0 true  0.75 1.10
run_case conservative-1y '08/09/2025 00:00' '08/09/2026 00:00' 65 0 true  0.60 1.05

python3 - <<'PYCODE'
import json
from pathlib import Path

def metric(name):
 r=json.loads(Path(f'work/{name}/report.json').read_text()); mo=json.loads(Path(f'work/{name}/monthly.json').read_text())
 return {'trades':int(r['tradeStatistics']['totalTrades']['all']),'roi':float(r['main']['roi']),'net':float(r['main']['netProfit']),'pf':float(r['tradeStatistics']['profitFactor']['all']),'dd':float(r['equity']['maxEquityDrawdownPercent']),'balance_dd':float(r['balance']['maxBalanceDrawdownPercent']),'monthly_geo':float(mo['duration_normalized_geometric_monthly_pct']),'full_month_geo':mo['full_calendar_months_only'].get('geometric_pct'),'worst_full_month':mo['full_calendar_months_only'].get('worst_pct'),'positive_full_month_pct':mo['full_calendar_months_only'].get('positive_pct')}
control3=metric('control-3y'); control1=metric('control-1y')
if control3['trades']!=256 or abs(control3['roi']-26.55)>0.05 or abs(control3['pf']-1.22)>0.03: raise SystemExit(f'Control drift 3Y: {control3}')
if control1['trades']!=95 or abs(control1['roi']-39.93)>0.05 or abs(control1['pf']-1.95)>0.03: raise SystemExit(f'Control drift 1Y: {control1}')
profiles={'balanced':{'low':0.75,'high':1.10},'conservative':{'low':0.60,'high':1.05}}
rows=[]
for name,cfg in profiles.items():
 m3=metric(name+'-3y'); m1=metric(name+'-1y')
 monthly_improvement=(m1['monthly_geo']/control1['monthly_geo']-1.0) if control1['monthly_geo'] else 0
 gates={
  '3y_trades_ge_250':m3['trades']>=250,'3y_pf_ge_1_30':m3['pf']>=1.30,'3y_dd_le_18':m3['dd']<=18.0,
  '1y_trades_ge_95':m1['trades']>=95,'1y_pf_ge_1_80':m1['pf']>=1.80,'1y_dd_le_6':m1['dd']<=6.0,
  'return_gate':(m1['roi']>=39.93) or (monthly_improvement>=0.10 and m1['roi']>=39.93*0.95),
  'worst_month_not_3pp_worse': (m1['worst_full_month'] is None or control1['worst_full_month'] is None or m1['worst_full_month']>=control1['worst_full_month']-3.0)
 }
 rows.append({'profile':name,'config':cfg,'metrics_3y':m3,'metrics_1y':m1,'monthly_improvement_ratio':monthly_improvement,'gates':gates,'gate_count':sum(gates.values()),'pass_preliminary':all(gates.values())})
rows.sort(key=lambda x:(x['pass_preliminary'],x['gate_count'],x['metrics_1y']['monthly_geo'],x['metrics_3y']['pf'],-x['metrics_3y']['dd']),reverse=True)
out={'version':'Round30 Monthly Compound','control_3y':control3,'control_1y':control1,'profiles':rows,'selected':rows[0]}
Path('work/Round30-Screen.json').write_text(json.dumps(out,indent=2)); Path('work/selected.json').write_text(json.dumps(rows[0]['config']))
print(json.dumps(out,indent=2))
PYCODE
low=$(python3 -c "import json; print(json.load(open('work/selected.json'))['low'])")
high=$(python3 -c "import json; print(json.load(open('work/selected.json'))['high'])")

run_case y1       '08/09/2023 00:00' '08/09/2024 00:00' 65 0 true "$low" "$high"
run_case y2       '08/09/2024 00:00' '08/09/2025 00:00' 65 0 true "$low" "$high"
run_case y3       '08/09/2025 00:00' '08/09/2026 00:00' 65 0 true "$low" "$high"
run_case harsh-3y '08/09/2023 00:00' '08/09/2026 00:00' 100 1500 true "$low" "$high"
run_case harsh-1y '08/09/2025 00:00' '08/09/2026 00:00' 100 1500 true "$low" "$high"

python3 - <<'PYCODE'
import json
from pathlib import Path

def metric(name):
 r=json.loads(Path(f'work/{name}/report.json').read_text()); mo=json.loads(Path(f'work/{name}/monthly.json').read_text())
 return {'trades':int(r['tradeStatistics']['totalTrades']['all']),'roi':float(r['main']['roi']),'net':float(r['main']['netProfit']),'pf':float(r['tradeStatistics']['profitFactor']['all']),'dd':float(r['equity']['maxEquityDrawdownPercent']),'balance_dd':float(r['balance']['maxBalanceDrawdownPercent']),'monthly_geo':float(mo['duration_normalized_geometric_monthly_pct']),'worst_full_month':mo['full_calendar_months_only'].get('worst_pct')}
screen=json.loads(Path('work/Round30-Screen.json').read_text()); annual={k:metric(k) for k in ('y1','y2','y3')}; h3=metric('harsh-3y'); h1=metric('harsh-1y')
rob={'two_positive_years':sum(x['net']>0 for x in annual.values())>=2,'worst_year_pf_ge_0_90':min(x['pf'] for x in annual.values())>=0.90}
hg={'recent_harsh_pf_ge_1_35':h1['pf']>=1.35,'recent_harsh_dd_le_6_8':h1['dd']<=6.8}
promotion=screen['selected']['pass_preliminary'] and all(rob.values()) and all(hg.values())
out={'version':'Round30 Monthly Compound','selected':screen['selected'],'annual':annual,'harsh_3y':h3,'harsh_1y':h1,'robustness_gates':rob,'harsh_gates':hg,'promotion_eligible':promotion,'decision':'PROMOTE' if promotion else 'DO_NOT_PROMOTE'}
Path('work/Round30-Final-Summary.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
PYCODE
