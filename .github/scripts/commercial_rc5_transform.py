from pathlib import Path
import subprocess, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: commercial_rc5_transform.py <store-main.cs> <rc5-main.cs>')

# RC5 is a single evidence-based change on top of validated RC4:
# keep H1 and Reciprocal-ABCD M30 live, keep centralized commercial risk/execution,
# but quarantine the newly unlocked M30 ABCD satellite after it showed negative
# standalone attribution in both 3Y and Recent validation. Signals remain visible
# as shadow telemetry and cannot consume the single live position.
subprocess.run([sys.executable, '.github/scripts/commercial_rc4_transform.py', sys.argv[1], sys.argv[2]], check=True)

out = Path(sys.argv[2]).resolve()
base = out.parent
main = out.read_text().replace('BTC-Harmonic-Guard-Commercial-RC4', 'BTC-Harmonic-Guard-Commercial-RC5')

anchor = '''        private void Round15ExecuteM30(PatternMatch m, int lastClosed, bool round21Bypass)\n        {\n            // Re-check position immediately before market order; both engines share the same label/account.'''
replacement = '''        private void Round15ExecuteM30(PatternMatch m, int lastClosed, bool round21Bypass)\n        {\n            // RC5: ABCD remains observable but is quarantined from live execution.\n            // RC4 evidence: 3Y 137 trades / net -33.58 / PF 0.9433;\n            // Recent 50 trades / net -69.93 / PF 0.7061.\n            if (Growth2Enabled && m.Definition.Name.Equals("ABCD", StringComparison.OrdinalIgnoreCase))\n            {\n                Print("[M30 ABCD SHADOW] dir={0} score={1:F1}% bypass={2} signal={3}",\n                    m.Direction,m.Score,round21Bypass,m.SignalKey);\n                return;\n            }\n\n            // Re-check position immediately before market order; both engines share the same label/account.'''
if anchor not in main:
    raise SystemExit('RC5 M30 execution anchor missing')
main = main.replace(anchor, replacement, 1)
out.write_text(main)

# Preserve RC4 structural invariants and explicitly prove quarantine is candidate-only,
# so the frozen Growth2-disabled Round22 parity path remains untouched.
commercial = base / 'Commercial.IntentExecution.cs'
arch = base / 'Growth3.Architecture.cs'
src = Path(sys.argv[1]).resolve()
counts=[]
for p in base.glob('*.cs'):
    if p.resolve()==src:
        continue
    counts.append((p.name,p.read_text().count('ExecuteMarketOrder(')))
direct=sum(v for _,v in counts)
central=commercial.read_text().count('ExecuteMarketOrder(')
text=out.read_text()
if direct!=1 or central!=1 or text.count('ExecuteMarketOrder(')!=0:
    raise SystemExit('RC5 execution invariant failed direct=%d central=%d files=%r'%(direct,central,counts))
if 'Growth2Enabled && m.Definition.Name.Equals("ABCD"' not in text or '[M30 ABCD SHADOW]' not in text:
    raise SystemExit('RC5 ABCD quarantine missing')
if '[GROWTH3 SHADOW]' not in arch.read_text():
    raise SystemExit('RC5 Growth3 shadow isolation missing')
print('Commercial RC5 generated: RC4 architecture preserved; M30 ABCD quarantined candidate-only; direct orders=1')

# validation-trigger: 2026-09-10 RC5
