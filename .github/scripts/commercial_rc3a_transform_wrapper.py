from pathlib import Path
import re, subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: commercial_rc3a_transform_wrapper.py <store-main.cs> <rc3a-main.cs>')

# Start from the already validated Commercial RC1 structural refactor so H1, M30
# and Growth3 share one direct ExecuteMarketOrder boundary. RC3A then removes all
# policy changes that altered Growth3 v3.1 behavior. This stage is architecture
# parity only: no alpha tuning, no risk increase, no window/gate changes.
base_wrapper='.github/scripts/commercial_rc1_transform_wrapper.py'
proc=subprocess.run([sys.executable,base_wrapper,sys.argv[1],sys.argv[2]],text=True,capture_output=True)
if proc.stdout: print(proc.stdout,end='')
if proc.stderr: print(proc.stderr,end='',file=sys.stderr)
if proc.returncode!=0: raise SystemExit(proc.returncode)

out=Path(sys.argv[2]).resolve(); base=out.parent
portfolio=base/'Commercial.Portfolio.cs'; arch=base/'Growth3.Architecture.cs'
if not out.exists() or not portfolio.exists() or not arch.exists():
    raise SystemExit('RC3A generated files missing')

main=out.read_text().replace('BTC-Harmonic-Guard-Commercial-RC1','BTC-Harmonic-Guard-Commercial-RC3A')
out.write_text(main)

px=portfolio.read_text()
# Portfolio arbiter is deliberately policy-neutral in RC3A. It only preserves the
# existing single-position / Store execution boundary and does not re-predict alpha.
pat=re.compile(r'        private bool CommercialPortfolioAllows\(string lane, TradeType direction, double quality\)\n        \{.*?\n        \}\n\n        private bool CommercialDirectionalHealthAllows',re.S)
rep='''        private bool CommercialPortfolioAllows(string lane, TradeType direction, double quality)\n        {\n            if (!Growth2Enabled) return true;\n            if (!StoreCanExecute() || Round18OwnOpenPositions()>=1) return false;\n            return lane=="H1" || lane=="M30" || lane=="GROWTH3";\n        }\n\n        private bool CommercialDirectionalHealthAllows'''
px,n=pat.subn(rep,px,count=1)
if n!=1: raise SystemExit('RC3A portfolio anchor missing')

# Restore the exact proven lane-specific sizing functions in candidate mode too.
old='''        private double CommercialVolumeForRisk(string lane,TradeType direction,double slPips,double requestedRiskPercent)\n        {\n            if (!Growth2Enabled)\n            {\n                if (lane=="H1") return Round22CalculateH1Volume(slPips,direction);\n                if (lane=="M30") return Round21CalculateM30Volume(slPips,requestedRiskPercent);\n            }\n            if (RiskMode!=RiskSizingMode.RiskPercentEquity || slPips<=0 || requestedRiskPercent<=0) return 0;\n'''
new='''        private double CommercialVolumeForRisk(string lane,TradeType direction,double slPips,double requestedRiskPercent)\n        {\n            if (lane=="H1") return Round22CalculateH1Volume(slPips,direction);\n            if (lane=="M30") return Round21CalculateM30Volume(slPips,requestedRiskPercent);\n            if (RiskMode!=RiskSizingMode.RiskPercentEquity || slPips<=0 || requestedRiskPercent<=0) return 0;\n'''
if old not in px: raise SystemExit('RC3A risk anchor missing')
px=px.replace(old,new,1)
portfolio.write_text(px)

# Restore Growth3 v3.1 participation and original confidence threshold. The lane
# still routes through the single commercial execution boundary.
a=arch.read_text()
old='if (intent==null || !TradingEnabled || !StoreCanExecute()) return false;'
# Depending on parent wrapper state, RC2-only disable must not survive here.
a=a.replace('if (intent==null || Growth2Enabled || !TradingEnabled || !StoreCanExecute()) return false;',old)
a=a.replace('intent.Confidence<0.62','intent.Confidence<0.45')
if old not in a or 'intent.Confidence<0.45' not in a:
    raise SystemExit('RC3A Growth3 parity anchors missing')
arch.write_text(a)

# Exactly one direct market-order call is allowed in the generated compile set.
src=Path(sys.argv[1]).resolve(); counts=[]
for p in base.glob('*.cs'):
    if p.resolve()==src: continue
    counts.append((p.name,p.read_text().count('ExecuteMarketOrder(')))
direct=sum(v for _,v in counts); central=portfolio.read_text().count('ExecuteMarketOrder(')
if direct!=1 or central!=1:
    raise SystemExit('RC3A structural invariant failed direct=%d central=%d counts=%r'%(direct,central,counts))
print('Commercial RC3A generated: Growth3 v3.1 policy restored; one centralized execution boundary verified')
