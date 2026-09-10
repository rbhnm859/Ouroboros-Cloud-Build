from pathlib import Path
import subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: commercial_rc2_transform_wrapper.py <store-main.cs> <rc2-main.cs>')

base_transform = 'FibonacciHarmonicSniperUltimate/store-commercial-rc1/commercial_rc1_transform.py'
proc = subprocess.run([sys.executable, base_transform, sys.argv[1], sys.argv[2]], text=True, capture_output=True)
if proc.stdout:
    print(proc.stdout, end='')
if proc.stderr:
    print(proc.stderr, end='', file=sys.stderr)
combined = (proc.stdout or '') + '\n' + (proc.stderr or '')
if proc.returncode != 0 and 'Commercial RC1 invariant failed:' not in combined:
    raise SystemExit(proc.returncode)

out = Path(sys.argv[2]).resolve()
base = out.parent
portfolio = base / 'Commercial.Portfolio.cs'
if not portfolio.exists():
    raise SystemExit('Commercial.Portfolio.cs missing after transform')
px = portfolio.read_text()

# RC2 is deliberately subtractive. The frozen Round22 control must remain exact.
# In candidate mode, portfolio/risk/execution/safety stay centralized, but the
# portfolio layer no longer second-guesses the validated H1/M30 pattern alpha
# with generic EMA/ATR regime or 3-loss/36h health vetoes. The empirically
# negative Growth3 recovery lane is disabled rather than tuned or risk-increased.
old = '''        private bool CommercialPortfolioAllows(string lane, TradeType direction, double quality)\n        {\n            if (!StoreCanExecute() || Round18OwnOpenPositions()>=1) return false;\n'''
new = '''        private bool CommercialPortfolioAllows(string lane, TradeType direction, double quality)\n        {\n            // Frozen baseline: preserve the Round22 decision surface exactly.\n            if (!Growth2Enabled) return true;\n            if (!StoreCanExecute() || Round18OwnOpenPositions()>=1) return false;\n\n            // RC2 attribution-driven subtraction:\n            // - H1/M30 retain their own validated pattern/quality logic.\n            // - Growth3 recovery alpha is disabled because both 3Y and Recent\n            //   attribution were negative in RC1/v3.1 evidence.\n            if (lane=="GROWTH3") return false;\n            if (lane=="H1" || lane=="M30") return true;\n'''
if old not in px:
    raise SystemExit('RC2 portfolio anchor missing')
px = px.replace(old, new, 1)

# Preserve exact Round22 lane-specific sizing in frozen control only. Candidate
# sizing remains on the centralized commercial risk engine with the same caps.
old = '''        private double CommercialVolumeForRisk(string lane,TradeType direction,double slPips,double requestedRiskPercent)\n        {\n            if (RiskMode!=RiskSizingMode.RiskPercentEquity || slPips<=0 || requestedRiskPercent<=0) return 0;\n'''
new = '''        private double CommercialVolumeForRisk(string lane,TradeType direction,double slPips,double requestedRiskPercent)\n        {\n            if (!Growth2Enabled)\n            {\n                if (lane=="H1") return Round22CalculateH1Volume(slPips,direction);\n                if (lane=="M30") return Round21CalculateM30Volume(slPips,requestedRiskPercent);\n            }\n            if (RiskMode!=RiskSizingMode.RiskPercentEquity || slPips<=0 || requestedRiskPercent<=0) return 0;\n'''
if old not in px:
    raise SystemExit('RC2 parity-mode risk anchor missing')
px = px.replace(old, new, 1)
portfolio.write_text(px)

src = Path(sys.argv[1]).resolve()
if not out.exists():
    raise SystemExit('RC2 output missing after transform')
counts=[]
for p in base.glob('*.cs'):
    if p.resolve() == src:
        continue
    counts.append((p.name,p.read_text().count('ExecuteMarketOrder(')))
count=sum(v for _,v in counts)
if count != 1:
    raise SystemExit('Commercial RC2 generated-project invariant failed: expected 1 direct ExecuteMarketOrder, found %d %r' % (count,counts))
if portfolio.read_text().count('ExecuteMarketOrder(') != 1:
    raise SystemExit('Centralized execution call is not in Commercial.Portfolio.cs')
print('Commercial RC2 wrapper verified generated project: one centralized ExecuteMarketOrder call')
print('Commercial RC2 preserves frozen Round22 parity when Growth2Enabled=false')
print('Commercial RC2 removed H1/M30 secondary regime-health vetoes and disabled negative Growth3 lane')
