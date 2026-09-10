from pathlib import Path
import json
import subprocess
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: commercial_rc4_parity_fix.py <store-main.cs> <rc4-main.cs>')

# RC7 compatibility: the legacy Growth3 generator expects the frozen original
# Growth2 transform at /tmp/growth2_transform.py. The workflow may replace the
# working-tree transform before this chain starts, so recover the committed
# original directly from the current Git object without modifying history.
frozen_growth2 = Path('/tmp/growth2_transform.py')
if not frozen_growth2.exists():
    repo_path = 'FibonacciHarmonicSniperUltimate/monthly-growth-v2/growth2_transform.py'
    r = subprocess.run(['git', 'show', 'HEAD:' + repo_path], check=True, capture_output=True, text=True)
    frozen_growth2.write_text(r.stdout)
    print('RC7 transform-chain recovery: restored frozen Growth2 generator from HEAD')

# Generate the RC4 candidate first, then isolate every candidate-only behavior
# behind Growth2Enabled so the frozen disabled control remains exact Round22 parity.
subprocess.run([sys.executable, '.github/scripts/commercial_rc4_transform.py', sys.argv[1], sys.argv[2]], check=True)

out = Path(sys.argv[2]).resolve()
base = out.parent
main = out.read_text()

old = '                    if (!IsPatternSelected(def, M30Patterns)) continue;'
new = '''                    if (!Growth2Enabled)\n                    {\n                        if (!def.Name.Equals("Reciprocal ABCD", StringComparison.OrdinalIgnoreCase)) continue;\n                    }\n                    else if (!IsPatternSelected(def, M30Patterns)) continue;'''
if old not in main:
    raise SystemExit('RC4 parity-fix M30 selector anchor missing')
main = main.replace(old, new, 1)
out.write_text(main)

commercial = base / 'Commercial.IntentExecution.cs'
c = commercial.read_text()
old = '            double factor=CommercialRiskGovernorFactor(intent);'
new = '            double factor=Growth2Enabled ? CommercialRiskGovernorFactor(intent) : 1.0;'
if old not in c:
    raise SystemExit('RC4 parity-fix governor anchor missing')
c = c.replace(old, new, 1)
commercial.write_text(c)

# Invariants: control mode cannot expand the M30 pattern universe and cannot
# apply candidate risk scaling. Candidate mode retains both behaviors.
if 'if (!Growth2Enabled)' not in out.read_text():
    raise SystemExit('RC4 parity-fix control selector guard missing')
if 'Growth2Enabled ? CommercialRiskGovernorFactor(intent) : 1.0' not in commercial.read_text():
    raise SystemExit('RC4 parity-fix governor bypass missing')

src = Path(sys.argv[1]).resolve()
cs = [p for p in base.glob('*.cs') if p.resolve() != src]
direct = sum(p.read_text().count('ExecuteMarketOrder(') for p in cs)
central = commercial.read_text().count('ExecuteMarketOrder(')
if direct != 1 or central != 1 or out.read_text().count('ExecuteMarketOrder(') != 0:
    raise SystemExit(f'RC4 parity-fix structural invariant failed direct={direct} central={central}')

# RC7 is a branch-local post-transform. It changes portfolio arbitration only;
# RC6 continues afterward and remains responsible for the single execution boundary.
rc7_policy = Path('.github/policies/commercial_rc7_policy.json')
rc7_post = Path('.github/scripts/commercial_rc7_post_transform.py')
if rc7_policy.exists() and rc7_post.exists():
    p = json.loads(rc7_policy.read_text())
    if p.get('policy_version') == 'RC7A-2026-09-10':
        subprocess.run([sys.executable, str(rc7_post), str(out)], check=True)

print('Commercial RC4 parity isolation applied: frozen control exact path restored; candidate selector/governor scoped to Growth2Enabled')
