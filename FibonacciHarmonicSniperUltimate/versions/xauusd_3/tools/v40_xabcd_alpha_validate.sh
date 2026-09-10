#!/usr/bin/env bash
set -euo pipefail

ROOT='FibonacciHarmonicSniperUltimate/versions/xauusd_3'
SRC="$ROOT/src/FibonacciXAUUSD3.cs"
WORK="$ROOT/validation-v40-xabcd"
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
s=s.replace('Print("VERSION xauusd_3 v3.6.0-safety-hardening");','Print("VERSION xauusd_4 v4.0.0-xabcd-alpha-candidate");',1)

marker='''        [Parameter("H1 ATR14/ATR50 Min", DefaultValue = 1.15, MinValue = 1.00, MaxValue = 2.00, Group = "Regime")]\n        public double H1AtrExpansionMin { get; set; }\n'''
addition='''\n        [Parameter("Enable True XABCD Alpha", DefaultValue = false, Group = "Harmonic Alpha")]
        public bool EnableTrueXabcdAlpha { get; set; }

        [Parameter("XABCD Geometry Min", DefaultValue = 0.70, MinValue = 0.50, MaxValue = 0.95, Group = "Harmonic Alpha")]
        public double XabcdGeometryMin { get; set; }

        [Parameter("XABCD PreScore Min", DefaultValue = 64.0, MinValue = 45, MaxValue = 85, Group = "Harmonic Alpha")]
        public double XabcdPreScoreMin { get; set; }

        [Parameter("XABCD Target AD Fib", DefaultValue = 0.50, MinValue = 0.30, MaxValue = 0.786, Group = "Harmonic Alpha")]
        public double XabcdTargetAdFib { get; set; }

        [Parameter("XABCD Max Age M15", DefaultValue = 4, MinValue = 1, MaxValue = 12, Group = "Harmonic Alpha")]
        public int XabcdMaxAgeM15 { get; set; }
'''
assert s.count(marker)==1
s=s.replace(marker,marker+addition,1)

old='''            List<Pivot> pivots = BuildPivots(index);\n            if (pivots.Count < 2)\n                return;\n'''
new='''            List<Pivot> pivots = BuildPivots(index);
            if (EnableTrueXabcdAlpha && TryArmTrueXabcd(pivots, index, atr, m5Index))
                return;
            if (pivots.Count < 2)
                return;
'''
assert s.count(old)==1
s=s.replace(old,new,1)

insert='''        private bool TryArmTrueXabcd(List<Pivot> pivots, int index, double atr, int m5Index)
        {
            if (pivots == null || pivots.Count < 5 || atr <= Symbol.PipSize)
                return false;

            Pivot x = pivots[pivots.Count - 5];
            Pivot a = pivots[pivots.Count - 4];
            Pivot b = pivots[pivots.Count - 3];
            Pivot c = pivots[pivots.Count - 2];
            Pivot d = pivots[pivots.Count - 1];
            if (index - d.Index > XabcdMaxAgeM15)
                return false;
            if (x.IsHigh == a.IsHigh || a.IsHigh == b.IsHigh || b.IsHigh == c.IsHigh || c.IsHigh == d.IsHigh)
                return false;

            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            double bc = Math.Abs(c.Price - b.Price);
            double cd = Math.Abs(d.Price - c.Price);
            if (xa <= Symbol.PipSize || ab <= Symbol.PipSize || bc <= Symbol.PipSize || cd <= Symbol.PipSize)
                return false;

            double br = ab / xa;
            double bcr = bc / ab;
            double cdr = cd / bc;
            double dr = Math.Abs(d.Price - a.Price) / xa;

            string family = "None";
            double best = 0.0;
            double q;

            q = 0.35 * FitTarget(br, 0.618, 0.12) + 0.35 * FitTarget(dr, 0.786, 0.12)
                + 0.15 * FitRange(bcr, 0.382, 0.886, 0.22) + 0.15 * FitRange(cdr, 1.13, 1.75, 0.45);
            if (q > best) { best = q; family = "Gartley"; }

            q = 0.25 * FitRange(br, 0.382, 0.50, 0.12) + 0.40 * FitTarget(dr, 0.886, 0.11)
                + 0.15 * FitRange(bcr, 0.382, 0.886, 0.22) + 0.20 * FitRange(cdr, 1.50, 2.75, 0.55);
            if (q > best) { best = q; family = "Bat"; }

            q = 0.35 * FitTarget(br, 0.786, 0.11) + 0.35 * FitTarget(dr, 1.27, 0.18)
                + 0.15 * FitRange(bcr, 0.382, 0.886, 0.22) + 0.15 * FitRange(cdr, 1.50, 2.75, 0.55);
            if (q > best) { best = q; family = "Butterfly"; }

            q = 0.25 * FitRange(br, 0.382, 0.618, 0.14) + 0.40 * FitTarget(dr, 1.618, 0.22)
                + 0.15 * FitRange(bcr, 0.382, 0.886, 0.22) + 0.20 * FitRange(cdr, 2.00, 3.75, 0.75);
            if (q > best) { best = q; family = "Crab"; }

            q = 0.30 * FitTarget(br, 0.886, 0.11) + 0.40 * FitTarget(dr, 1.618, 0.22)
                + 0.15 * FitRange(bcr, 0.382, 0.886, 0.22) + 0.15 * FitRange(cdr, 2.00, 3.75, 0.75);
            if (q > best) { best = q; family = "DeepCrab"; }

            if (best < XabcdGeometryMin)
                return false;

            TradeType direction = d.IsHigh ? TradeType.Sell : TradeType.Buy;
            double h1Score = H1RegimeScore(direction);
            double atrRatio = H1AtrExpansionRatio();
            double volScore = Clamp((atrRatio - 0.90) / 0.45 * 10.0, 0.0, 10.0);
            double proximityAtr = Math.Abs(_m15.ClosePrices[index] - d.Price) / atr;
            if (proximityAtr > 1.25)
                return false;
            double proximityScore = Clamp(10.0 - proximityAtr * 6.0, 2.0, 10.0);
            double geometryScore = best * 45.0;
            double preScore = geometryScore + h1Score + volScore + proximityScore;
            if (preScore < XabcdPreScoreMin)
                return false;

            double ad = Math.Abs(a.Price - d.Price);
            if (ad <= atr * 0.5)
                return false;
            double target = direction == TradeType.Buy ? d.Price + ad * XabcdTargetAdFib : d.Price - ad * XabcdTargetAdFib;
            double zoneHalf = atr * 0.30;
            double zoneLow = d.Price - zoneHalf;
            double zoneHigh = d.Price + zoneHalf;
            double stopAnchor = d.Price;
            string key = "XABCD|" + family + "|" + direction + "|" + x.Index + "|" + a.Index + "|" + b.Index + "|" + c.Index + "|" + d.Index;
            if (_consumed.Contains(key))
                return false;

            _consumed.Add(key);
            string tag = "XABCD-" + family;
            _armed = new ArmedSetup(direction, zoneLow, zoneHigh, stopAnchor, target, atr, preScore, tag, key, m5Index, m5Index + ConfirmWindowM5Bars);
            Print("[XABCD ARM] {0} {1} geom={2:F3} pre={3:F1} B={4:F3} BC={5:F3} CD={6:F3} AD/XA={7:F3} D={8:F2} target={9:F2}", family, direction, best, preScore, br, bcr, cdr, dr, d.Price, target);
            return true;
        }

        private double FitTarget(double value, double target, double tolerance)
        {
            if (tolerance <= 0.0) return 0.0;
            return Clamp(1.0 - Math.Abs(value - target) / tolerance, 0.0, 1.0);
        }

        private double FitRange(double value, double low, double high, double tolerance)
        {
            if (value >= low && value <= high) return 1.0;
            if (tolerance <= 0.0) return 0.0;
            double distance = value < low ? low - value : value - high;
            return Clamp(1.0 - distance / tolerance, 0.0, 1.0);
        }

'''
needle='''        private HarmonicInfo HarmonicConfluence(List<Pivot> pivots, double zoneLow, double zoneHigh, double atr)\n        {\n'''
assert s.count(needle)==1
s=s.replace(needle,insert+needle,1)
p.write_text(s)
PY

grep -q 'v4.0.0-xabcd-alpha-candidate' "$SRC"
grep -q 'Enable True XABCD Alpha' "$SRC"
grep -q 'TryArmTrueXabcd' "$SRC"
grep -q 'RestoreDailyStateFromHistory' "$SRC"
grep -q 'EnsureProtectionIntegrity' "$SRC"
grep -q 'CurrentBotFloatingNet' "$SRC"

docker pull "$IMAGE"
docker run --rm --entrypoint sh -v "$PWD:/repo" -w /repo "$IMAGE" -c \
  "dotnet restore '$ROOT/FibonacciXAUUSD3.csproj' && dotnet build '$ROOT/FibonacciXAUUSD3.csproj' -c Release --no-restore -p:AlgoPublish=False -p:IncludeSource=True"

ALGO="$(find "$ROOT" -type f -name '*.algo' ! -path '*/builds/*' ! -path '*/validation-*/*' -print -quit)"
test -n "$ALGO"; test -s "$ALGO"
cp "$ALGO" "$WORK/FibonacciXAUUSD4-v4.0-XABCDAlpha.algo"
cp "$SRC" "$WORK/FibonacciXAUUSD4-v4.0.cs"
sha256sum "$WORK/FibonacciXAUUSD4-v4.0-XABCDAlpha.algo" > "$WORK/algo.sha256"

run_bt() {
  local variant="$1" enabled="$2" geom="$3" prescore="$4" target="$5" period="$6" cost="$7" start="$8" end="$9" spread="${10}" commission="${11}"
  local label="${variant}-${period}-${cost}"
  echo "=== BACKTEST $label XABCD=$enabled geom=$geom pre=$prescore target=$target ==="
  docker run --rm -v "$PWD/$WORK:/work" \
    -e "CTID=$CTRADER_CTID" -e 'PWD-FILE=/work/ctrader.pwd' -e "ACCOUNT=$CTRADER_ACCOUNT" \
    "$IMAGE" backtest /work/FibonacciXAUUSD4-v4.0-XABCDAlpha.algo \
    --environment-variables --exit-on-stop --symbol=XAUUSD --period=m5 \
    --start="$start" --end="$end" --balance=10000 --data-mode=m1 --data-dir=/work/cache \
    --commission="$commission" --spread="$spread" \
    --RiskPercent=0.50 --MaxDailyLossPercent=3 --MinimumRiskReward=1.5 \
    --PreScoreMin=42 --FinalScoreMin=60 --M5PreScoreFloor=50 --M5RulesNeeded=2 \
    --MinImpulseAtr=1.2 --MinStopAtr=0.20 --MaxAllowedRR=8 \
    --BuyH1MinScore=18 --BlockLondonEntries=true --RequireH1AtrExpansion=true --H1AtrExpansionMin=1.15 \
    --EnableTrueXabcdAlpha="$enabled" --XabcdGeometryMin="$geom" --XabcdPreScoreMin="$prescore" --XabcdTargetAdFib="$target" --XabcdMaxAgeM15=4 \
    --report="/work/reports/${label}.html" --report-json="/work/reports/${label}.json" \
    2>&1 | tee "$REPORTS/${label}.log"
  test -s "$REPORTS/${label}.json"
}

# Baseline plus three independently testable true-XABCD sleeves. Core strategy and risk stay fixed.
for spec in \
  'base false 0.70 64 0.50' \
  'x70t50 true 0.70 64 0.50' \
  'x75t50 true 0.75 66 0.50' \
  'x70t618 true 0.70 64 0.618'; do
  set -- $spec
  v="$1"; enabled="$2"; geom="$3"; pre="$4"; target="$5"
  run_bt "$v" "$enabled" "$geom" "$pre" "$target" 3m standard 09/06/2026 09/09/2026 17.42 35
  run_bt "$v" "$enabled" "$geom" "$pre" "$target" 3m harsh    09/06/2026 09/09/2026 30 50
  run_bt "$v" "$enabled" "$geom" "$pre" "$target" 6m standard 09/03/2026 09/09/2026 17.42 35
  run_bt "$v" "$enabled" "$geom" "$pre" "$target" 6m harsh    09/03/2026 09/09/2026 30 50
  run_bt "$v" "$enabled" "$geom" "$pre" "$target" 1y standard 09/09/2025 09/09/2026 17.42 35
  run_bt "$v" "$enabled" "$geom" "$pre" "$target" 1y harsh    09/09/2025 09/09/2026 30 50
done

python3 - <<'PY'
import datetime, json, math
from pathlib import Path
base=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_3/validation-v40-xabcd')
reports=base/'reports'
variants=['base','x70t50','x75t50','x70t618']
rows=[]
safety_fail=False
for v in variants:
  for period in ['3m','6m','1y']:
    for cost in ['standard','harsh']:
      d=json.loads((reports/f'{v}-{period}-{cost}.json').read_text())
      ts=d['tradeStatistics']; main=d['main']; eq=d['equity']; hist=d.get('history',{}).get('items',[])
      spans=sorted((int(x['entryTime']),int(x['closeTime']),x['direction']) for x in hist)
      overlap=hedge=0
      for i,a in enumerate(spans):
        for b in spans[i+1:]:
          if b[0]>=a[1]: break
          overlap+=1; hedge+=int(b[2]!=a[2])
      london=sum(1 for x in hist if 7<=datetime.datetime.fromtimestamp(int(x['entryTime'])/1000,datetime.timezone.utc).hour<13)
      trades=int(ts['totalTrades']['all']); net=float(main['netProfit']); roi=float(main['roi']); pf=float(ts['profitFactor']['all']); dd=float(eq['maxEquityDrawdownPercent'])
      safety_fail |= bool(overlap or hedge or london)
      gm=((1+roi/100.0)**(1/12.0)-1)*100.0 if period=='1y' and roi>-100 else 0.0
      xtrades=sum(1 for x in hist if str(x.get('comment','')).startswith('XABCD-'))
      rows.append(dict(v=v,period=period,cost=cost,trades=trades,xtrades=xtrades,net=net,roi=roi,pf=pf,dd=dd,gm=gm,overlap=overlap,hedge=hedge,london=london))

def pick(v,p,c): return next(r for r in rows if r['v']==v and r['period']==p and r['cost']==c)
baseh=pick('base','1y','harsh'); bases=pick('base','1y','standard')
ranking=[]
for v in variants:
  r3h=pick(v,'3m','harsh'); r6h=pick(v,'6m','harsh'); r1h=pick(v,'1y','harsh'); r1s=pick(v,'1y','standard')
  score=r1h['roi']+0.45*r6h['roi']+0.20*r3h['roi']+2.0*(r1h['pf']-1)-max(0,r1h['dd']-6)
  ranking.append((score,v,r1h,r1s))
ranking.sort(reverse=True,key=lambda x:x[0])
best=ranking[0]
winner='base'
if best[1]!='base':
  r1h,r1s=best[2],best[3]
  robust=(r1h['roi']>baseh['roi'] and r1s['roi']>bases['roi'] and r1h['pf']>=baseh['pf']-0.05 and r1h['dd']<=baseh['dd']+1.0 and pick(best[1],'6m','harsh')['roi']>0 and pick(best[1],'3m','harsh')['roi']>0 and r1h['xtrades']>=3)
  if robust: winner=best[1]
(base/'winner.txt').write_text(winner+'\n')
config={
 'base':('false','0.70','64','0.50'),
 'x70t50':('true','0.70','64','0.50'),
 'x75t50':('true','0.75','66','0.50'),
 'x70t618':('true','0.70','64','0.618')}
(base/'winner_config.txt').write_text(' '.join(config[winner])+'\n')
out=['# xauusd_4 True XABCD Alpha Validation','', '| Variant | Period | Cost | Trades | XABCD trades | Net | ROI % | PF | DD % | Geo monthly % |','|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
  out.append(f"| {r['v']} | {r['period']} | {r['cost']} | {r['trades']} | {r['xtrades']} | {r['net']:.2f} | {r['roi']:.2f} | {r['pf']:.2f} | {r['dd']:.2f} | {r['gm']:.2f} |")
out += ['', '## Ranking','']
for score,v,r1h,r1s in ranking:
  out.append(f"- {v}: score={score:.2f}; 1Y Std ROI={r1s['roi']:.2f}% PF={r1s['pf']:.2f} DD={r1s['dd']:.2f}% monthly={r1s['gm']:.2f}%; 1Y Harsh ROI={r1h['roi']:.2f}% PF={r1h['pf']:.2f} DD={r1h['dd']:.2f}% monthly={r1h['gm']:.2f}%")
out += ['',f'**Winner for chronological split: {winner}**',f'**Safety precheck: {"FAIL" if safety_fail else "PASS"}**','Store display benchmark: 7% geometric monthly is recorded as an aspirational commercial metric only; it is never a reason to increase risk or promote a weaker strategy.']
(base/'V40_XABCD_VALIDATION_SUMMARY.md').write_text('\n'.join(out)+'\n')
print('\n'.join(out))
PY

WINNER="$(cat "$WORK/winner.txt")"
read ENABLED GEOM PRE TARGET < "$WORK/winner_config.txt"
run_bt "$WINNER" "$ENABLED" "$GEOM" "$PRE" "$TARGET" oos1 standard 09/09/2025 09/03/2026 17.42 35
run_bt "$WINNER" "$ENABLED" "$GEOM" "$PRE" "$TARGET" oos1 harsh    09/09/2025 09/03/2026 30 50
run_bt "$WINNER" "$ENABLED" "$GEOM" "$PRE" "$TARGET" oos2 standard 09/03/2026 09/09/2026 17.42 35
run_bt "$WINNER" "$ENABLED" "$GEOM" "$PRE" "$TARGET" oos2 harsh    09/03/2026 09/09/2026 30 50

python3 - <<'PY'
import json
from pathlib import Path
base=Path('FibonacciHarmonicSniperUltimate/versions/xauusd_3/validation-v40-xabcd'); reports=base/'reports'; winner=(base/'winner.txt').read_text().strip()
lines=['','## Chronological split validation','', '| Segment | Cost | Trades | Net | ROI % | PF | DD % |','|---|---|---:|---:|---:|---:|---:|']
pass_all=True
for seg in ['oos1','oos2']:
  for cost in ['standard','harsh']:
    d=json.loads((reports/f'{winner}-{seg}-{cost}.json').read_text()); ts=d['tradeStatistics']; main=d['main']; eq=d['equity']
    trades=int(ts['totalTrades']['all']); net=float(main['netProfit']); roi=float(main['roi']); pf=float(ts['profitFactor']['all']); dd=float(eq['maxEquityDrawdownPercent'])
    lines.append(f'| {seg} | {cost} | {trades} | {net:.2f} | {roi:.2f} | {pf:.2f} | {dd:.2f} |')
    if trades<5 or net<=0 or pf<=1.0: pass_all=False
lines += ['',f'**Final robustness verdict: {"PASS" if pass_all else "NOT YET PASS"}**']
p=base/'V40_XABCD_VALIDATION_SUMMARY.md'; p.write_text(p.read_text()+'\n'.join(lines)+'\n'); print('\n'.join(lines))
PY
