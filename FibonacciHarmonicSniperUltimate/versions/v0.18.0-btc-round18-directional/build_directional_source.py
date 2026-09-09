from pathlib import Path
import base64
import gzip
import hashlib

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / "v0.17.0-btc-round18-diagnostics"
OUT = ROOT / "FibonacciHarmonicSniperUltimate-BTC-Round18-Directional.cs"
PARENT_SHA = "80390542f4eff2cc1f8a0f804090c3c5598441057ade12f3c8bb4b62f38dfeb0"
OUTPUT_SHA = "d82b55350e2f809f204df97a46bea5c4046508296d534c813e6e983ff54e8d66"

payload = "".join(p.read_text() for p in sorted(PARENT.glob("source_payload.part*"))).strip()
raw = gzip.decompress(base64.b64decode(payload))
if hashlib.sha256(raw).hexdigest() != PARENT_SHA:
    raise SystemExit("parent diagnostics source SHA mismatch")

s = raw.decode("utf-8")
s = s.replace('Print("VERSION v0.17.0-btc-round18-diagnostics");', 'Print("VERSION v0.18.0-btc-round18-directional");')

param_anchor = "        public bool Round18CandidateDiagnostics { get; set; }\n"
params = param_anchor + '''

        [Parameter("R18 Directional Expansion", DefaultValue = true, Group = "BTC Round18 Expansion")]
        public bool Round18DirectionalExpansion { get; set; }

        [Parameter("R18 H1 Align Max Age Hours", DefaultValue = 12, MinValue = 1, MaxValue = 24, Group = "BTC Round18 Expansion")]
        public int Round18H1AlignMaxAgeHours { get; set; }

        [Parameter("R18 Standalone M30 Buy Risk %", DefaultValue = 0.35, MinValue = 0.05, MaxValue = 0.50, Group = "BTC Round18 Expansion")]
        public double Round18StandaloneM30BuyRiskPercent { get; set; }
'''
if param_anchor not in s:
    raise SystemExit("parameter anchor missing")
s = s.replace(param_anchor, params, 1)

start = s.index("        private double Round17CalculateM30Volume(double slPips)")
end = s.index("        private bool Round16H1HealthAllowsM30()", start)
risk_code = '''        private double Round18CalculateM30Volume(double slPips, double riskPercent)
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

        private bool Round18HasRecentSameDirectionH1(PatternMatch m)
        {
            if (!Round18DirectionalExpansion || m == null)
                return false;
            Round5FrameState h1Same = Round18FindH1StateForDirection(m.Direction);
            return h1Same != null && h1Same.AgeBars >= 0 && h1Same.AgeBars <= Round18H1AlignMaxAgeHours;
        }

        private double Round18RiskForM30(PatternMatch m, bool aligned)
        {
            if (!Round18DirectionalExpansion || m == null)
                return Round17M30RiskPercent;
            if (m.Direction == TradeType.Buy && !aligned)
                return Math.Min(Round17M30RiskPercent, Round18StandaloneM30BuyRiskPercent);
            return Round17M30RiskPercent;
        }

'''
s = s[:start] + risk_code + s[end:]

health_start = s.index("            bool healthAllowed = Round16H1HealthAllowsM30();")
health_end = s.index("            if (!Round15PassSharedLimits(lastClosed))", health_start)
health_code = '''            bool alignedLane = Round18HasRecentSameDirectionH1(best);
            bool healthAllowed = Round16H1HealthAllowsM30();
            bool directionalHealthBypass = Round18DirectionalExpansion && best != null && alignedLane;
            if (!healthAllowed && !directionalHealthBypass)
            {
                _r16M30BlockedHealth++;
                if (best != null)
                    Round18RecordCandidate(best, lastClosed, confirmationPassed, "HEALTH");
                return;
            }

'''
s = s[:health_start] + health_code + s[health_end:]

exec_old = '''            Round18RecordCandidate(best, lastClosed, true, "EXECUTE");
            Round15ExecuteM30(best, lastClosed);
'''
exec_new = '''            double m30RiskPercent = Round18RiskForM30(best, alignedLane);
            string lane = alignedLane ? "ALIGNED" : "STANDALONE";
            Round18RecordCandidate(best, lastClosed, true, "EXECUTE:" + lane);
            Round15ExecuteM30(best, lastClosed, m30RiskPercent, lane);
'''
if exec_old not in s:
    raise SystemExit("execute anchor missing")
s = s.replace(exec_old, exec_new, 1)

s = s.replace("private void Round15ExecuteM30(PatternMatch m, int lastClosed)", "private void Round15ExecuteM30(PatternMatch m, int lastClosed, double riskPercent, string lane)", 1)
s = s.replace("double volume=Round17CalculateM30Volume(slPips);", "double volume=Round18CalculateM30Volume(slPips,riskPercent);", 1)
s = s.replace('Print("[R15 M30 OPEN] {0} {1} score={2:F1}% volume={3} SL={4:F1}p TP={5:F1}p RR={6:F2}",m.Definition.Name,m.Direction,m.Score,volume,slPips,tpPips,tpPips/slPips);', 'Print("[R18 M30 OPEN] lane={0} {1} {2} score={3:F1}% risk={4:F2}% volume={5} SL={6:F1}p TP={7:F1}p RR={8:F2}",lane,m.Definition.Name,m.Direction,m.Score,riskPercent,volume,slPips,tpPips,tpPips/slPips);', 1)
s = s.replace('else if (finalGate == "EXECUTE") _r18ExecuteCandidates++;', 'else if (finalGate.StartsWith("EXECUTE", StringComparison.Ordinal)) _r18ExecuteCandidates++;', 1)

startup = '            Print("BTC Round18 Diagnostics | candidate-first instrumentation={0} | trading gates and risk unchanged", Round18CandidateDiagnostics);\n'
if startup not in s:
    raise SystemExit("startup anchor missing")
s = s.replace(startup, startup + '            Print("BTC Round18 Directional Expansion | enabled={0} | H1 same-dir max age={1}h | standalone M30 Buy risk={2:F2}% | M30 Sell cap={3:F2}%", Round18DirectionalExpansion, Round18H1AlignMaxAgeHours, Round18StandaloneM30BuyRiskPercent, Round17M30RiskPercent);\n', 1)

out_bytes = s.encode("utf-8")
actual = hashlib.sha256(out_bytes).hexdigest()
if actual != OUTPUT_SHA:
    raise SystemExit(f"output SHA mismatch: {actual} != {OUTPUT_SHA}")
OUT.write_bytes(out_bytes)
(ROOT / "FibonacciHarmonicSniperUltimate-BTC-Round18-Directional.csproj").write_text('''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
    <ImplicitUsings>disable</ImplicitUsings>
    <Nullable>disable</Nullable>
    <RootNamespace>cAlgo.Robots</RootNamespace>
    <AlgoName>FibonacciHarmonicSniperUltimate-BTC-Round18-Directional</AlgoName>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="cTrader.Automate" Version="1.0.19" />
  </ItemGroup>
</Project>
''')
print(f"created {OUT} SHA256={actual}")
