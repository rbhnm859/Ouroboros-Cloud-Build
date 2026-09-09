from pathlib import Path
import hashlib, sys

if len(sys.argv) != 3:
    raise SystemExit("usage: round26_transform.py <round22.cs> <round26-main.cs>")

src = Path(sys.argv[1])
out = Path(sys.argv[2])
data = src.read_bytes()
expected22 = "d103dce25851d89bd51cb736c14ae91f416927dedfc692a441f28115a3343029"
actual22 = hashlib.sha256(data).hexdigest()
if actual22 != expected22:
    raise SystemExit(f"Round22 source SHA mismatch: {actual22}")

s = data.decode()

def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f"anchor missing: {label}")
    s = s.replace(old, new, 1)

replace_once(
    "public class FibonacciHarmonicSniperUltimate : Robot",
    "public partial class FibonacciHarmonicSniperUltimate : Robot",
    "partial class"
)
replace_once(
    'Print("VERSION v0.21.0-btc-round22-capital-efficiency");',
    'Print("VERSION v0.23.0-btc-round26-core-refactor");',
    "version"
)
round22_print = '''            Print("BTC Round22 Capital Efficiency | H1 Buy={0:F2}% H1 Sell={1:F2}% M30 Buy={2:F2}% M30 Sell={3:F2}%", Round22H1BuyRiskPercent, Round22H1SellRiskPercent, Round22M30BuyRiskPercent, Round22M30SellRiskPercent);\n'''
replace_once(
    round22_print,
    round22_print + '''            Print("BTC Round26 Core Refactor | Signal/Quality/Regime/Risk/Execution layers enabled | economic logic frozen to Round22");\n''',
    "round26 startup log"
)
replace_once(
    "PatternMatch best = Round15FindM30Pattern(lastClosed);",
    "PatternMatch best = Round26SignalSelectM30(lastClosed);",
    "M30 signal routing"
)
replace_once(
    "bool confirmationPassed = best != null && Round15PassM30Confirmation(best, lastClosed);",
    "bool confirmationPassed = best != null && Round26QualityPassM30(best, lastClosed);",
    "M30 quality routing"
)
replace_once(
    "Round15ExecuteM30(best, lastClosed, round21Bypass);",
    "Round26ExecutionM30(best, lastClosed, round21Bypass);",
    "M30 execution routing"
)
replace_once(
    "PatternMatch best = FindBestPattern(pivots);",
    "PatternMatch best = Round26SignalSelectH1(pivots);",
    "H1 signal routing"
)
replace_once(
    "ExecutePatternTrade(best);",
    "Round26ExecutionH1(best);",
    "H1 execution routing"
)
replace_once(
    "double volume = Round22CalculateH1Volume(slPips, m.Direction);",
    "double volume = Round26RiskH1Volume(slPips, m.Direction);",
    "H1 risk routing"
)
replace_once(
    "double volume=Round21CalculateM30Volume(slPips, riskPercent);",
    "double volume=Round26RiskM30Volume(slPips, riskPercent);",
    "M30 risk routing"
)

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(s)

layers = {
"Round26.Signal.cs": r'''using System.Collections.Generic;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        // Signal layer: selection only. No sizing, execution, or risk decisions.
        private PatternMatch Round26SignalSelectH1(List<PivotPoint> pivots)
        {
            return FindBestPattern(pivots);
        }

        private PatternMatch Round26SignalSelectM30(int lastClosed)
        {
            return Round15FindM30Pattern(lastClosed);
        }
    }
}
''',
"Round26.Quality.cs": r'''namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        // Quality layer: confirmation only. Round26 intentionally preserves Round22 behavior.
        private bool Round26QualityPassM30(PatternMatch match, int lastClosed)
        {
            return Round15PassM30Confirmation(match, lastClosed);
        }
    }
}
''',
"Round26.Regime.cs": r'''using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        // Regime layer is observational in Round26. It must not veto or resize trades.
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
            return new Round26RegimeSnapshot
            {
                Direction = direction,
                H1TrendAligned = IsTrendAligned(direction),
                M30HealthAllowed = Round16H1HealthAllowsM30(),
                OwnOpenPositions = Round18OwnOpenPositions(),
                SpreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize
            };
        }
    }
}
''',
"Round26.Risk.cs": r'''using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        // Risk layer: exact pass-through to Round22 sizing in the parity release.
        private double Round26RiskH1Volume(double slPips, TradeType direction)
        {
            return Round22CalculateH1Volume(slPips, direction);
        }

        private double Round26RiskM30Volume(double slPips, double riskPercent)
        {
            return Round21CalculateM30Volume(slPips, riskPercent);
        }
    }
}
''',
"Round26.Execution.cs": r'''namespace cAlgo.Robots
{
    public partial class FibonacciHarmonicSniperUltimate
    {
        // Execution layer: Round26 captures regime context but does not act on it.
        private void Round26ExecutionH1(PatternMatch match)
        {
            Round26CaptureRegime(match.Direction);
            ExecutePatternTrade(match);
        }

        private void Round26ExecutionM30(PatternMatch match, int lastClosed, bool round21Bypass)
        {
            Round26CaptureRegime(match.Direction);
            Round15ExecuteM30(match, lastClosed, round21Bypass);
        }
    }
}
'''
}
for name, content in layers.items():
    (out.parent / name).write_text(content)

main_sha = hashlib.sha256(out.read_bytes()).hexdigest()
expected_main = "edff7234a3fa9bd300ee6bf618e8f376e54a9c399b2a33c6da5df0f3dded8afc"
if main_sha != expected_main:
    raise SystemExit(f"Round26 main SHA mismatch: {main_sha}")

print("Round26 main SHA:", main_sha)
for name in sorted(layers):
    p = out.parent / name
    print(name, hashlib.sha256(p.read_bytes()).hexdigest())
