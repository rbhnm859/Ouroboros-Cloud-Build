from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit('usage: round22_transform.py <round21.cs> <round22.cs>')
src=Path(sys.argv[1]); out=Path(sys.argv[2]); data=src.read_bytes()
exp21='4ed08a5efd3f3ba4b6c438686396a63e6747b07747cd3e318d946868ce424153'
act21=hashlib.sha256(data).hexdigest()
if act21!=exp21: raise SystemExit(f'Round21 SHA mismatch {act21}')
s=data.decode()
needle='''        [Parameter("R21 Reserve H1 At Hour", DefaultValue = true, Group = "BTC Round21 Selective Bypass")]
        public bool Round21ReserveH1AtHour { get; set; }
'''
insert=needle+'''
        [Parameter("R22 H1 Buy Risk %", DefaultValue = 1.15, MinValue = 0.25, MaxValue = 2.0, Group = "BTC Round22 Capital Efficiency")]
        public double Round22H1BuyRiskPercent { get; set; }

        [Parameter("R22 H1 Sell Risk %", DefaultValue = 0.80, MinValue = 0.25, MaxValue = 2.0, Group = "BTC Round22 Capital Efficiency")]
        public double Round22H1SellRiskPercent { get; set; }

        [Parameter("R22 M30 Buy Risk %", DefaultValue = 0.40, MinValue = 0.05, MaxValue = 1.0, Group = "BTC Round22 Capital Efficiency")]
        public double Round22M30BuyRiskPercent { get; set; }

        [Parameter("R22 M30 Sell Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 1.0, Group = "BTC Round22 Capital Efficiency")]
        public double Round22M30SellRiskPercent { get; set; }
'''
if needle not in s: raise SystemExit('param anchor missing')
s=s.replace(needle,insert,1)
s=s.replace('Print("VERSION v0.20.0-btc-round21-selective-bypass");','Print("VERSION v0.21.0-btc-round22-capital-efficiency");',1)
old='''            Print("BTC Round21 Selective Bypass | enabled={0} minScore={1:F1} sameDirH1MaxAge={2}h bypassRisk={3:F2}% reserveH1AtHour={4}", Round21SelectiveHealthBypass, Round21BypassMinScore, Round21SameDirH1MaxAgeHours, Round21BypassRiskPercent, Round21ReserveH1AtHour);
'''
new=old+'''            Print("BTC Round22 Capital Efficiency | H1 Buy={0:F2}% H1 Sell={1:F2}% M30 Buy={2:F2}% M30 Sell={3:F2}%", Round22H1BuyRiskPercent, Round22H1SellRiskPercent, Round22M30BuyRiskPercent, Round22M30SellRiskPercent);
'''
if old not in s: raise SystemExit('print anchor missing')
s=s.replace(old,new,1)
old='''            double riskPercent = round21Bypass ? Round21BypassRiskPercent : Round17M30RiskPercent;
'''
new='''            double riskPercent = round21Bypass ? Round21BypassRiskPercent : (m.Direction == TradeType.Buy ? Round22M30BuyRiskPercent : Round22M30SellRiskPercent);
'''
if old not in s: raise SystemExit('m30 risk anchor missing')
s=s.replace(old,new,1)
old='''            double volume = CalculateVolume(slPips);
'''
new='''            double volume = Round22CalculateH1Volume(slPips, m.Direction);
'''
if old not in s: raise SystemExit('h1 volume call anchor missing')
s=s.replace(old,new,1)
needle='''        private double CalculateVolume(double slPips)
        {
'''
helper='''        private double Round22CalculateH1Volume(double slPips, TradeType direction)
        {
            if (RiskMode != RiskSizingMode.RiskPercentEquity)
                return CalculateVolume(slPips);
            double riskPercent = direction == TradeType.Buy ? Round22H1BuyRiskPercent : Round22H1SellRiskPercent;
            if (slPips <= 0 || riskPercent <= 0)
                return 0;
            double budget = Account.Equity * riskPercent / 100.0;
            double raw = Symbol.VolumeForFixedRisk(budget, slPips, RoundingMode.Down);
            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0)
                return 0;
            raw = Symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (raw > Symbol.VolumeInUnitsMax)
                raw = Symbol.VolumeInUnitsMax;
            double estimated = Symbol.AmountRisked(raw, slPips);
            if (double.IsNaN(estimated) || double.IsInfinity(estimated) || estimated <= 0 || estimated > budget + 1e-8)
            {
                Reject("risk_budget_exceeded");
                Print("[R22 RISK REJECT] dir={0} volume={1} estimated={2:F4} budget={3:F4}", direction, raw, estimated, budget);
                return 0;
            }
            return raw;
        }

'''+needle
if needle not in s: raise SystemExit('helper anchor missing')
s=s.replace(needle,helper,1)
out.write_text(s)
sha=hashlib.sha256(out.read_bytes()).hexdigest()
exp22='d103dce25851d89bd51cb736c14ae91f416927dedfc692a441f28115a3343029'
if sha!=exp22: raise SystemExit(f'Round22 SHA mismatch {sha}')
print(f'Round22 source verified: {sha}')
