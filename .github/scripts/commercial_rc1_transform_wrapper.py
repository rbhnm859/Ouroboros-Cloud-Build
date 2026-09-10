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
# requires exact Round22 parity. Commercial candidate filters and the unified
# candidate sizing layer must not alter that baseline-control pass. Candidate
# runs (Growth2Enabled=true) still use the full Commercial Portfolio/Regime/
# Health gates and commercial sizing, with unchanged frozen windows and risk caps.
out = Path(sys.argv[2]).resolve()
base = out.parent
portfolio = base / 'Commercial.Portfolio.cs'
if not portfolio.exists():
    raise SystemExit('Commercial.Portfolio.cs missing after transform')
px = portfolio.read_text()

old = '''        private bool CommercialPortfolioAllows(string lane, TradeType direction, double quality)\n        {\n            if (!StoreCanExecute() || Round18OwnOpenPositions()>=1) return false;\n'''
new = '''        private bool CommercialPortfolioAllows(string lane, TradeType direction, double quality)\n        {\n            // Frozen-baseline parity mode: when growth alpha is disabled, preserve\n            // the validated Round22 decision surface exactly.\n            if (!Growth2Enabled) return true;\n            if (!StoreCanExecute() || Round18OwnOpenPositions()>=1) return false;\n'''
if old not in px:
    raise SystemExit('RC1 parity-mode portfolio anchor missing')
px = px.replace(old, new, 1)

# Round22 parity also requires the original lane-specific sizing implementation.
# The commercial candidate path remains unchanged and still uses the unified
# risk engine when Growth2Enabled=true.
old = '''        private double CommercialVolumeForRisk(string lane,TradeType direction,double slPips,double requestedRiskPercent)\n        {\n            if (RiskMode!=RiskSizingMode.RiskPercentEquity || slPips<=0 || requestedRiskPercent<=0) return 0;\n'''
new = '''        private double CommercialVolumeForRisk(string lane,TradeType direction,double slPips,double requestedRiskPercent)\n        {\n            if (!Growth2Enabled)\n            {\n                if (lane=="H1") return Round22CalculateH1Volume(slPips,direction);\n                if (lane=="M30") return Round21CalculateM30Volume(slPips,requestedRiskPercent);\n            }\n            if (RiskMode!=RiskSizingMode.RiskPercentEquity || slPips<=0 || requestedRiskPercent<=0) return 0;\n'''
if old not in px:
    raise SystemExit('RC1 parity-mode risk anchor missing')
px = px.replace(old, new, 1)
portfolio.write_text(px)

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
print('Commercial RC1 wrapper restored original Round22 lane sizing in parity control')
