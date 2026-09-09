#!/usr/bin/env bash
set -euo pipefail

mkdir -p work/r26-src work/store-src work/growth-src work/build work/cache \
  work/conservative-3y work/balanced-3y work/responsive-3y \
  work/recent-a work/recent-b work/y1 work/y2 work/harsh-3y work/harsh-y3

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
python3 FibonacciHarmonicSniperUltimate/versions/v0.23.0-btc-round26-core-refactor/round26_transform.py work/Round22.cs work/r26-src/BTC-Harmonic-Guard-Control.cs
rm -f work/r26-src/Round22.cs
cp work/r26-src/*.cs work/store-src/
python3 FibonacciHarmonicSniperUltimate/store-v1/store_v1_transform.py work/store-src/BTC-Harmonic-Guard-Control.cs work/store-src/BTC-Harmonic-Guard.cs
rm -f work/store-src/BTC-Harmonic-Guard-Control.cs
cp work/store-src/*.cs work/growth-src/
python3 FibonacciHarmonicSniperUltimate/monthly-growth/growth_alpha_transform.py work/growth-src/BTC-Harmonic-Guard.cs work/growth-src/BTC-Harmonic-Guard-Growth.cs
rm -f work/growth-src/BTC-Harmonic-Guard.cs work/Round18.cs work/Round21.cs work/Round22.cs

cat > work/growth-src/Growth.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><TargetFramework>net6.0</TargetFramework><ImplicitUsings>disable</ImplicitUsings><Nullable>disable</Nullable><RootNamespace>cAlgo.Robots</RootNamespace><AlgoName>BTC-Harmonic-Guard-Growth</AlgoName></PropertyGroup>
  <ItemGroup><PackageReference Include="cTrader.Automate" Version="1.0.19" /></ItemGroup>
</Project>
EOF

dotnet restore work/growth-src/Growth.csproj
dotnet build work/growth-src/Growth.csproj -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True
ALGO=$(find work/growth-src/bin/Release -type f -name '*.algo' | head -n1)
cp "$ALGO" work/build/BTC-Harmonic-Guard-Growth.algo
sha256sum work/build/BTC-Harmonic-Guard-Growth.algo > work/build/SHA256SUMS.txt

: "${CTRADER_CTID:?missing CTRADER_CTID}"; : "${CTRADER_ACCOUNT:?missing CTRADER_ACCOUNT}"; : "${CTRADER_PASSWORD:?missing CTRADER_PASSWORD}"
printf '%s' "$CTRADER_PASSWORD" | tr -d '\r\n' > work/ctrader.pwd; chmod 600 work/ctrader.pwd
docker pull ghcr.io/spotware/ctrader-console:5.9.11

run_case() {
  name="$1"; start="$2"; end="$3"; commission="$4"; spread="$5"; risk="$6"; rr="$7"; stopatr="$8"; pull="$9"; body="${10}"
  docker run --rm -v "$PWD/work:/work" -e "CTID=$CTRADER_CTID" -e 'PWD-FILE=/work/ctrader.pwd' -e "ACCOUNT=$CTRADER_ACCOUNT" \
    ghcr.io/spotware/ctrader-console:5.9.11 backtest /work/build/BTC-Harmonic-Guard-Growth.algo \
    --environment-variables --exit-on-stop --symbol=BITCOIN --period=h1 --start="$start" --end="$end" --balance=10000 --data-mode=m1 --data-dir=/work/cache \
    --commission="$commission" --spread="$spread" --GrowthAlphaEnabled=true --GrowthRiskPercent="$risk" --GrowthRiskReward="$rr" --GrowthStopAtr="$stopatr" --GrowthPullbackBars="$pull" --GrowthBodyAtr="$body" \
    --report="/work/$name/report.html" --report-json="/work/$name/report.json" > "work/$name/report.log" 2>&1
}

# Three precommitted profiles; no brute-force optimization.
run_case conservative-3y '08/09/2023 00:00' '08/09/2026 00:00' 65 0 0.25 1.90 1.60 3 0.20
run_case balanced-3y     '08/09/2023 00:00' '08/09/2026 00:00' 65 0 0.30 1.80 1.50 4 0.15
run_case responsive-3y   '08/09/2023 00:00' '08/09/2026 00:00' 65 0 0.35 1.70 1.40 5 0.12

python3 - <<'PYCODE'
import json
from pathlib import Path
profiles={
 'conservative':{'risk':0.25,'rr':1.90,'stop':1.60,'pull':3,'body':0.20},
 'balanced':{'risk':0.30,'rr':1.80,'stop':1.50,'pull':4,'body':0.15},
 'responsive':{'risk':0.35,'rr':1.70,'stop':1.40,'pull':5,'body':0.12}}
def m(path):
 r=json.loads(Path(path).read_text()); return {'trades':int(r['tradeStatistics']['totalTrades']['all']),'roi':float(r['main']['roi']),'net':float(r['main']['netProfit']),'pf':float(r['tradeStatistics']['profitFactor']['all']),'dd':float(r['equity']['maxEquityDrawdownPercent']),'balance_dd':float(r['balance']['maxBalanceDrawdownPercent'])}
rows=[]
for n,c in profiles.items():
 x=m(f'work/{n}-3y/report.json')
 g={'trades_ge_280':x['trades']>=280,'roi_gt_26_55':x['roi']>26.55,'pf_ge_1_22':x['pf']>=1.22,'dd_le_21_90':x['dd']<=21.90}
 rows.append({'profile':n,'config':c,'metrics':x,'gates':g,'gate_count':sum(g.values()),'pass_all':all(g.values())})
rows.sort(key=lambda z:(z['pass_all'],z['gate_count'],z['metrics']['pf'],z['metrics']['roi'],-z['metrics']['dd'],z['metrics']['trades']),reverse=True)
out={'baseline_3y':{'trades':256,'roi':26.55,'pf':1.22,'dd':21.893009225762995},'profiles':rows,'top2':[rows[0]['profile'],rows[1]['profile']]}
Path('work/Growth-3Y-Screen.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
PYCODE

top1=$(python3 -c "import json; print(json.load(open('work/Growth-3Y-Screen.json'))['top2'][0])")
top2=$(python3 -c "import json; print(json.load(open('work/Growth-3Y-Screen.json'))['top2'][1])")
getcfg(){ python3 - "$1" "$2" <<'PYCODE'
import sys
p=sys.argv[1]; k=sys.argv[2]
c={'conservative':{'risk':.25,'rr':1.90,'stop':1.60,'pull':3,'body':.20},'balanced':{'risk':.30,'rr':1.80,'stop':1.50,'pull':4,'body':.15},'responsive':{'risk':.35,'rr':1.70,'stop':1.40,'pull':5,'body':.12}}
print(c[p][k])
PYCODE
}
run_profile(){ n="$1"; out="$2"; start="$3"; end="$4"; commission="$5"; spread="$6"; run_case "$out" "$start" "$end" "$commission" "$spread" "$(getcfg "$n" risk)" "$(getcfg "$n" rr)" "$(getcfg "$n" stop)" "$(getcfg "$n" pull)" "$(getcfg "$n" body)"; }
run_profile "$top1" recent-a '08/09/2025 00:00' '08/09/2026 00:00' 65 0
run_profile "$top2" recent-b '08/09/2025 00:00' '08/09/2026 00:00' 65 0

python3 - <<'PYCODE'
import json,math
from pathlib import Path
screen=json.loads(Path('work/Growth-3Y-Screen.json').read_text())

def m(path):
 r=json.loads(Path(path).read_text()); roi=float(r['main']['roi']);
 return {'trades':int(r['tradeStatistics']['totalTrades']['all']),'roi':roi,'monthly_compound_equiv':((1+roi/100.0)**(1/12.0)-1)*100.0,'net':float(r['main']['netProfit']),'pf':float(r['tradeStatistics']['profitFactor']['all']),'dd':float(r['equity']['maxEquityDrawdownPercent'])}
rows=[]
for outname,profile in [('recent-a',screen['top2'][0]),('recent-b',screen['top2'][1])]:
 x=m(f'work/{outname}/report.json')
 g={'trades_ge_105':x['trades']>=105,'roi_gt_39_93':x['roi']>39.93,'pf_ge_1_80':x['pf']>=1.80,'dd_le_6':x['dd']<=6.0,'monthly_compound_gt_baseline':x['monthly_compound_equiv']>2.84}
 rows.append({'profile':profile,'metrics':x,'gates':g,'gate_count':sum(g.values()),'pass_all':all(g.values())})
rows.sort(key=lambda z:(z['pass_all'],z['gate_count'],z['metrics']['monthly_compound_equiv'],z['metrics']['pf'],-z['metrics']['dd']),reverse=True)
sel=rows[0]['profile']
out={'baseline_recent':{'trades':95,'roi':39.93,'monthly_compound_equiv':2.84,'pf':1.95,'dd':5.646323173396001},'top2_recent':rows,'selected':sel}
Path('work/Growth-Recent-Screen.json').write_text(json.dumps(out,indent=2)); Path('work/selected-growth.txt').write_text(sel); print(json.dumps(out,indent=2))
PYCODE

sel=$(cat work/selected-growth.txt)
run_profile "$sel" y1       '08/09/2023 00:00' '08/09/2024 00:00' 65 0
run_profile "$sel" y2       '08/09/2024 00:00' '08/09/2025 00:00' 65 0
# selected recent-year report already exists as recent-a or recent-b; harsh checks below
run_profile "$sel" harsh-3y '08/09/2023 00:00' '08/09/2026 00:00' 100 1500
run_profile "$sel" harsh-y3 '08/09/2025 00:00' '08/09/2026 00:00' 100 1500

python3 - <<'PYCODE'
import json,datetime,calendar,math
from pathlib import Path
screen=json.loads(Path('work/Growth-3Y-Screen.json').read_text()); recent=json.loads(Path('work/Growth-Recent-Screen.json').read_text()); sel=recent['selected']
recent_out='recent-a' if screen['top2'][0]==sel else 'recent-b'
def load(path): return json.loads(Path(path).read_text())
def m(path):
 r=load(path); roi=float(r['main']['roi']); return {'trades':int(r['tradeStatistics']['totalTrades']['all']),'roi':roi,'monthly_compound_equiv':((1+roi/100.0)**(1/12.0)-1)*100.0,'net':float(r['main']['netProfit']),'pf':float(r['tradeStatistics']['profitFactor']['all']),'dd':float(r['equity']['maxEquityDrawdownPercent']),'balance_dd':float(r['balance']['maxBalanceDrawdownPercent'])}
def monthly(path):
 r=load(path); items=sorted(r['history']['items'],key=lambda x:x['closeTime']); by={}
 for x in items:
  k=x['closeTime'][:7]; by[k]=by.get(k,0.0)+float(x['net'])
 months=[]; y,mn=2025,9; end=(2026,9); eq=10000.0
 while (y,mn)<=end:
  k=f'{y:04d}-{mn:02d}'; net=by.get(k,0.0); ret=100*net/eq if eq else 0; months.append({'month':k,'net':round(net,2),'return_pct':round(ret,4)}); eq+=net
  mn+=1
  if mn==13: y+=1; mn=1
 return months
annual={'y1':m('work/y1/report.json'),'y2':m('work/y2/report.json'),'y3':m(f'work/{recent_out}/report.json')}
h3=m('work/harsh-3y/report.json'); hy=m('work/harsh-y3/report.json'); mm=monthly(f'work/{recent_out}/report.json')
gates={'3y':next(x for x in screen['profiles'] if x['profile']==sel)['pass_all'],'recent':next(x for x in recent['top2_recent'] if x['profile']==sel)['pass_all'],'positive_years_ge_2':sum(v['net']>0 for v in annual.values())>=2,'worst_year_pf_ge_0_90':min(v['pf'] for v in annual.values())>=.90,'harsh3y_pf_ge_1':h3['pf']>=1.0,'harsh3y_roi_nonnegative':h3['roi']>=0,'harsh_recent_pf_ge_1_35':hy['pf']>=1.35,'harsh_recent_dd_le_6_8':hy['dd']<=6.8}
out={'selected':sel,'selected_3y':next(x for x in screen['profiles'] if x['profile']==sel)['metrics'],'recent':annual['y3'],'monthly_returns':mm,'positive_months':sum(x['return_pct']>0 for x in mm),'negative_months':sum(x['return_pct']<0 for x in mm),'worst_month':min(mm,key=lambda x:x['return_pct']),'best_month':max(mm,key=lambda x:x['return_pct']),'annual':annual,'harsh_3y':h3,'harsh_recent':hy,'gates':gates,'promotion_eligible':all(gates.values())}
Path('work/Growth-Final-Summary.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
PYCODE
