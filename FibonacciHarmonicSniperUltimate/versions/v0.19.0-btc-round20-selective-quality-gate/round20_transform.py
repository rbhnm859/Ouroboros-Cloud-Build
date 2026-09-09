from pathlib import Path
import hashlib
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: round20_transform.py <round19.cs> <round20.cs>')

src_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
data = src_path.read_bytes()
expected_r19 = 'c408a95259b791937a52490fe4472a1f1799edca53e87a4b4fedd08115484b98'
actual_r19 = hashlib.sha256(data).hexdigest()
if actual_r19 != expected_r19:
    raise SystemExit(f'Round19 source SHA mismatch: {actual_r19} != {expected_r19}')
s = data.decode('utf-8')

s = s.replace(
    '[Parameter("R19 M30 Buy Risk %", DefaultValue = 0.35, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round19 Expansion")]',
    '[Parameter("R19 M30 Buy Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round19 Expansion")]',
    1,
)

needle = '''        [Parameter("R19 Aligned Buy Risk %", DefaultValue = 0.50, MinValue = 0.05, MaxValue = 2.0, Group = "BTC Round19 Expansion")]
        public double Round19AlignedBuyRiskPercent { get; set; }
'''
insert = needle + '''
        [Parameter("R20 Selective Health Bypass", DefaultValue = true, Group = "BTC Round20 Quality Gate")]
        public bool Round20SelectiveHealthBypass { get; set; }

        [Parameter("R20 Allow Buy Bypass", DefaultValue = true, Group = "BTC Round20 Quality Gate")]
        public bool Round20AllowBuyBypass { get; set; }

        [Parameter("R20 Allow Sell Bypass", DefaultValue = false, Group = "BTC Round20 Quality Gate")]
        public bool Round20AllowSellBypass { get; set; }

        [Parameter("R20 Bypass Buy Min Score %", DefaultValue = 96.0, MinValue = 50.0, MaxValue = 100.0, Group = "BTC Round20 Quality Gate")]
        public double Round20BypassBuyMinScore { get; set; }

        [Parameter("R20 Bypass Max H1 Age (h)", DefaultValue = 2, MinValue = 1, MaxValue = 16, Group = "BTC Round20 Quality Gate")]
        public int Round20BypassMaxH1AgeHours { get; set; }
'''
if needle not in s:
    raise SystemExit('Round20 parameter insertion anchor missing')
s = s.replace(needle, insert, 1)

s = s.replace(
    'Print("VERSION v0.18.0-btc-round19-quality-expansion");',
    'Print("VERSION v0.19.0-btc-round20-selective-quality-gate");',
    1,
)

old_print = '''            Print("BTC Round19 Quality Expansion | enabled={0} | H1 align max age={1}h | M30 buy risk={2:F2}% | aligned buy risk={3:F2}% | sell risk={4:F2}%", Round19QualityExpansion, Round19H1AlignMaxAgeHours, Round19M30BuyRiskPercent, Round19AlignedBuyRiskPercent, Round19M30SellRiskPercent);
'''
new_print = old_print + '''            Print("BTC Round20 Selective Gate | enabled={0} | buy={1} sell={2} | buyScore>={3:F1} | H1Age<={4}h", Round20SelectiveHealthBypass, Round20AllowBuyBypass, Round20AllowSellBypass, Round20BypassBuyMinScore, Round20BypassMaxH1AgeHours);
'''
if old_print not in s:
    raise SystemExit('Round20 print anchor missing')
s = s.replace(old_print, new_print, 1)

risk_anchor = '''        private double Round19M30RiskFor(TradeType direction)
        {
'''
quality_helper = '''        private bool Round20HealthBypassAllows(PatternMatch m, bool confirmationPassed, out int ageHours)
        {
            ageHours = -1;
            if (m == null || !confirmationPassed || !m.TrendAligned)
                return false;

            if (!Round20SelectiveHealthBypass)
                return Round19HasRecentSameDirectionH1(m.Direction, out ageHours);

            if (m.Direction == TradeType.Buy)
            {
                if (!Round20AllowBuyBypass || m.Score < Round20BypassBuyMinScore)
                    return false;
            }
            else
            {
                if (!Round20AllowSellBypass)
                    return false;
            }

            Round5FrameState h1 = Round18FindH1StateForDirection(m.Direction);
            if (h1 == null)
                return false;
            ageHours = h1.AgeBars;
            return ageHours >= 0 && ageHours <= Round20BypassMaxH1AgeHours;
        }

'''
if risk_anchor not in s:
    raise SystemExit('Round20 helper insertion anchor missing')
s = s.replace(risk_anchor, quality_helper + risk_anchor, 1)

old_gate = '''            bool healthAllowed = Round16H1HealthAllowsM30();
            bool round19Bypass = false;
            int round19H1Age = -1;
            if (!healthAllowed && Round19QualityExpansion && best != null && confirmationPassed && best.TrendAligned)
                round19Bypass = Round19HasRecentSameDirectionH1(best.Direction, out round19H1Age);
'''
new_gate = '''            bool healthAllowed = Round16H1HealthAllowsM30();
            bool round19Bypass = false;
            int round19H1Age = -1;
            if (!healthAllowed && Round19QualityExpansion)
                round19Bypass = Round20HealthBypassAllows(best, confirmationPassed, out round19H1Age);
'''
if old_gate not in s:
    raise SystemExit('Round20 gate anchor missing')
s = s.replace(old_gate, new_gate, 1)

s = s.replace(
    'Print("[R19 HEALTH BYPASS] time={0:yyyy-MM-ddTHH:mm:ss} dir={1} score={2:F2} h1AgeH={3} emaAligned={4} confirm={5}", _barsM30.OpenTimes[lastClosed], best.Direction, best.Score, round19H1Age, best.TrendAligned, confirmationPassed);',
    'Print("[R20 HEALTH BYPASS] time={0:yyyy-MM-ddTHH:mm:ss} dir={1} score={2:F2} h1AgeH={3} emaAligned={4} confirm={5}", _barsM30.OpenTimes[lastClosed], best.Direction, best.Score, round19H1Age, best.TrendAligned, confirmationPassed);',
    1,
)

out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(s, encoding='utf-8')
expected_r20 = '5916aede6a0fdee5fe5db0c6baa5262213cb07184210ae77036a5cb83dea0691'
actual_r20 = hashlib.sha256(out_path.read_bytes()).hexdigest()
if actual_r20 != expected_r20:
    raise SystemExit(f'Round20 source SHA mismatch: {actual_r20} != {expected_r20}')
print(f'Round20 source verified: {actual_r20}')
