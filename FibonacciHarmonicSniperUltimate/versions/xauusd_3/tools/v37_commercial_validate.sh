#!/usr/bin/env bash
set -euo pipefail

ROOT='FibonacciHarmonicSniperUltimate/versions/xauusd_3'
V37="$ROOT/v37"
SRC="$V37/src/FibonacciXAUUSD3V37.cs"
PROJ="$V37/FibonacciXAUUSD3V37.csproj"
WORK="$ROOT/validation-v37-commercial"
REPORTS="$WORK/reports"
IMAGE='ghcr.io/spotware/ctrader-console:5.9.11'
CACHE="${RUNNER_TEMP:-/tmp}/xauusd-v37-cache"
PASSFILE="${RUNNER_TEMP:-/tmp}/xauusd-v37-ctrader.pwd"

: "${CTRADER_CTID:?CTRADER_CTID missing}"
: "${CTRADER_ACCOUNT:?CTRADER_ACCOUNT missing}"
: "${CTRADER_PASSWORD:?CTRADER_PASSWORD missing}"

rm -rf "$WORK" "$CACHE"
mkdir -p "$REPORTS" "$CACHE" "$V37/src" "$V37/builds" "$V37/reports"
printf '%s' "$CTRADER_PASSWORD" > "$PASSFILE"
chmod 600 "$PASSFILE"
trap 'rm -f "$PASSFILE"' EXIT

# Build v3.7 from the proven v3.6 source without modifying the v3.6 champion.
cp "$ROOT/src/FibonacciXAUUSD3.cs" "$SRC"
python3 - <<'PY'
from pathlib import Path
p=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_3/v37/src/FibonacciXAUUSD3V37.cs')
s=p.read_text()

def once(old,new):
    global s
    assert s.count(old)==1, f'marker mismatch: {old[:80]!r} count={s.count(old)}'
    s=s.replace(old,new,1)

once('public class FibonacciXAUUSD3 : Robot','public class FibonacciXAUUSD3V37 : Robot')
once('Print("VERSION xauusd_3 v3.6.0-safety-hardening");','Print("VERSION xauusd_3 v3.7.0-commercial-architecture");')
marker='''        [Parameter("H1 ATR14/ATR50 Min", DefaultValue = 1.15, MinValue = 1.00, MaxValue = 2.00, Group = "Regime")]\n        public double H1AtrExpansionMin { get; set; }\n'''
addition='''\n        [Parameter("TP Distance Multiplier", DefaultValue = 1.0, MinValue = 1.0, MaxValue = 1.4, Group = "Exit")]
        public double TakeProfitMultiplier { get; set; }

        [Parameter("Strict XAUUSD M5 Environment", DefaultValue = true, Group = "Commercial")]
        public bool StrictEnvironment { get; set; }

        [Parameter("Reject Generic Harmonic", DefaultValue = true, Group = "Commercial")]
        public bool RejectGenericHarmonic { get; set; }

        [Parameter("Require Dual-Family M5", DefaultValue = true, Group = "Commercial")]
        public bool RequireDualFamilyM5 { get; set; }

        [Parameter("Countertrend Risk Multiplier", DefaultValue = 0.60, MinValue = 0.25, MaxValue = 1.0, Group = "Commercial")]
        public double CountertrendRiskMultiplier { get; set; }

        [Parameter("Max Consumed Setups", DefaultValue = 4096, MinValue = 256, MaxValue = 20000, Group = "Commercial")]
        public int MaxConsumedSetups { get; set; }
'''
once(marker,marker+addition)
once('                double tpPips = tpDistance / Symbol.PipSize;','                double tpPips = (tpDistance / Symbol.PipSize) * TakeProfitMultiplier;')
once('        private readonly HashSet<string> _consumed = new HashSet<string>();','        private readonly HashSet<string> _consumed = new HashSet<string>();\n        private readonly Queue<string> _consumedQueue = new Queue<string>();')
once('''        protected override void OnStart()
        {
            _m15 = MarketData.GetBars(TimeFrame.Minute15, SymbolName);''','''        protected override void OnStart()
        {
            if (!ValidateEnvironment())
            {
                Stop();
                return;
            }
            _m15 = MarketData.GetBars(TimeFrame.Minute15, SymbolName);''')
once('''            Print("[SCORE] H1 20 + M15 Fib 20 + M15 Structure 15 + Harmonic 25 + M5 20");''','''            Print("[SCORE] H1 20 + M15 Fib 20 + M15 Structure 15 + recognized Harmonic 25 + M5 actual rules");
            Print("[COMMERCIAL] strictEnv={0} rejectGeneric={1} dualFamilyM5={2} countertrendRisk={3:F2}", StrictEnvironment, RejectGenericHarmonic, RequireDualFamilyM5, CountertrendRiskMultiplier);''')
once('''            _consumed.Add(key);
            string tag = harmonic.Score >= 12.0 ? "Hybrid-" + harmonic.Tag : "FibStructure";
            _armed = new ArmedSetup(direction, zoneLow, zoneHigh, stopAnchor, target, atr, preScore, tag, key, m5Index, m5Index + ConfirmWindowM5Bars);''','''            RememberConsumed(key);
            string tag = harmonic.Score >= 12.0 && harmonic.Tag != "None" ? "Hybrid-" + harmonic.Tag : "FibStructure";
            _armed = new ArmedSetup(direction, zoneLow, zoneHigh, stopAnchor, target, atr, preScore, h1Score, tag, key, m5Index, m5Index + ConfirmWindowM5Bars);''')
once('''            int rules = 0;
            if (engulfing) rules++;
            if (rejection) rules++;
            if (microBreak) rules++;
            if (momentum) rules++;
            if (rules < M5RulesNeeded)
                return false;
            double m5Score = M5RulesNeeded * 5.0;''','''            int rules = 0;
            if (engulfing) rules++;
            if (rejection) rules++;
            if (microBreak) rules++;
            if (momentum) rules++;
            if (rules < M5RulesNeeded)
                return false;
            bool triggerFamily = engulfing || rejection;
            bool continuationFamily = microBreak || momentum;
            if (RequireDualFamilyM5 && (!triggerFamily || !continuationFamily))
            {
                if (DebugLogging) Print("[M5 FAMILY REJECT] {0} {1} trigger={2} continuation={3} rules={4}/4", a.Tag, a.Direction, triggerFamily, continuationFamily, rules);
                return false;
            }
            double m5Score = rules * 5.0;''')
once('''                double budget = Account.Equity * RiskPercent / 100.0;
                double volume = Symbol.VolumeForFixedRisk(budget, slPips, RoundingMode.Down);''','''                double riskMultiplier = a.H1Score <= 3.5 ? CountertrendRiskMultiplier : 1.0;
                double budget = Account.Equity * RiskPercent / 100.0 * riskMultiplier;
                double volume = Symbol.VolumeForFixedRisk(budget, slPips, RoundingMode.Down);''')
once('''                string comment = a.Tag + "|" + finalScore.ToString("F1") + "|M5R" + confirmRules;''','''                string comment = a.Tag + "|" + finalScore.ToString("F1") + "|M5R" + confirmRules + "|H1" + a.H1Score.ToString("F0");''')
once('''                _openMeta[result.Position.Id] = new TradeMeta(a.Tag, a.Direction, finalScore, rr, confirmRules, session);''','''                _openMeta[result.Position.Id] = new TradeMeta(a.Tag, a.Direction, finalScore, rr, confirmRules, session, a.H1Score, riskMultiplier);''')
once('''                Print("[OPEN] {0} {1} session={2} score={3:F1} rules={4}/4 vol={5} entry={6:F2} SL={7:F1}p TP={8:F1}p RR={9:F2}", a.Tag, a.Direction, session, finalScore, confirmRules, volume, result.Position.EntryPrice, slPips, tpPips, rr);''','''                Print("[OPEN] {0} {1} session={2} score={3:F1} rules={4}/4 H1={5:F1} riskX={6:F2} vol={7} entry={8:F2} SL={9:F1}p TP={10:F1}p RR={11:F2}", a.Tag, a.Direction, session, finalScore, confirmRules, a.H1Score, riskMultiplier, volume, result.Position.EntryPrice, slPips, tpPips, rr);''')
once('''            else { ratioScore = 6.0; tag = "Generic"; }
            double symmetryScore = Clamp((symmetry - 0.55) / 0.45 * 7.0, 0, 7.0);''','''            else
            {
                if (RejectGenericHarmonic)
                    return new HarmonicInfo(0.0, "None");
                ratioScore = 6.0;
                tag = "Generic";
            }
            double symmetryScore = Clamp((symmetry - 0.55) / 0.45 * 7.0, 0, 7.0);''')
once('''        private bool BarTouchesZone(Bars bars, int index, double zoneLow, double zoneHigh)
''','''        private bool ValidateEnvironment()
        {
            if (!StrictEnvironment) return true;
            bool symbolOk = SymbolName != null && SymbolName.ToUpperInvariant().StartsWith("XAUUSD");
            bool timeframeOk = Bars != null && Bars.TimeFrame == TimeFrame.Minute5;
            if (!symbolOk || !timeframeOk)
            {
                Print("[ENV REJECT] v3.7 requires XAUUSD on M5. symbol={0} timeframe={1}", SymbolName, Bars == null ? "null" : Bars.TimeFrame.ToString());
                return false;
            }
            return true;
        }

        private void RememberConsumed(string key)
        {
            if (_consumed.Add(key)) _consumedQueue.Enqueue(key);
            while (_consumedQueue.Count > MaxConsumedSetups)
            {
                string expired = _consumedQueue.Dequeue();
                _consumed.Remove(expired);
            }
        }

        private bool BarTouchesZone(Bars bars, int index, double zoneLow, double zoneHigh)
''')
once('''            Print("[CLOSE] {0} {1} session={2} score={3:F1} rules={4}/4 RR={5:F2} net={6:F2} reason={7}", meta.Tag, meta.Direction, meta.Session, meta.Score, meta.ConfirmRules, meta.Rr, p.NetProfit, args.Reason);''','''            Print("[CLOSE] {0} {1} session={2} score={3:F1} rules={4}/4 H1={5:F1} riskX={6:F2} RR={7:F2} net={8:F2} reason={9}", meta.Tag, meta.Direction, meta.Session, meta.Score, meta.ConfirmRules, meta.H1Score, meta.RiskMultiplier, meta.Rr, p.NetProfit, args.Reason);''')
once('''            public ArmedSetup(TradeType direction, double zoneLow, double zoneHigh, double stopAnchor, double target, double m15Atr, double preScore, string tag, string key, int armedM5Index, int expiresM5Index)
            {
                Direction = direction; ZoneLow = zoneLow; ZoneHigh = zoneHigh; StopAnchor = stopAnchor; Target = target; M15Atr = m15Atr; PreScore = preScore; Tag = tag; Key = key; ArmedM5Index = armedM5Index; ExpiresM5Index = expiresM5Index;
            }
            public TradeType Direction; public double ZoneLow; public double ZoneHigh; public double StopAnchor; public double Target; public double M15Atr; public double PreScore; public string Tag; public string Key; public int ArmedM5Index; public int ExpiresM5Index;''','''            public ArmedSetup(TradeType direction, double zoneLow, double zoneHigh, double stopAnchor, double target, double m15Atr, double preScore, double h1Score, string tag, string key, int armedM5Index, int expiresM5Index)
            {
                Direction = direction; ZoneLow = zoneLow; ZoneHigh = zoneHigh; StopAnchor = stopAnchor; Target = target; M15Atr = m15Atr; PreScore = preScore; H1Score = h1Score; Tag = tag; Key = key; ArmedM5Index = armedM5Index; ExpiresM5Index = expiresM5Index;
            }
            public TradeType Direction; public double ZoneLow; public double ZoneHigh; public double StopAnchor; public double Target; public double M15Atr; public double PreScore; public double H1Score; public string Tag; public string Key; public int ArmedM5Index; public int ExpiresM5Index;''')
once('''            public TradeMeta(string tag, TradeType direction, double score, double rr, int confirmRules, string session)
            {
                Tag = tag; Direction = direction; Score = score; Rr = rr; ConfirmRules = confirmRules; Session = session;
            }
            public string Tag; public TradeType Direction; public double Score; public double Rr; public int ConfirmRules; public string Session;''','''            public TradeMeta(string tag, TradeType direction, double score, double rr, int confirmRules, string session, double h1Score, double riskMultiplier)
            {
                Tag = tag; Direction = direction; Score = score; Rr = rr; ConfirmRules = confirmRules; Session = session; H1Score = h1Score; RiskMultiplier = riskMultiplier;
            }
            public string Tag; public TradeType Direction; public double Score; public double Rr; public int ConfirmRules; public string Session; public double H1Score; public double RiskMultiplier;''')
p.write_text(s)
PY

cat > "$PROJ" <<'EOF'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
    <ImplicitUsings>disable</ImplicitUsings>
    <Nullable>disable</Nullable>
    <RootNamespace>cAlgo.Robots</RootNamespace>
    <AlgoName>FibonacciXAUUSD3-v3.7-Commercial</AlgoName>
    <AlgoType>Robot</AlgoType>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="cTrader.Automate" Version="1.*-*" />
  </ItemGroup>
</Project>
EOF

grep -q 'v3.7.0-commercial-architecture' "$SRC"
grep -q 'Require Dual-Family M5' "$SRC"
grep -q 'Reject Generic Harmonic' "$SRC"
grep -q 'Countertrend Risk Multiplier' "$SRC"
grep -q 'Bars.TimeFrame == TimeFrame.Minute5' "$SRC"

docker pull "$IMAGE"
docker run --rm --entrypoint sh -v "$PWD:/repo" -w /repo "$IMAGE" -c "dotnet restore '$PROJ' && dotnet build '$PROJ' -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True"
ALGO="$(find "$V37" -type f -name '*.algo' ! -path '*/builds/*' -print -quit)"
test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" "$WORK/FibonacciXAUUSD3-v3.7-candidate.algo"

run_bt() {
  local variant="$1" generic="$2" dual="$3" ctrisk="$4" segment="$5" cost="$6" start="$7" end="$8" spread="$9" commission="${10}"
  local label="${variant}-${segment}-${cost}"
  echo "=== BACKTEST $label ==="
  docker run --rm \
    -v "$PWD/$WORK:/work" -v "$PASSFILE:/run/ctrader.pwd:ro" -v "$CACHE:/cache" \
    -e "CTID=$CTRADER_CTID" -e 'PWD-FILE=/run/ctrader.pwd' -e "ACCOUNT=$CTRADER_ACCOUNT" \
    "$IMAGE" backtest /work/FibonacciXAUUSD3-v3.7-candidate.algo \
    --environment-variables --exit-on-stop --symbol=XAUUSD --period=m5 --start="$start" --end="$end" \
    --balance=10000 --data-mode=m1 --data-dir=/cache --commission="$commission" --spread="$spread" \
    --RiskPercent=0.50 --MaxDailyLossPercent=3 --MinimumRiskReward=1.5 \
    --PreScoreMin=42 --FinalScoreMin=60 --M5PreScoreFloor=50 --M5RulesNeeded=2 \
    --MinImpulseAtr=1.2 --MinStopAtr=0.20 --MaxAllowedRR=8 --BuyH1MinScore=18 \
    --BlockLondonEntries=true --RequireH1AtrExpansion=true --H1AtrExpansionMin=1.15 \
    --TakeProfitMultiplier=1.0 --StrictEnvironment=true \
    --RejectGenericHarmonic="$generic" --RequireDualFamilyM5="$dual" --CountertrendRiskMultiplier="$ctrisk" \
    --report="/work/reports/${label}.html" --report-json="/work/reports/${label}.json" \
    2>&1 | tee "$REPORTS/${label}.log"
  test -s "$REPORTS/${label}.json"
}

# Candidate definitions preserve attribution of each structural change.
CANDIDATES=(
  'compat false false 1.00'
  'semantic true false 1.00'
  'dual true true 1.00'
  'balanced true true 0.60'
)

for spec in "${CANDIDATES[@]}"; do
  set -- $spec; v="$1"; generic="$2"; dual="$3"; ctrisk="$4"
  run_bt "$v" "$generic" "$dual" "$ctrisk" 1y standard 09/09/2025 09/09/2026 17.42 35
  run_bt "$v" "$generic" "$dual" "$ctrisk" 1y harsh    09/09/2025 09/09/2026 30 50
  run_bt "$v" "$generic" "$dual" "$ctrisk" oos1 standard 09/09/2025 09/03/2026 17.42 35
  run_bt "$v" "$generic" "$dual" "$ctrisk" oos1 harsh    09/09/2025 09/03/2026 30 50
  run_bt "$v" "$generic" "$dual" "$ctrisk" oos2 standard 09/03/2026 09/09/2026 17.42 35
  run_bt "$v" "$generic" "$dual" "$ctrisk" oos2 harsh    09/03/2026 09/09/2026 30 50
done

python3 - <<'PY'
import json, datetime
from pathlib import Path
root=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_3')
work=root/'validation-v37-commercial'; reports=work/'reports'
variants=['compat','semantic','dual','balanced']
rows=[]
for v in variants:
  for seg in ['1y','oos1','oos2']:
    for cost in ['standard','harsh']:
      d=json.loads((reports/f'{v}-{seg}-{cost}.json').read_text())
      ts=d['tradeStatistics']; main=d['main']; eq=d['equity']; hist=d.get('history',{}).get('items',[])
      trades=int(ts['totalTrades']['all']); wins=int(ts['winningTrades']['all']); net=float(main['netProfit']); roi=float(main['roi']); pf=float(ts['profitFactor']['all']); dd=float(eq['maxEquityDrawdownPercent'])
      spans=sorted((int(x['entryTime']),int(x['closeTime']),x['direction']) for x in hist)
      overlap=hedge=0
      for i,a in enumerate(spans):
        for b in spans[i+1:]:
          if b[0]>=a[1]: break
          overlap+=1; hedge+=int(a[2]!=b[2])
      london=sum(1 for x in hist if 7<=datetime.datetime.fromtimestamp(int(x['entryTime'])/1000,datetime.timezone.utc).hour<13)
      rows.append(dict(v=v,seg=seg,cost=cost,trades=trades,wins=wins,wr=100*wins/trades if trades else 0,net=net,roi=roi,pf=pf,dd=dd,overlap=overlap,hedge=hedge,london=london))

def get(v,seg,cost): return next(r for r in rows if r['v']==v and r['seg']==seg and r['cost']==cost)
rank=[]
for v in variants:
  yS=get(v,'1y','standard'); yH=get(v,'1y','harsh'); aH=get(v,'oos1','harsh'); bH=get(v,'oos2','harsh')
  safety=all(r['overlap']==0 and r['hedge']==0 and r['london']==0 for r in rows if r['v']==v)
  gate=(v!='compat' and safety and yS['trades']>=50 and yS['roi']>=18 and yH['roi']>=15 and yS['pf']>=1.75 and yH['pf']>=1.65 and max(yS['dd'],yH['dd'])<=5.75 and aH['trades']>=15 and aH['net']>0 and aH['pf']>=1.25 and bH['trades']>=15 and bH['net']>0 and bH['pf']>=1.50)
  score=yH['roi'] + 0.65*min(aH['roi'],bH['roi']) + 2.0*(min(yH['pf'],aH['pf'],bH['pf'])-1.0) - max(0,max(yS['dd'],yH['dd'])-5.0)
  rank.append((gate,score,v))
rank.sort(reverse=True)
winner=next((v for gate,score,v in rank if gate), '')
(work/'winner.txt').write_text(winner+'\n')
lines=['# XAUUSD v3.7 Commercial Architecture Validation','', '| Variant | Segment | Cost | Trades | Win % | Net | ROI % | PF | DD % | Overlap | Hedge | London |','|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
  lines.append(f"| {r['v']} | {r['seg']} | {r['cost']} | {r['trades']} | {r['wr']:.2f} | {r['net']:.2f} | {r['roi']:.2f} | {r['pf']:.2f} | {r['dd']:.2f} | {r['overlap']} | {r['hedge']} | {r['london']} |")
lines += ['', '## Commercial ranking','']
for gate,score,v in rank: lines.append(f'- {v}: score={score:.2f}; gate={"PASS" if gate else "FAIL"}')
lines += ['', f'**Selected structural candidate: {winner if winner else "NONE"}**']
(work/'V37_COMMERCIAL_REPORT.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
if not winner:
  raise SystemExit('No structural candidate passed the commercial gate; do not seal.')
PY

WINNER="$(cat "$WORK/winner.txt")"
case "$WINNER" in
  semantic) GENERIC=true; DUAL=false; CTRISK=1.00 ;;
  dual) GENERIC=true; DUAL=true; CTRISK=1.00 ;;
  balanced) GENERIC=true; DUAL=true; CTRISK=0.60 ;;
  *) echo 'Invalid winner'; exit 1 ;;
esac

# Final cross-window checks on the selected structural candidate.
run_bt "$WINNER" "$GENERIC" "$DUAL" "$CTRISK" 3m standard 09/06/2026 09/09/2026 17.42 35
run_bt "$WINNER" "$GENERIC" "$DUAL" "$CTRISK" 3m harsh    09/06/2026 09/09/2026 30 50
run_bt "$WINNER" "$GENERIC" "$DUAL" "$CTRISK" 6m standard 09/03/2026 09/09/2026 17.42 35
run_bt "$WINNER" "$GENERIC" "$DUAL" "$CTRISK" 6m harsh    09/03/2026 09/09/2026 30 50

python3 - <<'PY'
import json
from pathlib import Path
root=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_3'); work=root/'validation-v37-commercial'; reports=work/'reports'; v=(work/'winner.txt').read_text().strip()
lines=['','## Final short-window verification','', '| Window | Cost | Trades | Win % | Net | ROI % | PF | DD % |','|---|---|---:|---:|---:|---:|---:|---:|']
ok=True
for seg in ['3m','6m']:
  for cost in ['standard','harsh']:
    d=json.loads((reports/f'{v}-{seg}-{cost}.json').read_text()); ts=d['tradeStatistics']; m=d['main']; eq=d['equity']
    tr=int(ts['totalTrades']['all']); wi=int(ts['winningTrades']['all']); net=float(m['netProfit']); roi=float(m['roi']); pf=float(ts['profitFactor']['all']); dd=float(eq['maxEquityDrawdownPercent']); wr=100*wi/tr if tr else 0
    lines.append(f'| {seg} | {cost} | {tr} | {wr:.2f} | {net:.2f} | {roi:.2f} | {pf:.2f} | {dd:.2f} |')
    ok &= tr>=5 and net>0 and pf>1.0 and dd<=6.0
rep=work/'V37_COMMERCIAL_REPORT.md'; rep.write_text(rep.read_text()+'\n'.join(lines)+'\n')
if not ok: raise SystemExit('Winner failed 3M/6M final verification; do not seal.')
(work/'COMMERCIAL_PASS').write_text(v+'\n')
PY

# Make the winning configuration the source defaults, then rebuild a mobile/cloud-ready final package.
python3 - <<'PY'
from pathlib import Path
root=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_3'); work=root/'validation-v37-commercial'; p=root/'v37/src/FibonacciXAUUSD3V37.cs'; s=p.read_text(); v=(work/'winner.txt').read_text().strip()
vals={'semantic':('true','false','1.00'),'dual':('true','true','1.00'),'balanced':('true','true','0.60')}[v]
generic,dual,ctrisk=vals
import re
s=re.sub(r'\[Parameter\("Reject Generic Harmonic", DefaultValue = (?:true|false),', f'[Parameter("Reject Generic Harmonic", DefaultValue = {generic},', s, count=1)
s=re.sub(r'\[Parameter\("Require Dual-Family M5", DefaultValue = (?:true|false),', f'[Parameter("Require Dual-Family M5", DefaultValue = {dual},', s, count=1)
s=re.sub(r'\[Parameter\("Countertrend Risk Multiplier", DefaultValue = [0-9.]+,', f'[Parameter("Countertrend Risk Multiplier", DefaultValue = {ctrisk},', s, count=1)
p.write_text(s)
(root/'v37/reports/COMMERCIAL-SEAL.md').write_text((work/'V37_COMMERCIAL_REPORT.md').read_text()+f'\n## Seal\n\n**SEALED: Fibonacci XAUUSD v3.7 Commercial / {v}**\n')
PY

docker run --rm --entrypoint sh -v "$PWD:/repo" -w /repo "$IMAGE" -c "dotnet build '$PROJ' -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True"
FINAL_ALGO="$(find "$V37" -type f -name '*.algo' ! -path '*/builds/*' -print -quit)"
test -s "$FINAL_ALGO"
cp "$FINAL_ALGO" "$V37/builds/FibonacciXAUUSD3-v3.7-Commercial-FINAL.algo"
sha256sum "$V37/builds/FibonacciXAUUSD3-v3.7-Commercial-FINAL.algo" > "$V37/builds/FibonacciXAUUSD3-v3.7-Commercial-FINAL.sha256"

# Credential hygiene: no password file is ever copied into WORK or release artifacts.
! find "$WORK" "$V37" -type f -name '*pwd*' -o -name '*password*' | grep -q .

echo "SEALED $WINNER"
