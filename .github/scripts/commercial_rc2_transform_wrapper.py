from pathlib import Path
import re, subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: commercial_rc2_transform_wrapper.py <store-main.cs> <rc2-main.cs>')

# Reuse the validated RC1 structural transform (centralized risk/execution/safety)
# and then remove only the candidate alpha vetoes that damaged proven H1/M30 edge.
base_wrapper = '.github/scripts/commercial_rc1_transform_wrapper.py'
proc = subprocess.run([sys.executable, base_wrapper, sys.argv[1], sys.argv[2]], text=True, capture_output=True)
if proc.stdout:
    print(proc.stdout, end='')
if proc.stderr:
    print(proc.stderr, end='', file=sys.stderr)
if proc.returncode != 0:
    raise SystemExit(proc.returncode)

out = Path(sys.argv[2]).resolve()
base = out.parent
portfolio = base / 'Commercial.Portfolio.cs'
arch = base / 'Growth3.Architecture.cs'
if not out.exists() or not portfolio.exists() or not arch.exists():
    raise SystemExit('RC2 required generated files missing')

# Version identity only; do not alter frozen windows/risk caps.
main = out.read_text()
main = main.replace('BTC-Harmonic-Guard-Commercial-RC1', 'BTC-Harmonic-Guard-Commercial-RC2')
out.write_text(main)

# Portfolio is an arbitration/safety layer, not an alpha predictor.
# H1 and M30 retain their own validated signal logic. We deliberately remove:
#   - H4/H1 EMA/ATR regime vetoes for H1/M30
#   - 3-loss / 36h directional health veto
# Growth3 Quality Recovery is disabled because independent attribution was negative.
px = portfolio.read_text()
pattern = re.compile(
    r'        private bool CommercialPortfolioAllows\(string lane, TradeType direction, double quality\)\n'
    r'        \{.*?\n        \}\n\n'
    r'        private bool CommercialDirectionalHealthAllows',
    re.S,
)
replacement = '''        private bool CommercialPortfolioAllows(string lane, TradeType direction, double quality)\n        {\n            // Frozen baseline control must remain exact Round22 parity.\n            if (!Growth2Enabled) return true;\n\n            // Commercial RC2: portfolio layer enforces execution eligibility and\n            // single-position arbitration only. It must not re-predict alpha quality.\n            if (!StoreCanExecute() || Round18OwnOpenPositions()>=1) return false;\n\n            // Quality Recovery had negative standalone attribution in both 3Y and\n            // Recent windows; disable it instead of letting a negative lane consume\n            // the single-position slot and displace proven H1/M30 opportunities.\n            if (lane=="GROWTH3") return false;\n\n            return lane=="H1" || lane=="M30";\n        }\n\n        private bool CommercialDirectionalHealthAllows'''
px2, n = pattern.subn(replacement, px, count=1)
if n != 1:
    raise SystemExit('RC2 portfolio function anchor missing')
portfolio.write_text(px2)

# Defense in depth: even if the alpha emits an intent, candidate mode cannot submit it.
a = arch.read_text()
old = '            if (intent==null || !TradingEnabled || !StoreCanExecute()) return false;'
new = '            if (intent==null || Growth2Enabled || !TradingEnabled || !StoreCanExecute()) return false;'
if old not in a:
    raise SystemExit('RC2 Growth3 disable anchor missing')
arch.write_text(a.replace(old, new, 1))

# Invariants: exactly one direct market order call in the final generated project,
# and it remains centralized in Commercial.Portfolio.cs.
src = Path(sys.argv[1]).resolve()
counts=[]
for p in base.glob('*.cs'):
    if p.resolve() == src:
        continue
    counts.append((p.name,p.read_text().count('ExecuteMarketOrder(')))
direct=sum(v for _,v in counts)
central=portfolio.read_text().count('ExecuteMarketOrder(')
if direct != 1 or central != 1:
    raise SystemExit('RC2 structural invariant failed direct=%d central=%d counts=%r' % (direct,central,counts))
if 'if (lane=="GROWTH3") return false;' not in portfolio.read_text():
    raise SystemExit('RC2 Growth3 portfolio disable missing')
if 'Growth2Enabled || !TradingEnabled' not in arch.read_text():
    raise SystemExit('RC2 Growth3 submit disable missing')
print('Commercial RC2 generated: H1/M30 edge preserved; Growth3 alpha disabled; single execution boundary verified')
# RC2 validation trigger marker: edge-preserve-v1
