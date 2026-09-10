from pathlib import Path
import subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: commercial_rc1_transform.py <store-main.cs> <rc1-main.cs>')

# Build validated Growth3 v3.1 first, then refactor only shared commercial boundaries.
subprocess.run([
    sys.executable,
    'FibonacciHarmonicSniperUltimate/monthly-growth-v3/growth3_transform.py',
    sys.argv[1], sys.argv[2]
], check=True)

out = Path(sys.argv[2])
main = out.read_text()
base = out.parent

for name in ['Round26.Execution.cs','Round26.Risk.cs','Round26.Regime.cs','Growth3.Architecture.cs','Store.Safety.cs']:
    if not (base / name).exists():
        raise SystemExit('Commercial RC1 required generated layer missing: ' + name)

def rep(text, old, new, label):
    if old not in text:
        raise SystemExit('Commercial RC1 anchor missing: ' + label)
    return text.replace(old, new, 1)

main = rep(main, 'BTC-Harmonic-Guard-Growth3-v3.1', 'BTC-Harmonic-Guard-Commercial-RC1', 'version')

# Route H1 market order through centralized execution.
old_h1 = '''            var result = ExecuteMarketOrder(m.Direction, SymbolName, volume, BotLabel, slPips, tpPips, m.Definition.Name, false);\n            if (!result.IsSuccessful)\n            {\n                Print("[ORDER FAIL] {0} {1} error={2}", m.Definition.Name, m.Direction, result.Error);\n                return;\n            }\n\n            if (result.Position == null || !result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)\n            {\n                Print("[PROTECTION FAIL] Position opened without complete SL/TP; closing immediately.");\n                if (result.Position != null)\n                    StoreEmergencyClose(result.Position, "H1_PROTECTION_FAIL");\n                return;\n            }\n'''
new_h1 = '''            var result = CommercialExecuteMarketIntent("H1", m.Direction, volume, slPips, tpPips, m.Definition.Name);\n            if (result == null || !result.IsSuccessful || result.Position == null)\n                return;\n'''
main = rep(main, old_h1, new_h1, 'H1 centralized execution')

# Route M30 market order through centralized execution.
old_m30 = '''            var result=ExecuteMarketOrder(m.Direction,SymbolName,volume,BotLabel,slPips,tpPips,patternName,false);\n            if (!result.IsSuccessful || result.Position==null)\n            {\n                Print("[R15 M30 ORDER FAIL] {0} {1} error={2}",m.Definition.Name,m.Direction,result.Error);\n                return;\n            }\n            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)\n            {\n                Print("[R15 M30 PROTECTION FAIL] closing unprotected position");\n                StoreEmergencyClose(result.Position, "M30_PROTECTION_FAIL");\n                return;\n            }\n'''
new_m30 = '''            var result=CommercialExecuteMarketIntent("M30",m.Direction,volume,slPips,tpPips,patternName);\n            if (result==null || !result.IsSuccessful || result.Position==null)\n                return;\n'''
main = rep(main, old_m30, new_m30, 'M30 centralized execution')
out.write_text(main)

(base / 'Round26.Risk.cs').write_text(r'''using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        private double Round26RiskH1Volume(double slPips, TradeType direction)
        {
            double requested = direction == TradeType.Buy ? Round22H1BuyRiskPercent : Round22H1SellRiskPercent;
            return CommercialVolumeForRisk("H1", direction, slPips, requested);
        }

        private double Round26RiskM30Volume(double slPips, double riskPercent)
        {
            return CommercialVolumeForRisk("M30", TradeType.Buy, slPips, riskPercent);
        }
    }
}
''')

(base / 'Round26.Execution.cs').write_text(r'''namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        private void Round26ExecutionH1(PatternMatch match)
        {
            if (match == null) return;
            if (!CommercialPortfolioAllows("H1", match.Direction, match.FinalScore)) return;
            ExecutePatternTrade(match);
        }

        private void Round26ExecutionM30(PatternMatch match, int lastClosed, bool round21Bypass)
        {
            if (match == null) return;
            if (!CommercialPortfolioAllows("M30", match.Direction, match.FinalScore)) return;
            Round15ExecuteM30(match, lastClosed, round21Bypass);
        }
    }
}
''')

(base / 'Round26.Regime.cs').write_text(r'''using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        private sealed class Round26RegimeSnapshot
        {
            public TradeType Direction;
            public bool H1TrendAligned;
            public bool M30HealthAllowed;
            public int OwnOpenPositions;
            public double SpreadPips;
        }

        private Round26RegimeSnapshot Round26CaptureRegime(TradeType direction)
        {
            var c = CommercialCaptureRegime(direction);
            return new Round26RegimeSnapshot
            {
                Direction = direction,
                H1TrendAligned = c != null && c.H1Aligned,
                M30HealthAllowed = CommercialDirectionalHealthAllows("M30", direction),
                OwnOpenPositions = Round18OwnOpenPositions(),
                SpreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize
            };
        }
    }
}
''')

arch_path = base / 'Growth3.Architecture.cs'
a = arch_path.read_text()
a = rep(a,
    'if (!(intent.StopPips>0) || !(intent.TargetPips>0) || intent.Confidence<0.45) return false;',
    'if (!(intent.StopPips>0) || !(intent.TargetPips>0) || intent.Confidence<0.62) return false;\n            if (!CommercialPortfolioAllows("GROWTH3", intent.Direction, intent.Confidence * 100.0)) return false;',
    'Growth3 commercial portfolio gate')
old_growth = '''            // Unified portfolio gate: Growth3 may consume at most the frozen low research budget.\n            // Risk cannot be increased by alpha confidence or by candidate tuning.\n            double effectiveRiskPercent=Math.Min(Growth2RiskPercent,0.15);\n            double budget=Account.Equity*effectiveRiskPercent/100.0;\n            if (!(budget>0) || double.IsNaN(budget) || double.IsInfinity(budget)) return false;\n\n            double volume=Symbol.VolumeForFixedRisk(budget,intent.StopPips,RoundingMode.Down);\n            if (double.IsNaN(volume)||double.IsInfinity(volume)||volume<=0) return false;\n            volume=Symbol.NormalizeVolumeInUnits(volume,RoundingMode.Down);\n            if (volume>Symbol.VolumeInUnitsMax) volume=Symbol.VolumeInUnitsMax;\n            if (volume<Symbol.VolumeInUnitsMin) return false;\n            double estimated=Symbol.AmountRisked(volume,intent.StopPips);\n            if (!(estimated>0)||double.IsNaN(estimated)||double.IsInfinity(estimated)||estimated>budget+1e-8) return false;\n\n            string patternName="GROWTH2|QUALITY_RECOVERY";\n            TradeResult result=ExecuteMarketOrder(intent.Direction,SymbolName,volume,BotLabel,\n                intent.StopPips,intent.TargetPips,patternName,false);\n            if (!result.IsSuccessful || result.Position==null)\n            {\n                Print("[GROWTH3 ORDER FAIL] strategy={0} dir={1} confidence={2:F2} error={3}",\n                    intent.StrategyId,intent.Direction,intent.Confidence,result.Error);\n                return false;\n            }\n            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)\n            {\n                StoreEmergencyClose(result.Position,"GROWTH3_PROTECTION_FAIL");\n                return false;\n            }\n'''
new_growth = '''            double effectiveRiskPercent=Math.Min(Growth2RiskPercent,0.15);\n            double volume=CommercialVolumeForRisk("GROWTH3",intent.Direction,intent.StopPips,effectiveRiskPercent);\n            if (volume<Symbol.VolumeInUnitsMin) return false;\n\n            string patternName="GROWTH2|QUALITY_RECOVERY";\n            TradeResult result=CommercialExecuteMarketIntent("GROWTH3",intent.Direction,volume,\n                intent.StopPips,intent.TargetPips,patternName);\n            if (result==null || !result.IsSuccessful || result.Position==null) return false;\n'''
a = rep(a, old_growth, new_growth, 'Growth3 shared risk/execution')
arch_path.write_text(a)

(base / 'Commercial.Portfolio.cs').write_text(r'''using System;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        private enum CommercialRegimeState { Unknown, StrongTrend, NormalTrend, MixedTrend, Compression, Shock }

        private sealed class CommercialRegimeSnapshot
        {
            public CommercialRegimeState State;
            public bool H4Aligned;
            public bool H1Aligned;
            public double H4Separation;
            public double H1Separation;
            public double M30AtrPercent;
        }

        private CommercialRegimeSnapshot CommercialCaptureRegime(TradeType direction)
        {
            var r = new CommercialRegimeSnapshot { State = CommercialRegimeState.Unknown };
            if (_g2H4Ema50 == null || _g2H4Ema200 == null || _g2H1Ema20 == null || _g2H1Ema50 == null || _r15M30Atr == null)
                return r;
            int h4 = _barsH4.Count - 2, h1 = Bars.Count - 2, m30 = _barsM30.Count - 2;
            if (h4 < 202 || h1 < 52 || m30 < 20) return r;

            double h4Close=_barsH4.ClosePrices[h4], h4Fast=_g2H4Ema50.Result[h4], h4Slow=_g2H4Ema200.Result[h4], h4Prev=_g2H4Ema50.Result[h4-2];
            double h1Close=Bars.ClosePrices[h1], h1Fast=_g2H1Ema20.Result[h1], h1Slow=_g2H1Ema50.Result[h1], h1Prev=_g2H1Ema20.Result[h1-2];
            double m30Close=_barsM30.ClosePrices[m30], m30Atr=_r15M30Atr.Result[m30];
            r.H4Separation=Math.Abs(h4Fast-h4Slow)/Math.Max(Symbol.PipSize,Math.Abs(h4Close));
            r.H1Separation=Math.Abs(h1Fast-h1Slow)/Math.Max(Symbol.PipSize,Math.Abs(h1Close));
            r.M30AtrPercent=Math.Abs(m30Atr)/Math.Max(Symbol.PipSize,Math.Abs(m30Close));

            if (direction==TradeType.Buy)
            {
                r.H4Aligned=h4Close>h4Fast && h4Fast>h4Slow && h4Fast>=h4Prev;
                r.H1Aligned=h1Close>h1Fast && h1Fast>h1Slow && h1Fast>=h1Prev;
            }
            else
            {
                r.H4Aligned=h4Close<h4Fast && h4Fast<h4Slow && h4Fast<=h4Prev;
                r.H1Aligned=h1Close<h1Fast && h1Fast<h1Slow && h1Fast<=h1Prev;
            }

            if (r.M30AtrPercent>=0.022) r.State=CommercialRegimeState.Shock;
            else if (r.H4Aligned && r.H1Aligned && r.H4Separation>=0.0025 && r.H1Separation>=0.0008) r.State=CommercialRegimeState.StrongTrend;
            else if (r.H4Aligned && r.H1Aligned) r.State=CommercialRegimeState.NormalTrend;
            else if (r.H4Aligned || r.H1Aligned) r.State=CommercialRegimeState.MixedTrend;
            else if (r.H4Separation<0.0008 && r.H1Separation<0.00035) r.State=CommercialRegimeState.Compression;
            else r.State=CommercialRegimeState.MixedTrend;
            return r;
        }

        private bool CommercialPortfolioAllows(string lane, TradeType direction, double quality)
        {
            if (!StoreCanExecute() || Round18OwnOpenPositions()>=1) return false;
            var r=CommercialCaptureRegime(direction);
            if (r==null || r.State==CommercialRegimeState.Unknown || r.State==CommercialRegimeState.Shock) return false;
            if (!CommercialDirectionalHealthAllows(lane,direction))
            {
                Print("[COMMERCIAL HEALTH VETO] lane={0} dir={1}",lane,direction);
                return false;
            }
            if (lane=="GROWTH3") return r.State==CommercialRegimeState.StrongTrend;
            if (lane=="H1")
            {
                if (r.State==CommercialRegimeState.StrongTrend || r.State==CommercialRegimeState.NormalTrend) return true;
                if (r.State==CommercialRegimeState.MixedTrend) return quality>=97.0;
                if (r.State==CommercialRegimeState.Compression) return quality>=99.0;
                return false;
            }
            return lane=="M30";
        }

        private bool CommercialDirectionalHealthAllows(string lane, TradeType direction)
        {
            var recent=History.FindAll(BotLabel,SymbolName)
                .Where(h=>h.TradeType==direction && CommercialHistoryLaneMatches(h.Comment,lane))
                .OrderByDescending(h=>h.ClosingTime).Take(5).ToArray();
            if (recent.Length<3) return true;
            int losses=0;
            foreach (var h in recent) { if (h.NetProfit<0) losses++; else break; }
            if (losses<3) return true;
            return (Server.Time-recent[0].ClosingTime).TotalHours>=36.0;
        }

        private bool CommercialHistoryLaneMatches(string comment,string lane)
        {
            string c=comment??string.Empty;
            bool m30=c.StartsWith("M30|",StringComparison.OrdinalIgnoreCase)||c.StartsWith("R21M30|",StringComparison.OrdinalIgnoreCase);
            bool growth=c.StartsWith("GROWTH2|",StringComparison.OrdinalIgnoreCase)||c.StartsWith("GROWTH3|",StringComparison.OrdinalIgnoreCase);
            if (lane=="M30") return m30;
            if (lane=="GROWTH3") return growth;
            return lane=="H1" && !m30 && !growth;
        }

        private double CommercialVolumeForRisk(string lane,TradeType direction,double slPips,double requestedRiskPercent)
        {
            if (RiskMode!=RiskSizingMode.RiskPercentEquity || slPips<=0 || requestedRiskPercent<=0) return 0;
            double riskPercent=Math.Min(requestedRiskPercent,2.0);
            double budget=Account.Equity*riskPercent/100.0;
            if (!(budget>0)||double.IsNaN(budget)||double.IsInfinity(budget)) return 0;
            double raw=Symbol.VolumeForFixedRisk(budget,slPips,RoundingMode.Down);
            if (double.IsNaN(raw)||double.IsInfinity(raw)||raw<=0) return 0;
            raw=Symbol.NormalizeVolumeInUnits(raw,RoundingMode.Down);
            if (raw>Symbol.VolumeInUnitsMax) raw=Symbol.VolumeInUnitsMax;
            if (raw<Symbol.VolumeInUnitsMin) return 0;
            double estimated=Symbol.AmountRisked(raw,slPips);
            if (!(estimated>0)||double.IsNaN(estimated)||double.IsInfinity(estimated)||estimated>budget+1e-8)
            {
                Reject("commercial_risk_budget_exceeded");
                Print("[COMMERCIAL RISK REJECT] lane={0} dir={1} estimated={2:F4} budget={3:F4}",lane,direction,estimated,budget);
                return 0;
            }
            return raw;
        }

        private TradeResult CommercialExecuteMarketIntent(string lane,TradeType direction,double volume,double slPips,double tpPips,string comment)
        {
            if (!StoreCanExecute() || Round18OwnOpenPositions()>=1) return null;
            if (volume<Symbol.VolumeInUnitsMin || slPips<=0 || tpPips<=0 || tpPips+1e-9<slPips*MinimumRiskReward) return null;
            TradeResult result=ExecuteMarketOrder(direction,SymbolName,volume,BotLabel,slPips,tpPips,comment,false);
            if (!result.IsSuccessful || result.Position==null)
            {
                Print("[COMMERCIAL ORDER FAIL] lane={0} dir={1} error={2}",lane,direction,result.Error);
                return result;
            }
            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                Print("[COMMERCIAL PROTECTION FAIL] lane={0} pos={1}",lane,result.Position.Id);
                StoreEmergencyClose(result.Position,lane+"_PROTECTION_FAIL");
                return null;
            }
            return result;
        }
    }
}
''')

# Structural invariant: exactly one direct market order call is allowed in the generated project.
counts=[]
for p in base.glob('*.cs'):
    counts.append((p.name,p.read_text().count('ExecuteMarketOrder(')))
count=sum(v for _,v in counts)
if count!=1:
    raise SystemExit('Commercial RC1 invariant failed: expected one centralized ExecuteMarketOrder call, found %d %r' % (count,counts))
print('Commercial RC1 generated; centralized ExecuteMarketOrder count=',count)
