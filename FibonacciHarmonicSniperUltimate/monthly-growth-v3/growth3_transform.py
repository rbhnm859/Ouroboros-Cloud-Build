from pathlib import Path
import subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: growth3_transform.py <store-main.cs> <growth3-main.cs>')

# The v3 workflow preserves the proven Growth2 generator at /tmp/growth2_transform.py.
# Generate the modular candidate first, then replace only the rejected alpha's signal/risk surface.
subprocess.run([sys.executable, '/tmp/growth2_transform.py', sys.argv[1], sys.argv[2]], check=True)
out = Path(sys.argv[2])
alpha = out.parent / 'Growth2.Alpha.cs'
main = out.read_text()
s = alpha.read_text()

def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit('Growth3 anchor missing: ' + label)
    s = s.replace(old, new, 1)

# Keep the old parameter names so the frozen Growth2 validation harness can run unchanged,
# but make the candidate identity explicit in logs/artifacts.
main = main.replace('BTC-Harmonic-Guard-Growth2-v2', 'BTC-Harmonic-Guard-Growth3-v3')

# Quality Recovery: require meaningful H4/H1 trend separation, not only EMA ordering.
rep('''            bool h4Bull = h4Close > h4Fast && h4Fast > h4Slow && h4Fast > h4FastPrev;\n            bool h4Bear = h4Close < h4Fast && h4Fast < h4Slow && h4Fast < h4FastPrev;''',
'''            double h4Sep = Math.Abs(h4Fast - h4Slow) / Math.Max(Symbol.PipSize, Math.Abs(h4Close));\n            bool h4Bull = h4Close > h4Fast && h4Fast > h4Slow && h4Fast > h4FastPrev && h4Sep >= 0.0020;\n            bool h4Bear = h4Close < h4Fast && h4Fast < h4Slow && h4Fast < h4FastPrev && h4Sep >= 0.0020;''', 'h4 quality')

rep('''            bool h1Bull = h1Close > h1E20 && h1E20 > h1E50 && h1E20 > h1E20Prev && h1E50 >= h1E50Prev;\n            bool h1Bear = h1Close < h1E20 && h1E20 < h1E50 && h1E20 < h1E20Prev && h1E50 <= h1E50Prev;''',
'''            double h1Sep = Math.Abs(h1E20 - h1E50) / Math.Max(Symbol.PipSize, Math.Abs(h1Close));\n            bool h1Bull = h1Close > h1E20 && h1E20 > h1E50 && h1E20 > h1E20Prev && h1E50 >= h1E50Prev && h1Sep >= 0.0010;\n            bool h1Bear = h1Close < h1E20 && h1E20 < h1E50 && h1E20 < h1E20Prev && h1E50 <= h1E50Prev && h1Sep >= 0.0010;''', 'h1 quality')

# Recovery candle must close with directional conviction and M30 trend must have real separation.
rep('''            double body = Math.Abs(close - open);\n            if (body < atr * Growth2BodyAtr) return false;\n            if (Math.Abs(close - e20) > atr * Growth2MaxExtensionAtr) return false;''',
'''            double body = Math.Abs(close - open);\n            double range = Math.Max(Symbol.PipSize, _barsM30.HighPrices[m30] - _barsM30.LowPrices[m30]);\n            double closeLocation = (close - _barsM30.LowPrices[m30]) / range;\n            double m30SepAtr = Math.Abs(e20 - e50) / atr;\n            if (body < atr * Growth2BodyAtr) return false;\n            if (Math.Abs(close - e20) > atr * Growth2MaxExtensionAtr) return false;\n            if (m30SepAtr < 0.12) return false;''', 'm30 quality')

# Replace one-bar breakout with a two-bar momentum recovery and rejection/close-location confirmation.
rep('''            TradeType dir;\n            if (h4Bull && h1Bull && close > open && close > e20 && e20 > e50 &&\n                close > _barsM30.HighPrices[m30-1] && pullbackLow >= e50 - atr * Growth2DeepPullbackAtr)\n                dir=TradeType.Buy;\n            else if (h4Bear && h1Bear && close < open && close < e20 && e20 < e50 &&\n                close < _barsM30.LowPrices[m30-1] && pullbackHigh <= e50 + atr * Growth2DeepPullbackAtr)\n                dir=TradeType.Sell;\n            else\n                return false;''',
'''            double recoveryHigh = Math.Max(_barsM30.HighPrices[m30-1], _barsM30.HighPrices[m30-2]);\n            double recoveryLow = Math.Min(_barsM30.LowPrices[m30-1], _barsM30.LowPrices[m30-2]);\n            TradeType dir;\n            if (h4Bull && h1Bull && close > open && close > e20 && e20 > e50 &&\n                close > recoveryHigh && closeLocation >= 0.68 &&\n                pullbackLow >= e50 - atr * Growth2DeepPullbackAtr)\n                dir=TradeType.Buy;\n            else if (h4Bear && h1Bear && close < open && close < e20 && e20 < e50 &&\n                close < recoveryLow && closeLocation <= 0.32 &&\n                pullbackHigh <= e50 + atr * Growth2DeepPullbackAtr)\n                dir=TradeType.Sell;\n            else\n                return false;''', 'momentum recovery')

# Do not manufacture improvement by increasing alpha risk. Cap the research lane at the prior low budget.
rep('''            double budget=Account.Equity*Growth2RiskPercent/100.0;''',
'''            double effectiveRiskPercent=Math.Min(Growth2RiskPercent,0.15);\n            double budget=Account.Equity*effectiveRiskPercent/100.0;''', 'risk cap')

s = s.replace('GROWTH2|CONTINUATION', 'GROWTH2|QUALITY_RECOVERY')
s = s.replace('[GROWTH2 OPEN]', '[GROWTH3 OPEN]').replace('[GROWTH2 ORDER FAIL]', '[GROWTH3 ORDER FAIL]')
alpha.write_text(s)
out.write_text(main)
print('Growth3 quality-recovery source generated')
