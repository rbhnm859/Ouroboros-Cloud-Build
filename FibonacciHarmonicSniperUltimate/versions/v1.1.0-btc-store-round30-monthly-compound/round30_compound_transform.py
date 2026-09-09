from pathlib import Path
import hashlib, shutil, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: round30_compound_transform.py <store-src-dir> <round30-dir>')
srcdir=Path(sys.argv[1]); outdir=Path(sys.argv[2]); outdir.mkdir(parents=True,exist_ok=True)
required=['BTC-Harmonic-Guard.cs','Round26.Execution.cs','Round26.Quality.cs','Round26.Regime.cs','Round26.Risk.cs','Round26.Signal.cs','Store.Safety.cs']
for n in required:
    p=srcdir/n
    if not p.exists(): raise SystemExit(f'missing {n}')
    shutil.copy2(p,outdir/n)

main=outdir/'BTC-Harmonic-Guard.cs'; s=main.read_text()
def rep(a,b,label,count=1):
    global s
    if a not in s: raise SystemExit(f'anchor missing: {label}')
    s=s.replace(a,b,count)

anchor='''        [Parameter("R22 M30 Sell Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 1.0, Group = "BTC Round22 Capital Efficiency")]
        public double Round22M30SellRiskPercent { get; set; }
'''
rep(anchor,anchor+'''
        [Parameter("R30 Compound Enabled", DefaultValue = false, Group = "BTC Store Compound")]
        public bool Round30CompoundEnabled { get; set; }

        [Parameter("R30 Low Quality Scale", DefaultValue = 0.75, MinValue = 0.50, MaxValue = 1.00, Group = "BTC Store Compound")]
        public double Round30LowQualityScale { get; set; }

        [Parameter("R30 High Quality Scale", DefaultValue = 1.10, MinValue = 1.00, MaxValue = 1.20, Group = "BTC Store Compound")]
        public double Round30HighQualityScale { get; set; }

        [Parameter("R30 Low Quality Threshold", DefaultValue = 0.45, MinValue = 0.30, MaxValue = 0.60, Group = "BTC Store Compound")]
        public double Round30LowQualityThreshold { get; set; }

        [Parameter("R30 High Quality Threshold", DefaultValue = 0.75, MinValue = 0.60, MaxValue = 0.90, Group = "BTC Store Compound")]
        public double Round30HighQualityThreshold { get; set; }
''','compound params')

rep('Print("VERSION BTC-Harmonic-Guard-Store-v1.0");','Print("VERSION BTC-Harmonic-Guard-Store-v1.1-Compound");','version')
startup='''            Print("BTC Round26 Core Refactor | Signal/Quality/Regime/Risk/Execution layers enabled | economic logic frozen to Round22");
'''
rep(startup,startup+'''            Round30InitializeCompound();
            Print("BTC Store Compound | enabled={0} lowScale={1:F2} highScale={2:F2} lowQ={3:F2} highQ={4:F2}", Round30CompoundEnabled, Round30LowQualityScale, Round30HighQualityScale, Round30LowQualityThreshold, Round30HighQualityThreshold);
''','startup')

rep('double volume=Round26RiskM30Volume(slPips, riskPercent);','double volume=Round30RiskM30Volume(slPips, riskPercent, m.Direction, round21Bypass);','m30 risk')
rep('''            double storeH1Risk = m.Direction == TradeType.Buy ? Round22H1BuyRiskPercent : Round22H1SellRiskPercent;
            if (!StoreValidateOrder(m.Direction, volume, slPips, tpPips, storeH1Risk, "H1"))
''','''            double storeH1Risk = Round30EffectiveH1RiskPercent(m.Direction);
            if (!StoreValidateOrder(m.Direction, volume, slPips, tpPips, storeH1Risk, "H1"))
''','h1 preflight risk')
rep('''            if (!StoreValidateOrder(m.Direction, volume, slPips, tpPips, riskPercent, round21Bypass ? "M30_BYPASS" : "M30"))
''','''            double storeM30Risk = Round30EffectiveM30RiskPercent(m.Direction, riskPercent, round21Bypass);
            if (!StoreValidateOrder(m.Direction, volume, slPips, tpPips, storeM30Risk, round21Bypass ? "M30_BYPASS" : "M30"))
''','m30 preflight risk')
main.write_text(s)

risk=outdir/'Round26.Risk.cs'; rs=risk.read_text()
old='''        private double Round26RiskH1Volume(double slPips, TradeType direction)
        {
            return Round22CalculateH1Volume(slPips, direction);
        }
'''
new='''        private double Round26RiskH1Volume(double slPips, TradeType direction)
        {
            return Round30RiskH1Volume(slPips, direction);
        }
'''
if old not in rs: raise SystemExit('h1 risk hook missing')
risk.write_text(rs.replace(old,new,1))

(outdir/'Round30.CompoundRisk.cs').write_text(r'''using System;
using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        private ExponentialMovingAverage _r30H4Ema;
        private ExponentialMovingAverage _r30H1Ema;

        private void Round30InitializeCompound()
        {
            _r30H4Ema = Indicators.ExponentialMovingAverage(_barsH4.ClosePrices, EmaPeriod);
            _r30H1Ema = Indicators.ExponentialMovingAverage(_barsH1.ClosePrices, EmaPeriod);
        }

        private double Round30FrameQuality(Bars bars, ExponentialMovingAverage ema, TradeType direction)
        {
            if (bars == null || ema == null || bars.Count < 12) return 0.50;
            int i = bars.Count - 2; // last fully closed bar only
            if (i < 10) return 0.50;
            bool buy = direction == TradeType.Buy;
            double close=bars.ClosePrices[i], prevClose=bars.ClosePrices[i-1];
            double e=ema.Result[i], prevE=ema.Result[i-1];
            double q=0.0;
            if (buy ? close>e : close<e) q += 0.30;
            if (buy ? e>prevE : e<prevE) q += 0.25;
            if (buy ? close>prevClose : close<prevClose) q += 0.15;
            bool structure = buy
                ? (bars.LowPrices[i] > bars.LowPrices[i-1] || bars.HighPrices[i] > bars.HighPrices[i-1])
                : (bars.HighPrices[i] < bars.HighPrices[i-1] || bars.LowPrices[i] < bars.LowPrices[i-1]);
            if (structure) q += 0.15;
            double range=0; int n=0;
            for (int k=i-9;k<=i;k++)
            {
                if (k<0) continue;
                double r=bars.HighPrices[k]-bars.LowPrices[k];
                if (r>0 && !double.IsNaN(r) && !double.IsInfinity(r)) { range+=r; n++; }
            }
            if (n>0)
            {
                double avg=range/n;
                if (avg>0) q += 0.15*Math.Min(1.0, Math.Abs(close-e)/(avg*0.75));
            }
            return Math.Max(0.0,Math.Min(1.0,q));
        }

        private double Round30Quality(TradeType direction)
        {
            double h4=Round30FrameQuality(_barsH4,_r30H4Ema,direction);
            double h1=Round30FrameQuality(_barsH1,_r30H1Ema,direction);
            return 0.60*h4 + 0.40*h1;
        }

        private double Round30Scale(TradeType direction)
        {
            if (!Round30CompoundEnabled) return 1.0;
            double q=Round30Quality(direction);
            if (q < Round30LowQualityThreshold) return Round30LowQualityScale;
            if (q >= Round30HighQualityThreshold) return Round30HighQualityScale;
            return 1.0;
        }

        private double Round30RiskVolume(double slPips, double riskPercent)
        {
            if (slPips<=0 || riskPercent<=0) return 0;
            double budget=Account.Equity*riskPercent/100.0;
            double raw=Symbol.VolumeForFixedRisk(budget,slPips,RoundingMode.Down);
            if (double.IsNaN(raw)||double.IsInfinity(raw)||raw<=0) return 0;
            raw=Symbol.NormalizeVolumeInUnits(raw,RoundingMode.Down);
            if (raw>Symbol.VolumeInUnitsMax) raw=Symbol.VolumeInUnitsMax;
            double estimated=Symbol.AmountRisked(raw,slPips);
            if (double.IsNaN(estimated)||double.IsInfinity(estimated)||estimated<=0||estimated>budget+Math.Max(0.01,budget*0.0025)) return 0;
            return raw;
        }

        private double Round30EffectiveH1RiskPercent(TradeType direction)
        {
            double baseRisk=direction==TradeType.Buy?Round22H1BuyRiskPercent:Round22H1SellRiskPercent;
            return baseRisk*Round30Scale(direction);
        }

        private double Round30RiskH1Volume(double slPips, TradeType direction)
        {
            if (!Round30CompoundEnabled) return Round22CalculateH1Volume(slPips,direction);
            return Round30RiskVolume(slPips,Round30EffectiveH1RiskPercent(direction));
        }

        private double Round30EffectiveM30RiskPercent(TradeType direction, double baseRisk, bool bypass)
        {
            if (bypass || !Round30CompoundEnabled) return baseRisk;
            return baseRisk*Round30Scale(direction);
        }

        private double Round30RiskM30Volume(double slPips, double baseRisk, TradeType direction, bool bypass)
        {
            if (bypass || !Round30CompoundEnabled) return Round21CalculateM30Volume(slPips,baseRisk);
            return Round30RiskVolume(slPips,Round30EffectiveM30RiskPercent(direction,baseRisk,false));
        }
    }
}
''')
print('Round30 main SHA',hashlib.sha256(main.read_bytes()).hexdigest())
print('Round30 risk SHA',hashlib.sha256(risk.read_bytes()).hexdigest())
print('Round30 overlay SHA',hashlib.sha256((outdir/'Round30.CompoundRisk.cs').read_bytes()).hexdigest())
