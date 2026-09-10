from pathlib import Path
import re, subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: commercial_rc4_transform.py <store-main.cs> <rc4-main.cs>')

# RC4 starts from the proven RC3A architecture-parity generator.  It changes only
# the weak/satellite layers: H1 Buy alpha remains untouched, Growth3 becomes
# shadow-only, M30 finally honors its own M30Patterns selector, and all live orders
# remain behind one centralized execution/risk boundary.
subprocess.run([sys.executable, '.github/scripts/commercial_rc3a_transform.py', sys.argv[1], sys.argv[2]], check=True)

out = Path(sys.argv[2]).resolve()
base = out.parent
main = out.read_text().replace('BTC-Harmonic-Guard-Commercial-RC3A', 'BTC-Harmonic-Guard-Commercial-RC4')

# FIX: the M30 engine advertised M30Patterns=Reciprocal ABCD,ABCD but its actual
# execution loop hard-coded Reciprocal ABCD and iterated the H1/global _patterns
# list.  Use the complete library plus the M30-specific selector.  Preserve the
# proven Reciprocal ABCD choice whenever it exists; ABCD is an expansion signal
# only when no Reciprocal candidate is available for that decision epoch.
old = '''                foreach (var def in _patterns)\n                {\n                    if (!def.Name.Equals("Reciprocal ABCD", StringComparison.OrdinalIgnoreCase)) continue;'''
new = '''                foreach (var def in _allPatterns)\n                {\n                    if (!IsPatternSelected(def, M30Patterns)) continue;'''
if old not in main:
    raise SystemExit('RC4 M30 pattern-universe anchor missing')
main = main.replace(old, new, 1)

old = '''            var ordered=candidates.OrderByDescending(m=>m.FinalScore).ThenByDescending(m=>m.D.Index).ToList();\n            PatternMatch best=ordered[0];'''
new = '''            var reciprocal=candidates.Where(m=>m.Definition.Name.Equals("Reciprocal ABCD", StringComparison.OrdinalIgnoreCase)).ToList();\n            var pool=reciprocal.Count>0 ? reciprocal : candidates;\n            var ordered=pool.OrderByDescending(m=>m.FinalScore).ThenByDescending(m=>m.D.Index).ToList();\n            PatternMatch best=ordered[0];'''
if old not in main:
    raise SystemExit('RC4 M30 priority anchor missing')
main = main.replace(old, new, 1)

# New M30 ABCD opportunities are satellite trades only.  They may increase trade
# count, but can never carry more than 0.15% requested risk.
old = '''            double riskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);\n            string patternName=(round21Bypass ? "R21M30|" : "M30|")+m.Definition.Name;'''
new = '''            double riskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);\n            if (m.Definition.Name.Equals("ABCD", StringComparison.OrdinalIgnoreCase))\n                riskPercent=Math.Min(riskPercent,0.15);\n            string patternName=(round21Bypass ? "R21M30|" : "M30|")+m.Definition.Name;'''
if old not in main:
    raise SystemExit('RC4 M30 satellite-risk anchor missing')
main = main.replace(old, new, 1)
out.write_text(main)

# Growth3 failed standalone attribution.  Keep its signal engine as observable
# context/shadow telemetry, but do not let it consume the single live position.
arch = base / 'Growth3.Architecture.cs'
a = arch.read_text()
start = a.find('        private bool Growth3SubmitIntent(Growth3TradeIntent intent)')
if start < 0:
    raise SystemExit('RC4 Growth3 function missing')
end_marker = '\n        }\n    }\n}'
end = a.find(end_marker, start)
if end < 0:
    raise SystemExit('RC4 Growth3 function end missing')
new_func = r'''        private bool Growth3SubmitIntent(Growth3TradeIntent intent)
        {
            if (intent==null || !TradingEnabled || !StoreCanExecute()) return false;
            if (!(intent.StopPips>0) || !(intent.TargetPips>0) || intent.Confidence<0.45) return false;
            Print("[GROWTH3 SHADOW] strategy={0} dir={1} confidence={2:F2} SL={3:F1}p TP={4:F1}p",
                intent.StrategyId,intent.Direction,intent.Confidence,intent.StopPips,intent.TargetPips);
            return false;
        }'''
a = a[:start] + new_func + a[end + len('\n        }'):]
arch.write_text(a)

# Replace RC3A central executor with restart-safe, history-derived risk governance.
# Important: risk factors can only reduce the proven base volume; no factor can
# increase risk.  We throttle weak lane/direction regimes rather than veto them,
# keeping trade-frequency information intact and allowing automatic recovery.
commercial = base / 'Commercial.IntentExecution.cs'
commercial.write_text(r'''using System;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        private sealed class CommercialTradeIntent
        {
            public readonly string Lane;
            public readonly TradeType Direction;
            public readonly double StopPips;
            public readonly double TargetPips;
            public readonly double RequestedRiskPercent;
            public readonly string Comment;
            public readonly double Quality;
            public readonly int SignalIndex;
            public readonly bool Round21Bypass;
            public CommercialTradeIntent(string lane, TradeType direction, double stopPips,
                double targetPips, double requestedRiskPercent, string comment, double quality,
                int signalIndex, bool round21Bypass)
            {
                Lane=lane; Direction=direction; StopPips=stopPips; TargetPips=targetPips;
                RequestedRiskPercent=requestedRiskPercent; Comment=comment; Quality=quality;
                SignalIndex=signalIndex; Round21Bypass=round21Bypass;
            }
        }

        private sealed class CommercialExecutionReceipt
        {
            public readonly TradeResult Result;
            public readonly double Volume;
            public readonly double RiskPercent;
            public CommercialExecutionReceipt(TradeResult result,double volume,double riskPercent)
            { Result=result; Volume=volume; RiskPercent=riskPercent; }
        }

        private CommercialExecutionReceipt CommercialSubmitIntent(CommercialTradeIntent intent)
        {
            if (intent==null || !TradingEnabled || !StoreCanExecute()) return null;
            if (Round18OwnOpenPositions()>=1) return null;
            if (!(intent.StopPips>0) || !(intent.TargetPips>0)) return null;
            if (intent.TargetPips + 1e-9 < intent.StopPips * MinimumRiskReward) return null;

            double baseVolume=CommercialBaseRiskVolume(intent);
            if (double.IsNaN(baseVolume)||double.IsInfinity(baseVolume)||baseVolume<Symbol.VolumeInUnitsMin) return null;
            double factor=CommercialRiskGovernorFactor(intent);
            double scaled=Symbol.NormalizeVolumeInUnits(baseVolume*factor,RoundingMode.Down);
            if (scaled<Symbol.VolumeInUnitsMin)
                scaled=Symbol.VolumeInUnitsMin;
            if (scaled>baseVolume)
                scaled=baseVolume;
            if (scaled>Symbol.VolumeInUnitsMax)
                scaled=Symbol.VolumeInUnitsMax;
            if (scaled<Symbol.VolumeInUnitsMin) return null;

            // Defense in depth: the governor is reduction-only.  Broker min-volume
            // rounding may never create more risk than the original proven volume.
            double baseRisk=Symbol.AmountRisked(baseVolume,intent.StopPips);
            double actualRisk=Symbol.AmountRisked(scaled,intent.StopPips);
            if (!(baseRisk>0) || !(actualRisk>0) || double.IsNaN(actualRisk) || double.IsInfinity(actualRisk) || actualRisk>baseRisk+1e-8)
                return null;

            TradeResult result=ExecuteMarketOrder(intent.Direction,SymbolName,scaled,BotLabel,
                intent.StopPips,intent.TargetPips,intent.Comment,false);
            if (!result.IsSuccessful || result.Position==null)
            {
                Print("[COMMERCIAL ORDER FAIL] lane={0} dir={1} error={2}",intent.Lane,intent.Direction,result.Error);
                return new CommercialExecutionReceipt(result,scaled,intent.RequestedRiskPercent*factor);
            }
            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                Print("[COMMERCIAL PROTECTION FAIL] lane={0} pos={1}",intent.Lane,result.Position.Id);
                StoreEmergencyClose(result.Position,intent.Lane+"_PROTECTION_FAIL");
                return null;
            }
            Print("[COMMERCIAL RISK] lane={0} dir={1} quality={2:F1} factor={3:F2} baseVol={4} liveVol={5}",
                intent.Lane,intent.Direction,intent.Quality,factor,baseVolume,scaled);
            return new CommercialExecutionReceipt(result,scaled,intent.RequestedRiskPercent*factor);
        }

        private double CommercialBaseRiskVolume(CommercialTradeIntent intent)
        {
            if (intent.Lane=="H1")
                return Round22CalculateH1Volume(intent.StopPips,intent.Direction);
            if (intent.Lane=="M30")
                return Round21CalculateM30Volume(intent.StopPips,intent.RequestedRiskPercent);
            return 0;
        }

        private double CommercialRiskGovernorFactor(CommercialTradeIntent intent)
        {
            double factor=1.0;

            // H1 Buy is the frozen core alpha: no score-based penalty.  H1 Sell and
            // M30 use only reduction-only calibration where the native score has
            // repeatedly shown weak realized expectancy.
            if (intent.Lane=="H1" && intent.Direction==TradeType.Sell && intent.Quality>=90.0 && intent.Quality<95.0)
                factor=Math.Min(factor,0.35);
            if (intent.Lane=="M30")
            {
                if ((intent.Comment??string.Empty).EndsWith("|ABCD",StringComparison.OrdinalIgnoreCase))
                    factor=Math.Min(factor,0.35);
                else if (intent.Quality>=90.0 && intent.Quality<95.0)
                    factor=Math.Min(factor,0.30);
                else if (intent.Quality>=97.5)
                    factor=Math.Min(factor,0.75);
            }

            factor=Math.Min(factor,CommercialLaneHealthFactor(intent));
            factor=Math.Min(factor,CommercialPortfolioHealthFactor());
            factor=Math.Min(factor,CommercialCostFactor(intent));
            return Math.Max(0.25,Math.Min(1.0,factor));
        }

        private double CommercialLaneHealthFactor(CommercialTradeIntent intent)
        {
            // H1 Buy remains the frozen core and is governed only by portfolio/cost safety.
            if (intent.Lane=="H1" && intent.Direction==TradeType.Buy) return 1.0;
            var recent=History.FindAll(BotLabel,SymbolName)
                .Where(h=>h.TradeType==intent.Direction && CommercialHistoryLaneMatches(h.Comment,intent.Lane))
                .OrderByDescending(h=>h.ClosingTime).Take(8).ToArray();
            if (recent.Length<6) return 1.0;
            double gp=recent.Where(h=>h.NetProfit>0).Sum(h=>h.NetProfit);
            double gl=-recent.Where(h=>h.NetProfit<0).Sum(h=>h.NetProfit);
            double pf=gl>0 ? gp/gl : 9.0;
            if (pf<0.60) return 0.35;
            if (pf<0.90) return 0.60;
            if (pf<1.10) return 0.80;
            return 1.0;
        }

        private double CommercialPortfolioHealthFactor()
        {
            var recent=History.FindAll(BotLabel,SymbolName)
                .OrderByDescending(h=>h.ClosingTime).Take(16).ToArray();
            if (recent.Length<10) return 1.0;
            double gp=recent.Where(h=>h.NetProfit>0).Sum(h=>h.NetProfit);
            double gl=-recent.Where(h=>h.NetProfit<0).Sum(h=>h.NetProfit);
            double pf=gl>0 ? gp/gl : 9.0;
            if (pf<0.65) return 0.45;
            if (pf<0.90) return 0.65;
            if (pf<1.10) return 0.80;
            return 1.0;
        }

        private double CommercialCostFactor(CommercialTradeIntent intent)
        {
            double spreadPips=(Symbol.Ask-Symbol.Bid)/Symbol.PipSize;
            if (!(spreadPips>=0) || !(intent.StopPips>0)) return 1.0;
            double ratio=spreadPips/intent.StopPips;
            if (ratio>0.10) return 0.35;
            if (ratio>0.06) return 0.55;
            if (ratio>0.03) return 0.75;
            return 1.0;
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
    }
}
''')

# Structural invariants over the actual generated compile set.  The immutable
# Store input alias may coexist in the work directory and is intentionally excluded.
src=Path(sys.argv[1]).resolve()
counts=[]
for p in base.glob('*.cs'):
    if p.resolve()==src:
        continue
    counts.append((p.name,p.read_text().count('ExecuteMarketOrder(')))
direct=sum(v for _,v in counts)
central=commercial.read_text().count('ExecuteMarketOrder(')
if direct!=1 or central!=1:
    raise SystemExit('RC4 structural invariant failed direct=%d central=%d files=%r'%(direct,central,counts))
if out.read_text().count('ExecuteMarketOrder(')!=0:
    raise SystemExit('RC4 generated main retained direct order call')
if 'IsPatternSelected(def, M30Patterns)' not in out.read_text():
    raise SystemExit('RC4 M30 selector fix missing')
if '[GROWTH3 SHADOW]' not in arch.read_text() or 'CommercialSubmitIntent' in arch.read_text():
    raise SystemExit('RC4 Growth3 shadow isolation missing')
print('Commercial RC4 generated: core H1 Buy preserved; M30 selector fixed/expanded; Growth3 shadow-only; reduction-only governor; direct orders=1')
