from pathlib import Path
import hashlib, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: round19_refine_v2.py <round19-v1.cs> <round19-v2.cs>')

src=Path(sys.argv[1]); out=Path(sys.argv[2])
data=src.read_bytes()
expected_v1='c408a95259b791937a52490fe4472a1f1799edca53e87a4b4fedd08115484b98'
actual=hashlib.sha256(data).hexdigest()
if actual != expected_v1:
    raise SystemExit(f'Round19 v1 SHA mismatch: {actual} != {expected_v1}')
s=data.decode('utf-8')

s=s.replace('Print("VERSION v0.18.0-btc-round19-quality-expansion");',
            'Print("VERSION v0.18.1-btc-round19-quality-expansion-v2");',1)
s=s.replace('[Parameter("R19 H1 Align Max Age (h)", DefaultValue = 6, MinValue = 1, MaxValue = 16, Group = "BTC Round19 Expansion")]',
            '[Parameter("R19 H1 Align Max Age (h)", DefaultValue = 2, MinValue = 1, MaxValue = 16, Group = "BTC Round19 Expansion")]',1)
s=s.replace('[Parameter("R19 M30 Buy Risk %", DefaultValue = 0.35, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round19 Expansion")]',
            '[Parameter("R19 M30 Buy Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round19 Expansion")]',1)

needle='''        [Parameter("R19 Aligned Buy Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round19 Expansion")]
        public double Round19AlignedBuyRiskPercent { get; set; }
'''
insert=needle+'''
        [Parameter("R19 Min Bypass Score", DefaultValue = 96.0, MinValue = 84.0, MaxValue = 100.0, Group = "BTC Round19 Expansion")]
        public double Round19MinBypassScore { get; set; }

        [Parameter("R19 H1 Sell Risk %", DefaultValue = 0.95, MinValue = 0.10, MaxValue = 2.0, Group = "BTC Round19 Expansion")]
        public double Round19H1SellRiskPercent { get; set; }
'''
if needle not in s:
    raise SystemExit('v2 parameter anchor missing')
s=s.replace(needle,insert,1)

old='''            if (!healthAllowed && Round19QualityExpansion && best != null && confirmationPassed && best.TrendAligned)
                round19Bypass = Round19HasRecentSameDirectionH1(best.Direction, out round19H1Age);
'''
new='''            if (!healthAllowed && Round19QualityExpansion && best != null && confirmationPassed && best.TrendAligned &&
                best.Direction == TradeType.Buy && best.Score >= Round19MinBypassScore)
                round19Bypass = Round19HasRecentSameDirectionH1(best.Direction, out round19H1Age);
'''
if old not in s:
    raise SystemExit('v2 gate anchor missing')
s=s.replace(old,new,1)

old='''            double volume = CalculateVolume(slPips);
'''
new='''            double volume = CalculateVolume(slPips, m.Direction);
'''
if old not in s:
    raise SystemExit('v2 H1 call anchor missing')
s=s.replace(old,new,1)

old='''        private double CalculateVolume(double slPips)
        {
            double raw;
            if (RiskMode == RiskSizingMode.FixedLots)
            {
                raw = Symbol.QuantityToVolumeInUnits(FixedLots);
            }
            else
            {
                double amount = RiskMode == RiskSizingMode.FixedRiskCash
                    ? FixedRiskCash
                    : Account.Equity * RiskPercent / 100.0;
                raw = Symbol.VolumeForFixedRisk(amount, slPips, RoundingMode.Down);
            }

            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0)
                return 0;

            raw = Symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (raw > Symbol.VolumeInUnitsMax)
                raw = Symbol.VolumeInUnitsMax;
            if (RiskMode != RiskSizingMode.FixedLots)
            {
                double budget = RiskMode == RiskSizingMode.FixedRiskCash ? FixedRiskCash : Account.Equity * RiskPercent / 100.0;
                double estimated = Symbol.AmountRisked(raw, slPips);
                if (double.IsNaN(estimated) || double.IsInfinity(estimated) || estimated <= 0 || estimated > budget + 1e-8)
                {
                    Reject("risk_budget_exceeded");
                    Print("[RISK REJECT] volume={0} estimated={1:F4} budget={2:F4} min={3} pipValue={4}", raw, estimated, budget, Symbol.VolumeInUnitsMin, Symbol.PipValue);
                    return 0;
                }
            }
            return raw;
        }
'''
new='''        private double CalculateVolume(double slPips, TradeType direction)
        {
            double raw;
            double percentRisk = Round19QualityExpansion && direction == TradeType.Sell
                ? Round19H1SellRiskPercent
                : RiskPercent;
            if (RiskMode == RiskSizingMode.FixedLots)
            {
                raw = Symbol.QuantityToVolumeInUnits(FixedLots);
            }
            else
            {
                double amount = RiskMode == RiskSizingMode.FixedRiskCash
                    ? FixedRiskCash
                    : Account.Equity * percentRisk / 100.0;
                raw = Symbol.VolumeForFixedRisk(amount, slPips, RoundingMode.Down);
            }

            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0)
                return 0;

            raw = Symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (raw > Symbol.VolumeInUnitsMax)
                raw = Symbol.VolumeInUnitsMax;
            if (RiskMode != RiskSizingMode.FixedLots)
            {
                double budget = RiskMode == RiskSizingMode.FixedRiskCash ? FixedRiskCash : Account.Equity * percentRisk / 100.0;
                double estimated = Symbol.AmountRisked(raw, slPips);
                if (double.IsNaN(estimated) || double.IsInfinity(estimated) || estimated <= 0 || estimated > budget + 1e-8)
                {
                    Reject("risk_budget_exceeded");
                    Print("[RISK REJECT] volume={0} estimated={1:F4} budget={2:F4} min={3} pipValue={4}", raw, estimated, budget, Symbol.VolumeInUnitsMin, Symbol.PipValue);
                    return 0;
                }
            }
            return raw;
        }
'''
if old not in s:
    raise SystemExit('v2 H1 method anchor missing')
s=s.replace(old,new,1)

out.write_text(s,encoding='utf-8')
expected_v2='ad531ff93236f48d8fa23ff4ef539e1e016a7b9697062398873ab67ee1f41113'
actual_v2=hashlib.sha256(out.read_bytes()).hexdigest()
if actual_v2 != expected_v2:
    raise SystemExit(f'Round19 v2 SHA mismatch: {actual_v2} != {expected_v2}')
print(f'Round19 v2 source verified: {actual_v2}')
