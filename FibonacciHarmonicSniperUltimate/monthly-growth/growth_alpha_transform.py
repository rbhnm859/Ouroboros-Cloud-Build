from pathlib import Path
import sys

if len(sys.argv)!=3:
    raise SystemExit('usage: growth_alpha_transform.py <store-main.cs> <growth-main.cs>')
src=Path(sys.argv[1]); out=Path(sys.argv[2]); s=src.read_text()

def rep(old,new,label):
    global s
    if old not in s: raise SystemExit('anchor missing: '+label)
    s=s.replace(old,new,1)

# Add a second, independent alpha only on H1 bars where Harmonic Alpha #1 has no candidate.
anchor='''        [Parameter("Debug Logging", DefaultValue = false, Group = "Diagnostics")]\n        public bool DebugLogging { get; set; }\n'''
insert=anchor+'''\n        [Parameter("Growth Alpha Enabled", DefaultValue = true, Group = "Growth Alpha")]\n        public bool GrowthAlphaEnabled { get; set; }\n\n        [Parameter("Growth Risk %", DefaultValue = 0.30, MinValue = 0.10, MaxValue = 0.50, Group = "Growth Alpha")]\n        public double GrowthRiskPercent { get; set; }\n\n        [Parameter("Growth RR", DefaultValue = 1.80, MinValue = 1.50, MaxValue = 2.50, Group = "Growth Alpha")]\n        public double GrowthRiskReward { get; set; }\n\n        [Parameter("Growth Stop ATR", DefaultValue = 1.50, MinValue = 1.00, MaxValue = 2.50, Group = "Growth Alpha")]\n        public double GrowthStopAtr { get; set; }\n\n        [Parameter("Growth Pullback Bars", DefaultValue = 4, MinValue = 2, MaxValue = 8, Group = "Growth Alpha")]\n        public int GrowthPullbackBars { get; set; }\n\n        [Parameter("Growth Body ATR", DefaultValue = 0.15, MinValue = 0.05, MaxValue = 0.40, Group = "Growth Alpha")]\n        public double GrowthBodyAtr { get; set; }\n'''
rep(anchor,insert,'growth params')
rep('''            StoreValidateStartup();\n            Positions.Closed += OnPositionClosed;\n''','''            StoreValidateStartup();\n            GrowthInitialize();\n            Positions.Closed += OnPositionClosed;\n''','growth init')
rep('''            if (pivots.Count < 5)\n            {\n                Round10Count("bar_insufficient_pivots");\n                return;\n            }\n''','''            if (pivots.Count < 5)\n            {\n                Round10Count("bar_insufficient_pivots");\n                GrowthTryExecute();\n                return;\n            }\n''','growth low pivots')
rep('''            if (best == null)\n            {\n                Reject("no_candidate_or_conflict");\n                return;\n            }\n''','''            if (best == null)\n            {\n                if (!GrowthTryExecute())\n                    Reject("no_candidate_or_conflict");\n                return;\n            }\n''','growth no harmonic')
rep('''            if (!name.StartsWith("M30|", StringComparison.OrdinalIgnoreCase))\n''','''            if (!name.StartsWith("M30|", StringComparison.OrdinalIgnoreCase) &&\n                !name.StartsWith("GROWTH|", StringComparison.OrdinalIgnoreCase))\n''','growth health isolation')
rep('Print("VERSION BTC-Harmonic-Guard-Store-v1.0");','Print("VERSION BTC-Harmonic-Guard-Growth-v1");','growth version')
out.write_text(s)

layer=out.parent/'Growth.Alpha.cs'
layer.write_text(r'''using System;
using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        private ExponentialMovingAverage _growthH4Ema50;
        private ExponentialMovingAverage _growthH4Ema200;
        private ExponentialMovingAverage _growthH1Ema20;
        private ExponentialMovingAverage _growthH1Ema50;
        private AverageTrueRange _growthH1Atr;
        private int _growthOpened;

        private void GrowthInitialize()
        {
            _growthH4Ema50 = Indicators.ExponentialMovingAverage(_barsH4.ClosePrices, 50);
            _growthH4Ema200 = Indicators.ExponentialMovingAverage(_barsH4.ClosePrices, 200);
            _growthH1Ema20 = Indicators.ExponentialMovingAverage(Bars.ClosePrices, 20);
            _growthH1Ema50 = Indicators.ExponentialMovingAverage(Bars.ClosePrices, 50);
            _growthH1Atr = Indicators.AverageTrueRange(Bars, 14, MovingAverageType.Exponential);
        }

        private bool GrowthTryExecute()
        {
            if (!GrowthAlphaEnabled || !TradingEnabled || !StoreCanExecute()) return false;
            if (_barsH4 == null || _growthH4Ema50 == null || _growthH4Ema200 == null || Bars.Count < 60 || _barsH4.Count < 205) return false;

            int h1 = Bars.Count - 1;
            int h4 = _barsH4.Count - 2; // last fully closed H4 bar; no current-H4 lookahead
            if (h1 < GrowthPullbackBars + 2 || h4 < 202) return false;

            double h4Close = _barsH4.ClosePrices[h4];
            double h4Fast = _growthH4Ema50.Result[h4];
            double h4Slow = _growthH4Ema200.Result[h4];
            double h4FastPrev = _growthH4Ema50.Result[h4 - 2];
            bool bull = h4Close > h4Fast && h4Fast > h4Slow && h4Fast > h4FastPrev;
            bool bear = h4Close < h4Fast && h4Fast < h4Slow && h4Fast < h4FastPrev;
            if (!bull && !bear) return false;

            double atr = _growthH1Atr.Result[h1];
            if (!(atr > 0) || double.IsNaN(atr) || double.IsInfinity(atr)) return false;
            double close = Bars.ClosePrices[h1];
            double open = Bars.OpenPrices[h1];
            double prevClose = Bars.ClosePrices[h1 - 1];
            double ema20 = _growthH1Ema20.Result[h1];
            double ema20Prev = _growthH1Ema20.Result[h1 - 1];
            double ema50 = _growthH1Ema50.Result[h1];
            double body = Math.Abs(close - open);
            if (body < atr * GrowthBodyAtr) return false;

            bool touched = false;
            for (int k=1; k<=GrowthPullbackBars; k++)
            {
                int i=h1-k;
                double e20=_growthH1Ema20.Result[i];
                if (bull && Bars.LowPrices[i] <= e20) { touched=true; break; }
                if (bear && Bars.HighPrices[i] >= e20) { touched=true; break; }
            }
            if (!touched) return false;

            TradeType dir;
            if (bull && close > open && close > ema20 && close > ema50 && prevClose <= ema20Prev && close > Bars.HighPrices[h1-1])
                dir=TradeType.Buy;
            else if (bear && close < open && close < ema20 && close < ema50 && prevClose >= ema20Prev && close < Bars.LowPrices[h1-1])
                dir=TradeType.Sell;
            else
                return false;

            double slPips = Math.Max(MinStopPips, atr * GrowthStopAtr / Symbol.PipSize);
            if (MaxStopPips > 0 && slPips > MaxStopPips) return false;
            double tpPips = slPips * GrowthRiskReward;
            if (tpPips < slPips * MinimumRiskReward) return false;

            double budget = Account.Equity * GrowthRiskPercent / 100.0;
            double volume = Symbol.VolumeForFixedRisk(budget, slPips, RoundingMode.Down);
            if (double.IsNaN(volume) || double.IsInfinity(volume) || volume <= 0) return false;
            volume = Symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);
            if (volume > Symbol.VolumeInUnitsMax) volume = Symbol.VolumeInUnitsMax;
            if (volume < Symbol.VolumeInUnitsMin) return false;
            double estimated = Symbol.AmountRisked(volume, slPips);
            if (!(estimated > 0) || estimated > budget + 1e-8) return false;

            var result=ExecuteMarketOrder(dir, SymbolName, volume, BotLabel, slPips, tpPips, "GROWTH|TREND", false);
            if (!result.IsSuccessful || result.Position == null)
            {
                Print("[GROWTH ORDER FAIL] dir={0} error={1}", dir, result.Error);
                return false;
            }
            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                StoreEmergencyClose(result.Position, "GROWTH_PROTECTION_FAIL");
                return false;
            }

            _tradesToday++;
            _lastTradeBar=Bars.Count-1;
            _growthOpened++;
            _positionPattern[result.Position.Id]="GROWTH|TREND";
            _round8InitialRiskPips[result.Position.Id]=slPips;
            _round8InitialTpPips[result.Position.Id]=tpPips;
            _round8MfePips[result.Position.Id]=0.0;
            _round8MaePips[result.Position.Id]=0.0;
            if (!_stats.ContainsKey("GROWTH|TREND")) _stats["GROWTH|TREND"]=new PatternStats();
            _stats["GROWTH|TREND"].Trades++;
            StorePersistAll();
            Print("[GROWTH OPEN] {0} volume={1} risk={2:F2}% SL={3:F1}p TP={4:F1}p RR={5:F2}", dir, volume, GrowthRiskPercent, slPips, tpPips, GrowthRiskReward);
            return true;
        }
    }
}
''')
print('growth source generated')
