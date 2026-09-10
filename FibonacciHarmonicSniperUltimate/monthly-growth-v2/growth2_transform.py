from pathlib import Path
import sys

if len(sys.argv)!=3:
    raise SystemExit('usage: growth2_transform.py <store-main.cs> <growth2-main.cs>')
src=Path(sys.argv[1]); out=Path(sys.argv[2]); s=src.read_text()

def rep(old,new,label):
    global s
    if old not in s:
        raise SystemExit('anchor missing: '+label)
    s=s.replace(old,new,1)

anchor='''        [Parameter("Debug Logging", DefaultValue = false, Group = "Diagnostics")]
        public bool DebugLogging { get; set; }
'''
insert=anchor+'''\n        [Parameter("Growth2 Enabled", DefaultValue = true, Group = "Growth2 Continuation")]
        public bool Growth2Enabled { get; set; }

        [Parameter("Growth2 Risk %", DefaultValue = 0.15, MinValue = 0.05, MaxValue = 0.25, Group = "Growth2 Continuation")]
        public double Growth2RiskPercent { get; set; }

        [Parameter("Growth2 RR", DefaultValue = 1.90, MinValue = 1.50, MaxValue = 2.50, Group = "Growth2 Continuation")]
        public double Growth2RiskReward { get; set; }

        [Parameter("Growth2 Stop ATR", DefaultValue = 1.40, MinValue = 1.00, MaxValue = 2.00, Group = "Growth2 Continuation")]
        public double Growth2StopAtr { get; set; }

        [Parameter("Growth2 Pullback Bars", DefaultValue = 4, MinValue = 2, MaxValue = 6, Group = "Growth2 Continuation")]
        public int Growth2PullbackBars { get; set; }

        [Parameter("Growth2 Min Body ATR", DefaultValue = 0.22, MinValue = 0.10, MaxValue = 0.40, Group = "Growth2 Continuation")]
        public double Growth2BodyAtr { get; set; }

        [Parameter("Growth2 Max Extension ATR", DefaultValue = 0.70, MinValue = 0.40, MaxValue = 1.00, Group = "Growth2 Continuation")]
        public double Growth2MaxExtensionAtr { get; set; }

        [Parameter("Growth2 Deep Pullback ATR", DefaultValue = 0.20, MinValue = 0.05, MaxValue = 0.40, Group = "Growth2 Continuation")]
        public double Growth2DeepPullbackAtr { get; set; }
'''
rep(anchor,insert,'growth2 params')

rep('''            StoreValidateStartup();
            Positions.Closed += OnPositionClosed;
''','''            StoreValidateStartup();
            Growth2Initialize();
            Positions.Closed += OnPositionClosed;
''','growth2 init')

rep('''                if (p.SymbolName != SymbolName || p.Label != BotLabel || string.IsNullOrEmpty(p.Comment) || !p.Comment.StartsWith("R21M30|", StringComparison.Ordinal))
                    continue;
''','''                if (p.SymbolName != SymbolName || p.Label != BotLabel || string.IsNullOrEmpty(p.Comment) ||
                    !(p.Comment.StartsWith("R21M30|", StringComparison.Ordinal) || p.Comment.StartsWith("GROWTH2|", StringComparison.Ordinal)))
                    continue;
''','growth2 h1 reservation')

rep('''            if (best == null)
                return;
''','''            if (best == null)
            {
                Growth2TryExecute(lastClosed);
                return;
            }
''','growth2 no m30 harmonic')

rep('Print("VERSION BTC-Harmonic-Guard-Store-v1.0");','Print("VERSION BTC-Harmonic-Guard-Growth2-v2");','growth2 version')

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(s)

safety=out.parent/'Store.Safety.cs'
if not safety.exists():
    raise SystemExit('Store.Safety.cs missing')
sx=safety.read_text()
old_health='''                    !h.Comment.StartsWith("R21M30|", StringComparison.OrdinalIgnoreCase))
'''
new_health='''                    !h.Comment.StartsWith("R21M30|", StringComparison.OrdinalIgnoreCase) &&
                    !h.Comment.StartsWith("GROWTH2|", StringComparison.OrdinalIgnoreCase))
'''
if old_health not in sx:
    raise SystemExit('anchor missing: growth2 health isolation')
safety.write_text(sx.replace(old_health,new_health,1))

layer=out.parent/'Growth2.Alpha.cs'
layer.write_text(r'''using System;
using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        private ExponentialMovingAverage _g2H4Ema50;
        private ExponentialMovingAverage _g2H4Ema200;
        private ExponentialMovingAverage _g2H1Ema20;
        private ExponentialMovingAverage _g2H1Ema50;
        private ExponentialMovingAverage _g2M30Ema20;
        private ExponentialMovingAverage _g2M30Ema50;

        private void Growth2Initialize()
        {
            _g2H4Ema50 = Indicators.ExponentialMovingAverage(_barsH4.ClosePrices, 50);
            _g2H4Ema200 = Indicators.ExponentialMovingAverage(_barsH4.ClosePrices, 200);
            _g2H1Ema20 = Indicators.ExponentialMovingAverage(Bars.ClosePrices, 20);
            _g2H1Ema50 = Indicators.ExponentialMovingAverage(Bars.ClosePrices, 50);
            _g2M30Ema20 = Indicators.ExponentialMovingAverage(_barsM30.ClosePrices, 20);
            _g2M30Ema50 = Indicators.ExponentialMovingAverage(_barsM30.ClosePrices, 50);
        }

        private bool Growth2TryExecute(int lastClosed)
        {
            if (!Growth2Enabled || !TradingEnabled || !StoreCanExecute()) return false;
            if (_g2H4Ema50 == null || _g2H4Ema200 == null || _g2H1Ema20 == null || _g2H1Ema50 == null ||
                _g2M30Ema20 == null || _g2M30Ema50 == null || _r15M30Atr == null) return false;
            if (Round18OwnOpenPositions() >= 1) return false;

            int h4 = _barsH4.Count - 2;
            int h1 = Bars.Count - 2;
            int m30 = lastClosed;
            if (h4 < 202 || h1 < 52 || m30 < Math.Max(52, Growth2PullbackBars + 2)) return false;

            double h4Close = _barsH4.ClosePrices[h4];
            double h4Fast = _g2H4Ema50.Result[h4];
            double h4Slow = _g2H4Ema200.Result[h4];
            double h4FastPrev = _g2H4Ema50.Result[h4 - 2];
            bool h4Bull = h4Close > h4Fast && h4Fast > h4Slow && h4Fast > h4FastPrev;
            bool h4Bear = h4Close < h4Fast && h4Fast < h4Slow && h4Fast < h4FastPrev;
            if (!h4Bull && !h4Bear) return false;

            double h1Close = Bars.ClosePrices[h1];
            double h1E20 = _g2H1Ema20.Result[h1];
            double h1E50 = _g2H1Ema50.Result[h1];
            double h1E20Prev = _g2H1Ema20.Result[h1 - 2];
            double h1E50Prev = _g2H1Ema50.Result[h1 - 2];
            bool h1Bull = h1Close > h1E20 && h1E20 > h1E50 && h1E20 > h1E20Prev && h1E50 >= h1E50Prev;
            bool h1Bear = h1Close < h1E20 && h1E20 < h1E50 && h1E20 < h1E20Prev && h1E50 <= h1E50Prev;

            double atr = _r15M30Atr.Result[m30];
            if (!(atr > 0) || double.IsNaN(atr) || double.IsInfinity(atr)) return false;
            double close = _barsM30.ClosePrices[m30];
            double open = _barsM30.OpenPrices[m30];
            double e20 = _g2M30Ema20.Result[m30];
            double e50 = _g2M30Ema50.Result[m30];
            double body = Math.Abs(close - open);
            if (body < atr * Growth2BodyAtr) return false;
            if (Math.Abs(close - e20) > atr * Growth2MaxExtensionAtr) return false;

            bool touched = false;
            double pullbackLow = double.PositiveInfinity;
            double pullbackHigh = double.NegativeInfinity;
            for (int k=1; k<=Growth2PullbackBars; k++)
            {
                int i=m30-k;
                double ie20=_g2M30Ema20.Result[i];
                pullbackLow=Math.Min(pullbackLow,_barsM30.LowPrices[i]);
                pullbackHigh=Math.Max(pullbackHigh,_barsM30.HighPrices[i]);
                if (h4Bull && h1Bull && _barsM30.LowPrices[i] <= ie20) touched=true;
                if (h4Bear && h1Bear && _barsM30.HighPrices[i] >= ie20) touched=true;
            }
            if (!touched) return false;

            TradeType dir;
            if (h4Bull && h1Bull && close > open && close > e20 && e20 > e50 &&
                close > _barsM30.HighPrices[m30-1] && pullbackLow >= e50 - atr * Growth2DeepPullbackAtr)
                dir=TradeType.Buy;
            else if (h4Bear && h1Bear && close < open && close < e20 && e20 < e50 &&
                close < _barsM30.LowPrices[m30-1] && pullbackHigh <= e50 + atr * Growth2DeepPullbackAtr)
                dir=TradeType.Sell;
            else
                return false;

            double slPips=Math.Max(MinStopPips,atr*Growth2StopAtr/Symbol.PipSize);
            if (MaxStopPips>0 && slPips>MaxStopPips) return false;
            double tpPips=slPips*Growth2RiskReward;
            if (tpPips < slPips*MinimumRiskReward) return false;

            double budget=Account.Equity*Growth2RiskPercent/100.0;
            double volume=Symbol.VolumeForFixedRisk(budget,slPips,RoundingMode.Down);
            if (double.IsNaN(volume)||double.IsInfinity(volume)||volume<=0) return false;
            volume=Symbol.NormalizeVolumeInUnits(volume,RoundingMode.Down);
            if (volume>Symbol.VolumeInUnitsMax) volume=Symbol.VolumeInUnitsMax;
            if (volume<Symbol.VolumeInUnitsMin) return false;
            double estimated=Symbol.AmountRisked(volume,slPips);
            if (!(estimated>0)||double.IsNaN(estimated)||double.IsInfinity(estimated)||estimated>budget+1e-8) return false;

            string patternName="GROWTH2|CONTINUATION";
            TradeResult result=ExecuteMarketOrder(dir,SymbolName,volume,BotLabel,slPips,tpPips,patternName,false);
            if (!result.IsSuccessful || result.Position==null)
            {
                Print("[GROWTH2 ORDER FAIL] dir={0} error={1}",dir,result.Error);
                return false;
            }
            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                StoreEmergencyClose(result.Position,"GROWTH2_PROTECTION_FAIL");
                return false;
            }

            _tradesToday++;
            _r15LastM30TradeClosedIndex=lastClosed;
            _positionPattern[result.Position.Id]=patternName;
            _round8InitialRiskPips[result.Position.Id]=slPips;
            _round8InitialTpPips[result.Position.Id]=tpPips;
            _round8MfePips[result.Position.Id]=0.0;
            _round8MaePips[result.Position.Id]=0.0;
            if (!_stats.ContainsKey(patternName)) _stats[patternName]=new PatternStats();
            _stats[patternName].Trades++;
            StorePersistAll();
            Print("[GROWTH2 OPEN] {0} volume={1} risk={2:F2}% SL={3:F1}p TP={4:F1}p RR={5:F2}",dir,volume,Growth2RiskPercent,slPips,tpPips,Growth2RiskReward);
            return true;
        }
    }
}
''')
print('Growth2 source generated')
