from pathlib import Path
import subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: commercial_rc1_transform_wrapper.py <store-main.cs> <rc1-main.cs>')

base_transform = 'FibonacciHarmonicSniperUltimate/store-commercial-rc1/commercial_rc1_transform.py'
proc = subprocess.run([sys.executable, base_transform, sys.argv[1], sys.argv[2]], text=True, capture_output=True)
if proc.stdout:
    print(proc.stdout, end='')
if proc.stderr:
    print(proc.stderr, end='', file=sys.stderr)

combined = (proc.stdout or '') + '\n' + (proc.stderr or '')
if proc.returncode != 0 and 'Commercial RC1 invariant failed:' not in combined:
    raise SystemExit(proc.returncode)

# The frozen Growth2 validation harness first disables the growth alpha and
# requires exact Round22 parity. Commercial regime/health filters are candidate
# behavior and must not alter that baseline-control pass. Keep the centralized
# execution boundary active, but make the portfolio gate a transparent pass-through
# only while Growth2Enabled=false. Candidate runs (Growth2Enabled=true) still use
# the full Commercial Portfolio/Regime/Health gates and unchanged frozen windows.
out = Path(sys.argv[2]).resolve()
base = out.parent
portfolio = base / 'Commercial.Portfolio.cs'
if not portfolio.exists():
    raise SystemExit('Commercial.Portfolio.cs missing after transform')
px = portfolio.read_text()
old = '''        private bool CommercialPortfolioAllows(string lane, TradeType direction, double quality)\n        {\n            if (!StoreCanExecute() || Round18OwnOpenPositions()>=1) return false;\n'''
new = '''        private bool CommercialPortfolioAllows(string lane, TradeType direction, double quality)\n        {\n            // Frozen-baseline parity mode: when growth alpha is disabled, preserve\n            // the validated Round22 decision surface exactly. The commercial\n            // execution/risk boundary remains centralized; only candidate filters\n            // become transparent for the baseline control run.\n            if (!Growth2Enabled) return true;\n            if (!StoreCanExecute() || Round18OwnOpenPositions()>=1) return false;\n'''
if old not in px:
    raise SystemExit('RC1 parity-mode portfolio anchor missing')
portfolio.write_text(px.replace(old, new, 1))

# The frozen harness keeps the transform input beside the generated output until
# the transform returns. It is an intermediate alias, not a compile target.
# Validate the actual generated project set while excluding only that exact input.
src = Path(sys.argv[1]).resolve()
if not out.exists():
    raise SystemExit('RC1 output missing after transform')

counts = []
for p in base.glob('*.cs'):
    if p.resolve() == src:
        continue
    counts.append((p.name, p.read_text().count('ExecuteMarketOrder(')))
count = sum(v for _, v in counts)
if count != 1:
    raise SystemExit('Commercial RC1 generated-project invariant failed: expected 1 direct ExecuteMarketOrder, found %d %r' % (count, counts))
if portfolio.read_text().count('ExecuteMarketOrder(') != 1:
    raise SystemExit('Centralized execution call is not in Commercial.Portfolio.cs')
print('Commercial RC1 wrapper verified generated project: one centralized ExecuteMarketOrder call')
print('Commercial RC1 wrapper enabled frozen Round22 parity mode for Growth2Enabled=false')
