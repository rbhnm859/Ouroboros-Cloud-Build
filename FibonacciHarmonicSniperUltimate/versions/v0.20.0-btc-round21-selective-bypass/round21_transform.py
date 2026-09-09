from pathlib import Path
import hashlib
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: round21_transform.py <round18.cs> <round21.cs>')

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
        [Parameter("R21 Selective Health Bypass", DefaultValue = true, Group = "BTC Round21 Selective Bypass")]
        public bool Round21SelectiveHealthBypass { get; set; }

        [Parameter("R21 Bypass Min Score", DefaultValue = 96.0, MinValue = 84.0, MaxValue = 100.0, Group = "BTC Round21 Selective Bypass")]
        public double Round21BypassMinScore { get; set; }

        [Parameter("R21 Same-Dir H1 Max Age (h)", DefaultValue = 2, MinValue = 1, MaxValue = 12, Group = "BTC Round21 Selective Bypass")]
        public int Round21SameDirH1MaxAgeHours { get; set; }

        [Parameter("R21 Bypass Risk % Equity", DefaultValue = 0.25, MinValue = 0.05, MaxValue = 0.50, Group = "BTC Round21 Selective Bypass")]
        public double Round21BypassRiskPercent { get; set; }

        [Parameter("R21 Reserve H1 At Hour", DefaultValue = true, Group = "BTC Round21 Selective Bypass")]
        public bool Round21ReserveH1AtHour { get; set; }
'''
if needle not in s:
    raise SystemExit('Round21 parameter anchor missing')
s=s.replace(needle,insert,1)

s=s.replace('Print("VERSION v0.17.0-btc-round18-diagnostics");','Print("VERSION v0.20.0-btc-round21-selective-bypass");',1)
s=s.replace('''            Print("BTC Round18 Diagnostics | candidate-first instrumentation={0} | trading gates and risk unchanged", Round18CandidateDiagnostics);
''','''            Print("BTC Round18 Diagnostics | candidate-first instrumentation={0}", Round18CandidateDiagnostics);
            Print("BTC Round21 Selective Bypass | enabled={0} minScore={1:F1} sameDirH1MaxAge={2}h bypassRisk={3:F2}% reserveH1AtHour={4}", Round21SelectiveHealthBypass, Round21BypassMinScore, Round21SameDirH1MaxAgeHours, Round21BypassRiskPercent, Round21ReserveH1AtHour);
''',1)

old='''        protected override void OnTick()
        {
            Round15ProcessM30ClosedBar();
'''
new='''        private void Round21ReserveH1Lane()
        {
            if (!Round21SelectiveHealthBypass || !Round21ReserveH1AtHour || Server.Time.Minute != 0)
                return;

            foreach (var p in Positions)
            {
                if (p.SymbolName != SymbolName || p.Label != BotLabel || string.IsNullOrEmpty(p.Comment) || !p.Comment.StartsWith("R21M30|", StringComparison.Ordinal))
                    continue;
                double heldMinutes = (Server.Time - p.EntryTime).TotalMinutes;
                if (heldMinutes < 20.0)
                    continue;
                Print("[R21 H1 RESERVATION] close optional M30 pos={0} dir={1} heldMin={2:F1}", p.Id, p.TradeType, heldMinutes);
                ClosePosition(p);
            }
        }

        protected override void OnTick()
        {
            Round21ReserveH1Lane();
            Round15ProcessM30ClosedBar();
'''
if old not in s:
    raise SystemExit('Round21 OnTick anchor missing')
s=s.replace(old,new,1)

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
new='''        private double Round21CalculateM30Volume(double slPips, double riskPercent)
        {
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

        private double Round17CalculateM30Volume(double slPips)
        {
            return Round21CalculateM30Volume(slPips, Round17M30RiskPercent);
        }

        private bool Round21HasRecentSameDirectionH1(TradeType direction, out int ageHours)
        {
            ageHours = -1;
            Round5FrameState h1 = Round18FindH1StateForDirection(direction);
            if (h1 == null)
                return false;
            ageHours = h1.AgeBars;
            return ageHours >= 0 && ageHours <= Round21SameDirH1MaxAgeHours;
        }

        private bool Round21BypassEligible(PatternMatch best, bool confirmationPassed, out int h1Age)
        {
            h1Age = -1;
            if (!Round21SelectiveHealthBypass || best == null || !confirmationPassed || !best.TrendAligned)
                return false;
            if (best.Score + 1e-9 < Round21BypassMinScore)
                return false;
            return Round21HasRecentSameDirectionH1(best.Direction, out h1Age);
        }
'''
if old not in s:
    raise SystemExit('Round21 volume anchor missing')
s=s.replace(old,new,1)

old='''            bool healthAllowed = Round16H1HealthAllowsM30();
            if (!healthAllowed)
            {
                _r16M30BlockedHealth++;
                if (best != null)
                    Round18RecordCandidate(best, lastClosed, confirmationPassed, "HEALTH");
                return;
            }
'''
new='''            bool healthAllowed = Round16H1HealthAllowsM30();
            bool round21Bypass = false;
            int round21H1Age = -1;
            if (!healthAllowed)
                round21Bypass = Round21BypassEligible(best, confirmationPassed, out round21H1Age);

            if (!healthAllowed && !round21Bypass)
            {
                _r16M30BlockedHealth++;
                if (best != null)
                    Round18RecordCandidate(best, lastClosed, confirmationPassed, "HEALTH");
                return;
            }

            if (round21Bypass)
                Print("[R21 BYPASS] time={0:yyyy-MM-ddTHH:mm:ss} dir={1} score={2:F2} h1AgeH={3} risk={4:F2}%", _barsM30.OpenTimes[lastClosed], best.Direction, best.Score, round21H1Age, Round21BypassRiskPercent);
'''
if old not in s:
    raise SystemExit('Round21 health gate anchor missing')
s=s.replace(old,new,1)

s=s.replace('''            Round18RecordCandidate(best, lastClosed, true, "EXECUTE");
            Round15ExecuteM30(best, lastClosed);
''','''            Round18RecordCandidate(best, lastClosed, true, round21Bypass ? "EXECUTE:R21_BYPASS" : "EXECUTE");
            Round15ExecuteM30(best, lastClosed, round21Bypass);
''',1)

s=s.replace('''        private void Round15ExecuteM30(PatternMatch m, int lastClosed)
''','''        private void Round15ExecuteM30(PatternMatch m, int lastClosed, bool round21Bypass)
''',1)
s=s.replace('''            double volume=Round17CalculateM30Volume(slPips);
''','''            double riskPercent = round21Bypass ? Round21BypassRiskPercent : Round17M30RiskPercent;
            double volume=Round21CalculateM30Volume(slPips, riskPercent);
''',1)
s=s.replace('''            string patternName="M30|"+m.Definition.Name;
''','''            string patternName=(round21Bypass ? "R21M30|" : "M30|")+m.Definition.Name;
''',1)
s=s.replace('''            Print("[R15 M30 OPEN] {0} {1} score={2:F1}% volume={3} SL={4:F1}p TP={5:F1}p RR={6:F2}",m.Definition.Name,m.Direction,m.Score,volume,slPips,tpPips,tpPips/slPips);
''','''            Print("[R15 M30 OPEN] {0} {1} score={2:F1}% volume={3} riskPct={4:F2} optionalBypass={5} SL={6:F1}p TP={7:F1}p RR={8:F2}",m.Definition.Name,m.Direction,m.Score,volume,riskPercent,round21Bypass,slPips,tpPips,tpPips/slPips);
''',1)

out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(s, encoding='utf-8')
actual_r21=hashlib.sha256(out_path.read_bytes()).hexdigest()
expected_r21='4ed08a5efd3f3ba4b6c438686396a63e6747b07747cd3e318d946868ce424153'
if actual_r21 != expected_r21:
    raise SystemExit(f'Round21 source SHA mismatch: {actual_r21} != {expected_r21}')
print(f'Round21 source verified: {actual_r21}')
