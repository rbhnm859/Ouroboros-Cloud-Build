from pathlib import Path
import subprocess, sys


def rep(text, old, new, label):
    if old not in text:
        raise SystemExit('RC3A anchor missing: ' + label)
    return text.replace(old, new, 1)


def transform_generated(out_path, source_path):
    out = Path(out_path).resolve()
    source = Path(source_path).resolve()
    base = out.parent
    arch = base / 'Growth3.Architecture.cs'
    r26exec = base / 'Round26.Execution.cs'
    if not out.exists() or not arch.exists() or not r26exec.exists():
        raise SystemExit('RC3A required generated files missing')

    main = out.read_text()
    main = main.replace('BTC-Harmonic-Guard-Growth3-v3.1', 'BTC-Harmonic-Guard-Commercial-RC3A')

    old_h1 = '''            double volume = Round26RiskH1Volume(slPips, m.Direction);\n            if (volume < Symbol.VolumeInUnitsMin)\n            {\n                Reject("volume_below_min");\n                if (DebugLogging)\n                    Print("[SKIP] Calculated volume {0} is below minimum {1}.", volume, Symbol.VolumeInUnitsMin);\n                return;\n            }\n\n            var result = ExecuteMarketOrder(m.Direction, SymbolName, volume, BotLabel, slPips, tpPips, m.Definition.Name, false);\n            if (!result.IsSuccessful)\n            {\n                Print("[ORDER FAIL] {0} {1} error={2}", m.Definition.Name, m.Direction, result.Error);\n                return;\n            }\n\n            if (result.Position == null || !result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)\n            {\n                Print("[PROTECTION FAIL] Position opened without complete SL/TP; closing immediately.");\n                if (result.Position != null)\n                    StoreEmergencyClose(result.Position, "H1_PROTECTION_FAIL");\n                return;\n            }\n'''
    new_h1 = '''            double requestedRiskPercent = m.Direction == TradeType.Buy ? Round22H1BuyRiskPercent : Round22H1SellRiskPercent;\n            var intent = new CommercialTradeIntent("H1", m.Direction, slPips, tpPips, requestedRiskPercent,\n                m.Definition.Name, m.Score, -1, false);\n            var receipt = CommercialSubmitIntent(intent);\n            if (receipt == null || receipt.Result == null || !receipt.Result.IsSuccessful || receipt.Result.Position == null)\n                return;\n            double volume = receipt.Volume;\n            var result = receipt.Result;\n'''
    main = rep(main, old_h1, new_h1, 'H1 intent conversion')

    old_m30 = '''            double riskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);\n            double volume=Round26RiskM30Volume(slPips, riskPercent);\n            if (volume<Symbol.VolumeInUnitsMin) return;\n\n            string patternName=(round21Bypass ? "R21M30|" : "M30|")+m.Definition.Name;\n            var result=ExecuteMarketOrder(m.Direction,SymbolName,volume,BotLabel,slPips,tpPips,patternName,false);\n            if (!result.IsSuccessful || result.Position==null)\n            {\n                Print("[R15 M30 ORDER FAIL] {0} {1} error={2}",m.Definition.Name,m.Direction,result.Error);\n                return;\n            }\n            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)\n            {\n                Print("[R15 M30 PROTECTION FAIL] closing unprotected position");\n                StoreEmergencyClose(result.Position, "M30_PROTECTION_FAIL");\n                return;\n            }\n'''
    new_m30 = '''            double riskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);\n            string patternName=(round21Bypass ? "R21M30|" : "M30|")+m.Definition.Name;\n            var intent = new CommercialTradeIntent("M30", m.Direction, slPips, tpPips, riskPercent,\n                patternName, m.Score, lastClosed, round21Bypass);\n            var receipt = CommercialSubmitIntent(intent);\n            if (receipt == null || receipt.Result == null || !receipt.Result.IsSuccessful || receipt.Result.Position == null)\n                return;\n            double volume = receipt.Volume;\n            var result = receipt.Result;\n'''
    main = rep(main, old_m30, new_m30, 'M30 intent conversion')
    out.write_text(main)

    a = arch.read_text()
    old_g3 = '''            // Unified portfolio gate: Growth3 may consume at most the frozen low research budget.\n            // Risk cannot be increased by alpha confidence or by candidate tuning.\n            double effectiveRiskPercent=Math.Min(Growth2RiskPercent,0.15);\n            double budget=Account.Equity*effectiveRiskPercent/100.0;\n            if (!(budget>0) || double.IsNaN(budget) || double.IsInfinity(budget)) return false;\n\n            double volume=Symbol.VolumeForFixedRisk(budget,intent.StopPips,RoundingMode.Down);\n            if (double.IsNaN(volume)||double.IsInfinity(volume)||volume<=0) return false;\n            volume=Symbol.NormalizeVolumeInUnits(volume,RoundingMode.Down);\n            if (volume>Symbol.VolumeInUnitsMax) volume=Symbol.VolumeInUnitsMax;\n            if (volume<Symbol.VolumeInUnitsMin) return false;\n            double estimated=Symbol.AmountRisked(volume,intent.StopPips);\n            if (!(estimated>0)||double.IsNaN(estimated)||double.IsInfinity(estimated)||estimated>budget+1e-8) return false;\n\n            string patternName="GROWTH2|QUALITY_RECOVERY";\n            TradeResult result=ExecuteMarketOrder(intent.Direction,SymbolName,volume,BotLabel,\n                intent.StopPips,intent.TargetPips,patternName,false);\n            if (!result.IsSuccessful || result.Position==null)\n            {\n                Print("[GROWTH3 ORDER FAIL] strategy={0} dir={1} confidence={2:F2} error={3}",\n                    intent.StrategyId,intent.Direction,intent.Confidence,result.Error);\n                return false;\n            }\n            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)\n            {\n                StoreEmergencyClose(result.Position,"GROWTH3_PROTECTION_FAIL");\n                return false;\n            }\n'''
    new_g3 = '''            double effectiveRiskPercent=Math.Min(Growth2RiskPercent,0.15);\n            string patternName="GROWTH2|QUALITY_RECOVERY";\n            var commercialIntent = new CommercialTradeIntent("GROWTH3", intent.Direction, intent.StopPips,\n                intent.TargetPips, effectiveRiskPercent, patternName, intent.Confidence * 100.0, intent.SignalIndex, false);\n            var receipt = CommercialSubmitIntent(commercialIntent);\n            if (receipt == null || receipt.Result == null || !receipt.Result.IsSuccessful || receipt.Result.Position == null)\n                return false;\n            double volume = receipt.Volume;\n            TradeResult result = receipt.Result;\n'''
    a = rep(a, old_g3, new_g3, 'Growth3 intent conversion')
    arch.write_text(a)

    r26 = r26exec.read_text()
    if 'CommercialPortfolioAllows' in r26:
        raise SystemExit('RC3A must not inherit RC1/RC2 alpha vetoes')

    commercial = base / 'Commercial.IntentExecution.cs'
    commercial.write_text(r'''using System;
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
                Lane=lane;
                Direction=direction;
                StopPips=stopPips;
                TargetPips=targetPips;
                RequestedRiskPercent=requestedRiskPercent;
                Comment=comment;
                Quality=quality;
                SignalIndex=signalIndex;
                Round21Bypass=round21Bypass;
            }
        }

        private sealed class CommercialExecutionReceipt
        {
            public readonly TradeResult Result;
            public readonly double Volume;
            public readonly double RiskPercent;
            public CommercialExecutionReceipt(TradeResult result, double volume, double riskPercent)
            {
                Result=result;
                Volume=volume;
                RiskPercent=riskPercent;
            }
        }

        private CommercialExecutionReceipt CommercialSubmitIntent(CommercialTradeIntent intent)
        {
            if (intent==null || !TradingEnabled || !StoreCanExecute()) return null;
            if (Round18OwnOpenPositions()>=1) return null;
            if (!(intent.StopPips>0) || !(intent.TargetPips>0)) return null;
            if (intent.TargetPips + 1e-9 < intent.StopPips * MinimumRiskReward) return null;

            double volume=CommercialRiskVolume(intent);
            if (double.IsNaN(volume)||double.IsInfinity(volume)||volume<Symbol.VolumeInUnitsMin) return null;

            TradeResult result=ExecuteMarketOrder(intent.Direction,SymbolName,volume,BotLabel,
                intent.StopPips,intent.TargetPips,intent.Comment,false);
            if (!result.IsSuccessful || result.Position==null)
            {
                Print("[COMMERCIAL ORDER FAIL] lane={0} dir={1} error={2}",intent.Lane,intent.Direction,result.Error);
                return new CommercialExecutionReceipt(result,volume,intent.RequestedRiskPercent);
            }
            if (!result.Position.StopLoss.HasValue || !result.Position.TakeProfit.HasValue)
            {
                Print("[COMMERCIAL PROTECTION FAIL] lane={0} pos={1}",intent.Lane,result.Position.Id);
                StoreEmergencyClose(result.Position,intent.Lane+"_PROTECTION_FAIL");
                return null;
            }
            return new CommercialExecutionReceipt(result,volume,intent.RequestedRiskPercent);
        }

        private double CommercialRiskVolume(CommercialTradeIntent intent)
        {
            if (intent.Lane=="H1")
                return Round22CalculateH1Volume(intent.StopPips,intent.Direction);
            if (intent.Lane=="M30")
                return Round21CalculateM30Volume(intent.StopPips,intent.RequestedRiskPercent);
            if (intent.Lane=="GROWTH3")
            {
                double budget=Account.Equity*intent.RequestedRiskPercent/100.0;
                if (!(budget>0)||double.IsNaN(budget)||double.IsInfinity(budget)) return 0;
                double raw=Symbol.VolumeForFixedRisk(budget,intent.StopPips,RoundingMode.Down);
                if (double.IsNaN(raw)||double.IsInfinity(raw)||raw<=0) return 0;
                raw=Symbol.NormalizeVolumeInUnits(raw,RoundingMode.Down);
                if (raw>Symbol.VolumeInUnitsMax) raw=Symbol.VolumeInUnitsMax;
                if (raw<Symbol.VolumeInUnitsMin) return 0;
                double estimated=Symbol.AmountRisked(raw,intent.StopPips);
                if (!(estimated>0)||double.IsNaN(estimated)||double.IsInfinity(estimated)||estimated>budget+1e-8) return 0;
                return raw;
            }
            return 0;
        }
    }
}
''')

    # The validation harness keeps the immutable Store source beside the generated
    # project as an input alias. It is not part of the compile set and must not be
    # counted as a generated direct-order call. This is the same exclusion used by
    # the validated RC1 wrapper.
    direct=[]
    for p in base.glob('*.cs'):
        if p.resolve() == source:
            continue
        direct.append((p.name,p.read_text().count('ExecuteMarketOrder(')))
    total=sum(v for _,v in direct)
    central=commercial.read_text().count('ExecuteMarketOrder(')
    if total!=1 or central!=1:
        raise SystemExit('RC3A invariant failed: direct=%d central=%d files=%r' % (total,central,direct))
    if out.read_text().count('ExecuteMarketOrder(') != 0:
        raise SystemExit('RC3A generated main still contains a direct market-order call')
    if 'CommercialPortfolioAllows' in r26exec.read_text():
        raise SystemExit('RC3A inherited portfolio alpha veto')
    print('Commercial RC3A generated: v3.1 alpha preserved through unified Intent -> Risk -> Execution path; generated direct orders=1; frozen input alias excluded')


if __name__ == '__main__':
    if len(sys.argv)!=3:
        raise SystemExit('usage: commercial_rc3a_transform.py <store-main.cs> <rc3a-main.cs>')
    subprocess.run([
        sys.executable,
        'FibonacciHarmonicSniperUltimate/monthly-growth-v3/growth3_transform.py',
        sys.argv[1], sys.argv[2]
    ], check=True)
    transform_generated(sys.argv[2], sys.argv[1])
