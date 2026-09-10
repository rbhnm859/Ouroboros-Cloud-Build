from pathlib import Path
import subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: growth3_transform.py <store-main.cs> <growth3-main.cs>')

# Preserve the proven Round26/Store generator. Growth3 changes only the rejected
# continuation lane and introduces a clean Alpha -> Intent -> Portfolio execution boundary.
subprocess.run([sys.executable, '/tmp/growth2_transform.py', sys.argv[1], sys.argv[2]], check=True)
out = Path(sys.argv[2])
alpha = out.parent / 'Growth2.Alpha.cs'
main = out.read_text()
s = alpha.read_text()

def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit('Growth3 anchor missing: ' + label)
    s = s.replace(old, new, 1)

main = main.replace('BTC-Harmonic-Guard-Growth2-v2', 'BTC-Harmonic-Guard-Growth3-v3.1')

# Regime quality: require H4/H1 directional separation and slope.
rep('''            bool h4Bull = h4Close > h4Fast && h4Fast > h4Slow && h4Fast > h4FastPrev;\n            bool h4Bear = h4Close < h4Fast && h4Fast < h4Slow && h4Fast < h4FastPrev;''',
'''            double h4Sep = Math.Abs(h4Fast - h4Slow) / Math.Max(Symbol.PipSize, Math.Abs(h4Close));\n            bool h4Bull = h4Close > h4Fast && h4Fast > h4Slow && h4Fast > h4FastPrev && h4Sep >= 0.0020;\n            bool h4Bear = h4Close < h4Fast && h4Fast < h4Slow && h4Fast < h4FastPrev && h4Sep >= 0.0020;''', 'h4 regime quality')

rep('''            bool h1Bull = h1Close > h1E20 && h1E20 > h1E50 && h1E20 > h1E20Prev && h1E50 >= h1E50Prev;\n            bool h1Bear = h1Close < h1E20 && h1E20 < h1E50 && h1E20 < h1E20Prev && h1E50 <= h1E50Prev;''',
'''            double h1Sep = Math.Abs(h1E20 - h1E50) / Math.Max(Symbol.PipSize, Math.Abs(h1Close));\n            bool h1Bull = h1Close > h1E20 && h1E20 > h1E50 && h1E20 > h1E20Prev && h1E50 >= h1E50Prev && h1Sep >= 0.0010;\n            bool h1Bear = h1Close < h1E20 && h1E20 < h1E50 && h1E20 < h1E20Prev && h1E50 <= h1E50Prev && h1Sep >= 0.0010;''', 'h1 regime quality')

rep('''            double body = Math.Abs(close - open);\n            if (body < atr * Growth2BodyAtr) return false;\n            if (Math.Abs(close - e20) > atr * Growth2MaxExtensionAtr) return false;''',
'''            double body = Math.Abs(close - open);\n            double range = Math.Max(Symbol.PipSize, _barsM30.HighPrices[m30] - _barsM30.LowPrices[m30]);\n            double closeLocation = (close - _barsM30.LowPrices[m30]) / range;\n            double m30SepAtr = Math.Abs(e20 - e50) / atr;\n            if (body < atr * Growth2BodyAtr) return false;\n            if (Math.Abs(close - e20) > atr * Growth2MaxExtensionAtr) return false;\n            if (m30SepAtr < 0.12) return false;''', 'm30 quality')

rep('''            TradeType dir;\n            if (h4Bull && h1Bull && close > open && close > e20 && e20 > e50 &&\n                close > _barsM30.HighPrices[m30-1] && pullbackLow >= e50 - atr * Growth2DeepPullbackAtr)\n                dir=TradeType.Buy;\n            else if (h4Bear && h1Bear && close < open && close < e20 && e20 < e50 &&\n                close < _barsM30.LowPrices[m30-1] && pullbackHigh <= e50 + atr * Growth2DeepPullbackAtr)\n                dir=TradeType.Sell;\n            else\n                return false;''',
'''            double recoveryHigh = Math.Max(_barsM30.HighPrices[m30-1], _barsM30.HighPrices[m30-2]);\n            double recoveryLow = Math.Min(_barsM30.LowPrices[m30-1], _barsM30.LowPrices[m30-2]);\n            TradeType dir;\n            if (h4Bull && h1Bull && close > open && close > e20 && e20 > e50 &&\n                close > recoveryHigh && closeLocation >= 0.68 &&\n                pullbackLow >= e50 - atr * Growth2DeepPullbackAtr)\n                dir=TradeType.Buy;\n            else if (h4Bear && h1Bear && close < open && close < e20 && e20 < e50 &&\n                close < recoveryLow && closeLocation <= 0.32 &&\n                pullbackHigh <= e50 + atr * Growth2DeepPullbackAtr)\n                dir=TradeType.Sell;\n            else\n                return false;''', 'momentum recovery')

# Replace alpha-owned sizing/order placement with an immutable TradeIntent.
old_exec='''            double budget=Account.Equity*Growth2RiskPercent/100.0;\n            double volume=Symbol.VolumeForFixedRisk(budget,slPips,RoundingMode.Down);\n            if (double.IsNaN(volume)||double.IsInfinity(volume)||volume<=0) return false;\n            volume=Symbol.NormalizeVolumeInUnits(volume,RoundingMode.Down);\n            if (volume>Symbol.VolumeInUnitsMax) volume=Symbol.VolumeInUnitsMax;\n            if (volume<Symbol.VolumeInUnitsMin) return false;\n            double estimated=Symbol.AmountRisked(volume,slPips);\n            if (!(estimated>0)||double.IsNaN(estimated)||double.IsInfinity(estimated)||estimated>budget+1e-8) return false;\n\n            string patternName="GROWTH2|CONTINUATION";\n            TradeResult result=ExecuteMarketOrder(dir,SymbolName,volume,BotLabel,slPips,tpPips,patternName,false);\n            if (!result.IsSuccessful || result.Position==null)\n            {\n                Print("[GROWTH2 ORDER FAIL] dir={0} error={1}",dir,result.Error);\n                return false;\n            }\n            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)\n            {\n                StoreEmergencyClose(result.Position,"GROWTH2_PROTECTION_FAIL");\n                return false;\n            }\n\n            _tradesToday++;\n            _r15LastM30TradeClosedIndex=lastClosed;\n            _positionPattern[result.Position.Id]=patternName;\n            _round8InitialRiskPips[result.Position.Id]=slPips;\n            _round8InitialTpPips[result.Position.Id]=tpPips;\n            _round8MfePips[result.Position.Id]=0.0;\n            _round8MaePips[result.Position.Id]=0.0;\n            if (!_stats.ContainsKey(patternName)) _stats[patternName]=new PatternStats();\n            _stats[patternName].Trades++;\n            StorePersistAll();\n            Print("[GROWTH2 OPEN] {0} volume={1} risk={2:F2}% SL={3:F1}p TP={4:F1}p RR={5:F2}",dir,volume,Growth2RiskPercent,slPips,tpPips,Growth2RiskReward);\n            return true;'''
new_exec='''            double confidence = Growth3ScoreIntent(h4Sep, h1Sep, m30SepAtr, closeLocation, dir);\n            var intent = new Growth3TradeIntent(\n                "GROWTH3_QUALITY_RECOVERY", dir, slPips, tpPips, confidence, lastClosed);\n            return Growth3SubmitIntent(intent);'''
rep(old_exec,new_exec,'alpha execution decoupling')

s=s.replace('[GROWTH2 OPEN]','[GROWTH3 OPEN]').replace('[GROWTH2 ORDER FAIL]','[GROWTH3 ORDER FAIL]')
alpha.write_text(s)
out.write_text(main)

# Portfolio boundary. Alpha has no access to volume sizing or ExecuteMarketOrder anymore.
architecture=out.parent/'Growth3.Architecture.cs'
architecture.write_text(r'''using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        private sealed class Growth3TradeIntent
        {
            public readonly string StrategyId;
            public readonly TradeType Direction;
            public readonly double StopPips;
            public readonly double TargetPips;
            public readonly double Confidence;
            public readonly int SignalIndex;

            public Growth3TradeIntent(string strategyId, TradeType direction, double stopPips,
                double targetPips, double confidence, int signalIndex)
            {
                StrategyId=strategyId;
                Direction=direction;
                StopPips=stopPips;
                TargetPips=targetPips;
                Confidence=confidence;
                SignalIndex=signalIndex;
            }
        }

        private double Growth3ScoreIntent(double h4Sep, double h1Sep, double m30SepAtr,
            double closeLocation, TradeType direction)
        {
            double h4Score=Math.Min(1.0,h4Sep/0.0060);
            double h1Score=Math.Min(1.0,h1Sep/0.0030);
            double m30Score=Math.Min(1.0,m30SepAtr/0.40);
            double candleScore=direction==TradeType.Buy ? closeLocation : 1.0-closeLocation;
            return Math.Max(0.0,Math.Min(1.0,0.30*h4Score+0.30*h1Score+0.25*m30Score+0.15*candleScore));
        }

        private bool Growth3SubmitIntent(Growth3TradeIntent intent)
        {
            if (intent==null || !TradingEnabled || !StoreCanExecute()) return false;
            if (Round18OwnOpenPositions()>=1) return false;
            if (!(intent.StopPips>0) || !(intent.TargetPips>0) || intent.Confidence<0.45) return false;

            // Unified portfolio gate: Growth3 may consume at most the frozen low research budget.
            // Risk cannot be increased by alpha confidence or by candidate tuning.
            double effectiveRiskPercent=Math.Min(Growth2RiskPercent,0.15);
            double budget=Account.Equity*effectiveRiskPercent/100.0;
            if (!(budget>0) || double.IsNaN(budget) || double.IsInfinity(budget)) return false;

            double volume=Symbol.VolumeForFixedRisk(budget,intent.StopPips,RoundingMode.Down);
            if (double.IsNaN(volume)||double.IsInfinity(volume)||volume<=0) return false;
            volume=Symbol.NormalizeVolumeInUnits(volume,RoundingMode.Down);
            if (volume>Symbol.VolumeInUnitsMax) volume=Symbol.VolumeInUnitsMax;
            if (volume<Symbol.VolumeInUnitsMin) return false;
            double estimated=Symbol.AmountRisked(volume,intent.StopPips);
            if (!(estimated>0)||double.IsNaN(estimated)||double.IsInfinity(estimated)||estimated>budget+1e-8) return false;

            string patternName="GROWTH2|QUALITY_RECOVERY";
            TradeResult result=ExecuteMarketOrder(intent.Direction,SymbolName,volume,BotLabel,
                intent.StopPips,intent.TargetPips,patternName,false);
            if (!result.IsSuccessful || result.Position==null)
            {
                Print("[GROWTH3 ORDER FAIL] strategy={0} dir={1} confidence={2:F2} error={3}",
                    intent.StrategyId,intent.Direction,intent.Confidence,result.Error);
                return false;
            }
            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                StoreEmergencyClose(result.Position,"GROWTH3_PROTECTION_FAIL");
                return false;
            }

            _tradesToday++;
            _r15LastM30TradeClosedIndex=intent.SignalIndex;
            _positionPattern[result.Position.Id]=patternName;
            _round8InitialRiskPips[result.Position.Id]=intent.StopPips;
            _round8InitialTpPips[result.Position.Id]=intent.TargetPips;
            _round8MfePips[result.Position.Id]=0.0;
            _round8MaePips[result.Position.Id]=0.0;
            if (!_stats.ContainsKey(patternName)) _stats[patternName]=new PatternStats();
            _stats[patternName].Trades++;
            StorePersistAll();
            Print("[GROWTH3 OPEN] strategy={0} dir={1} volume={2} risk={3:F2}% confidence={4:F2} SL={5:F1}p TP={6:F1}p",
                intent.StrategyId,intent.Direction,volume,effectiveRiskPercent,intent.Confidence,intent.StopPips,intent.TargetPips);
            return true;
        }
    }
}
''')
print('Growth3 v3.1 regime-aware TradeIntent architecture generated')
