from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit('usage: store_v1_unified_risk_patch.py <store-src-dir>')
d=Path(sys.argv[1]); risk=d/'Round26.Risk.cs'; safe=d/'Store.Safety.cs'
rs=risk.read_text()
old='''        private double Round26RiskH1Volume(double slPips, TradeType direction)
        {
            return Round22CalculateH1Volume(slPips, direction);
        }

        private double Round26RiskM30Volume(double slPips, double riskPercent)
        {
            return Round21CalculateM30Volume(slPips, riskPercent);
        }
'''
new='''        private double Round26RiskH1Volume(double slPips, TradeType direction)
        {
            double riskPercent = direction == TradeType.Buy ? Round22H1BuyRiskPercent : Round22H1SellRiskPercent;
            return StoreUnifiedRiskVolume(slPips, riskPercent);
        }

        private double Round26RiskM30Volume(double slPips, double riskPercent)
        {
            return StoreUnifiedRiskVolume(slPips, riskPercent);
        }
'''
if old not in rs: raise SystemExit('Round26 risk anchor missing')
risk.write_text(rs.replace(old,new,1))
ss=safe.read_text()
anchor='''        private bool StoreValidateOrder(TradeType direction, double volume, double slPips, double tpPips, double riskPercent, string lane)
'''
helper='''        private double StoreUnifiedRiskVolume(double slPips, double riskPercent)
        {
            if (RiskMode != RiskSizingMode.RiskPercentEquity || slPips <= 0 || riskPercent <= 0)
                return 0;
            double budget = Account.Equity * riskPercent / 100.0;
            double raw = Symbol.VolumeForFixedRisk(budget, slPips, RoundingMode.Down);
            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0)
                return 0;
            raw = Symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (raw < Symbol.VolumeInUnitsMin || raw > Symbol.VolumeInUnitsMax)
                return 0;
            double estimated = Symbol.AmountRisked(raw, slPips);
            if (double.IsNaN(estimated) || double.IsInfinity(estimated) || estimated <= 0 || estimated > budget + Math.Max(0.01, budget * 0.0025))
            {
                Print("[STORE RISK SIZE REJECT] volume={0} estimated={1:F4} budget={2:F4} riskPct={3:F4}", raw, estimated, budget, riskPercent);
                return 0;
            }
            return raw;
        }

'''+anchor
if anchor not in ss: raise SystemExit('StoreValidateOrder anchor missing')
safe.write_text(ss.replace(anchor,helper,1))
print('Store unified risk patch applied')
