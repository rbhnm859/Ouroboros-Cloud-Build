from pathlib import Path
import hashlib
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: round19_transform.py <round18.cs> <round19.cs>')

src_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
data = src_path.read_bytes()
expected_r18 = '5f2b7f31c4b8f0d60f52c4c15869aa75df4ff07d7224af971784137716bc8b93'
actual_r18 = hashlib.sha256(data).hexdigest()
if actual_r18 != expected_r18:
    raise SystemExit(f'Round18 source SHA mismatch: {actual_r18} != {expected_r18}')
s = data.decode('utf-8')

needle='''        [Parameter("R18 Candidate Diagnostics", DefaultValue = true, Group = "BTC Round18 Diagnostics")]
        public bool Round18CandidateDiagnostics { get; set; }
'''
insert=needle+'''
        [Parameter("R19 Quality Expansion", DefaultValue = true, Group = "BTC Round19 Expansion")]
        public bool Round19QualityExpansion { get; set; }

        [Parameter("R19 H1 Align Max Age (h)", DefaultValue = 6, MinValue = 1, MaxValue = 16, Group = "BTC Round19 Expansion")]
        public int Round19H1AlignMaxAgeHours { get; set; }

        [Parameter("R19 M30 Buy Risk %", DefaultValue = 0.35, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round19 Expansion")]
        public double Round19M30BuyRiskPercent { get; set; }

        [Parameter("R19 M30 Sell Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round19 Expansion")]
        public double Round19M30SellRiskPercent { get; set; }

        [Parameter("R19 Aligned Buy Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round19 Expansion")]
        public double Round19AlignedBuyRiskPercent { get; set; }
'''
if needle not in s: raise SystemExit('Round19 parameter insertion anchor missing')
s=s.replace(needle,insert,1)

s=s.replace('Print("VERSION v0.17.0-btc-round18-diagnostics");','Print("VERSION v0.18.0-btc-round19-quality-expansion");',1)
s=s.replace('''            Print("BTC Round18 Diagnostics | candidate-first instrumentation={0} | trading gates and risk unchanged", Round18CandidateDiagnostics);
''','''            Print("BTC Round18 Diagnostics | candidate-first instrumentation={0}", Round18CandidateDiagnostics);
            Print("BTC Round19 Quality Expansion | enabled={0} | H1 align max age={1}h | M30 buy risk={2:F2}% | aligned buy risk={3:F2}% | sell risk={4:F2}%", Round19QualityExpansion, Round19H1AlignMaxAgeHours, Round19M30BuyRiskPercent, Round19AlignedBuyRiskPercent, Round19M30SellRiskPercent);
''',1)

old='''        private double Round17CalculateM30Volume(double slPips)
        {
            if (slPips <= 0 || Round17M30RiskPercent <= 0)
                return 0;
            double amount = Account.Equity * Round17M30RiskPercent / 100.0;
            double raw = Symbol.VolumeForFixedRisk(amount, slPips, RoundingMode.Down);
            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0)
                return 0;
            raw = Symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (raw > Symbol.VolumeInUnitsMax)
                raw = Symbol.VolumeInUnitsMax;
            return raw;
        }
'''
new='''        private bool Round19HasRecentSameDirectionH1(TradeType direction, out int ageHours)
        {
            ageHours = -1;
            Round5FrameState h1 = Round18FindH1StateForDirection(direction);
            if (h1 == null)
                return false;
            ageHours = h1.AgeBars;
            return ageHours >= 0 && ageHours <= Round19H1AlignMaxAgeHours;
        }

        private double Round19M30RiskFor(TradeType direction)
        {
            if (!Round19QualityExpansion)
                return Round17M30RiskPercent;

            if (direction == TradeType.Sell)
                return Round19M30SellRiskPercent;

            int h1Age;
            if (Round19HasRecentSameDirectionH1(direction, out h1Age))
                return Round19AlignedBuyRiskPercent;
            return Round19M30BuyRiskPercent;
        }

        private double Round17CalculateM30Volume(double slPips, TradeType direction)
        {
            double riskPercent = Round19M30RiskFor(direction);
            if (slPips <= 0 || riskPercent <= 0)
                return 0;
            double amount = Account.Equity * riskPercent / 100.0;
            double raw = Symbol.VolumeForFixedRisk(amount, slPips, RoundingMode.Down);
            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0)
                return 0;
            raw = Symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (raw > Symbol.VolumeInUnitsMax)
                raw = Symbol.VolumeInUnitsMax;
            return raw;
        }
'''
if old not in s: raise SystemExit('Round19 risk transform anchor missing')
s=s.replace(old,new,1)

old='''            bool healthAllowed = Round16H1HealthAllowsM30();
            if (!healthAllowed)
            {
                _r16M30BlockedHealth++;
                if (best != null)
                    Round18RecordCandidate(best, lastClosed, confirmationPassed, "HEALTH");
                return;
            }

            if (!Round15PassSharedLimits(lastClosed))
'''
new='''            bool healthAllowed = Round16H1HealthAllowsM30();
            bool round19Bypass = false;
            int round19H1Age = -1;
            if (!healthAllowed && Round19QualityExpansion && best != null && confirmationPassed && best.TrendAligned)
                round19Bypass = Round19HasRecentSameDirectionH1(best.Direction, out round19H1Age);

            if (!healthAllowed && !round19Bypass)
            {
                _r16M30BlockedHealth++;
                if (best != null)
                    Round18RecordCandidate(best, lastClosed, confirmationPassed, "HEALTH");
                return;
            }

            if (round19Bypass)
                Print("[R19 HEALTH BYPASS] time={0:yyyy-MM-ddTHH:mm:ss} dir={1} score={2:F2} h1AgeH={3} emaAligned={4} confirm={5}", _barsM30.OpenTimes[lastClosed], best.Direction, best.Score, round19H1Age, best.TrendAligned, confirmationPassed);

            if (!Round15PassSharedLimits(lastClosed))
'''
if old not in s: raise SystemExit('Round19 gate transform anchor missing')
s=s.replace(old,new,1)

s=s.replace('double volume=Round17CalculateM30Volume(slPips);','double volume=Round17CalculateM30Volume(slPips, m.Direction);',1)
s=s.replace('''            Print("[R15 M30 OPEN] {0} {1} score={2:F1}% volume={3} SL={4:F1}p TP={5:F1}p RR={6:F2}",m.Definition.Name,m.Direction,m.Score,volume,slPips,tpPips,tpPips/slPips);
''','''            Print("[R15 M30 OPEN] {0} {1} score={2:F1}% volume={3} riskPct={4:F2} SL={5:F1}p TP={6:F1}p RR={7:F2}",m.Definition.Name,m.Direction,m.Score,volume,Round19M30RiskFor(m.Direction),slPips,tpPips,tpPips/slPips);
''',1)

out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(s, encoding='utf-8')
expected_r19='c408a95259b791937a52490fe4472a1f1799edca53e87a4b4fedd08115484b98'
actual_r19=hashlib.sha256(out_path.read_bytes()).hexdigest()
if actual_r19 != expected_r19:
    raise SystemExit(f'Round19 source SHA mismatch: {actual_r19} != {expected_r19}')
print(f'Round19 source verified: {actual_r19}')
