from pathlib import Path
import subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: growth32_transform.py <store-main.cs> <growth32-main.cs>')

# Build the validated v3.1 architecture first, then apply only explicit v3.2 candidate gates.
subprocess.run([sys.executable, 'FibonacciHarmonicSniperUltimate/monthly-growth-v3/growth3_transform.py', sys.argv[1], sys.argv[2]], check=True)
out = Path(sys.argv[2])
main = out.read_text()
arch = out.parent / 'Growth3.Architecture.cs'
a = arch.read_text()

main = main.replace('BTC-Harmonic-Guard-Growth3-v3.1', 'BTC-Harmonic-Guard-Growth3-v3.2')

# Y2 attribution showed the H1 lane as the dominant loss source. Add a long-term regime
# veto before H1 sizing/execution. This does not resize risk and does not touch M30/Fib logic.
anchor = '''        private void ExecutePatternTrade(PatternMatch m)\n        {\n            Round10Count("execute_attempt", m.Direction);'''
replacement = '''        private void ExecutePatternTrade(PatternMatch m)\n        {\n            Round10Count("execute_attempt", m.Direction);\n            if (!Growth32H1RegimeAllows(m.Direction))\n            {\n                Reject("growth32_h1_regime_veto");\n                return;\n            }'''
if anchor not in main:
    raise SystemExit('Growth32 anchor missing: ExecutePatternTrade')
main = main.replace(anchor, replacement, 1)

# Quarantine weak continuation intents: v3.1 alpha attribution was PF < 1 in both 3Y and recent.
# Raise only the quality threshold; confidence never increases position size.
a = a.replace('intent.Confidence<0.45', 'intent.Confidence<0.62')

insert = r'''
        private bool Growth32H1RegimeAllows(TradeType direction)
        {
            if (_g2H4Ema50 == null || _g2H4Ema200 == null || _g2H1Ema20 == null || _g2H1Ema50 == null)
                return false;
            int h4 = _barsH4.Count - 2;
            int h1 = Bars.Count - 2;
            if (h4 < 202 || h1 < 52) return false;

            double h4Close = _barsH4.ClosePrices[h4];
            double h4Fast = _g2H4Ema50.Result[h4];
            double h4Slow = _g2H4Ema200.Result[h4];
            double h4FastPrev = _g2H4Ema50.Result[h4 - 2];
            double h1Close = Bars.ClosePrices[h1];
            double h1Fast = _g2H1Ema20.Result[h1];
            double h1Slow = _g2H1Ema50.Result[h1];

            if (direction == TradeType.Buy)
                return h4Close > h4Slow && h4Fast > h4Slow && h4Fast >= h4FastPrev && h1Close > h1Fast && h1Fast > h1Slow;
            return h4Close < h4Slow && h4Fast < h4Slow && h4Fast <= h4FastPrev && h1Close < h1Fast && h1Fast < h1Slow;
        }
'''
needle = '    }\n}\n'
pos = a.rfind(needle)
if pos < 0:
    raise SystemExit('Growth32 anchor missing: architecture class close')
a = a[:pos] + insert + a[pos:]

out.write_text(main)
arch.write_text(a)
print('Growth3 v3.2 weak-regime repair generated')
