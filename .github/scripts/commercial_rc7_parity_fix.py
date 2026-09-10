from pathlib import Path
import subprocess
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: commercial_rc7_parity_fix.py <store-main.cs> <rc7-main.cs>')

# First generate the exact report-driven RC7B candidate.
subprocess.run([
    sys.executable,
    '.github/scripts/commercial_rc7_transform.py',
    sys.argv[1],
    sys.argv[2],
], check=True)

out = Path(sys.argv[2]).resolve()
base = out.parent
main = out.read_text()

# RC7B candidate must bypass the legacy blind H1 reservation, but frozen control
# must remain byte-for-behaviour compatible with the proven Round22 path.
old_tick = '''        protected override void OnTick()\n        {\n            CommercialTryExecuteDeferredM30();\n            Round15ProcessM30ClosedBar();'''
new_tick = '''        protected override void OnTick()\n        {\n            CommercialOnTickArbitration();\n            Round15ProcessM30ClosedBar();'''
if old_tick not in main:
    raise SystemExit('RC7B parity-fix OnTick anchor missing')
main = main.replace(old_tick, new_tick, 1)
out.write_text(main)

arb = base / 'Commercial.ArbitrationLedger.cs'
text = arb.read_text()
anchor = '''        private void CommercialLedger(string evt, string detail)\n        {\n            Print("[COMMERCIAL LEDGER] event={0} time={1:yyyy-MM-ddTHH:mm:ss} {2}", evt, Server.Time, detail ?? string.Empty);\n        }\n'''
insert = anchor + '''\n        private void CommercialOnTickArbitration()\n        {\n            // Frozen Round22 control path: preserve the legacy reservation exactly.\n            if (!Growth2Enabled)\n            {\n                Round21ReserveH1Lane();\n                return;\n            }\n\n            // RC7B candidate path: no blind reservation; use report-directed deferred arbitration.\n            CommercialTryExecuteDeferredM30();\n        }\n'''
if anchor not in text:
    raise SystemExit('RC7B parity-fix ledger anchor missing')
text = text.replace(anchor, insert, 1)
arb.write_text(text)

# Engineering invariants only; strategy policy/risk/alpha are untouched.
main = out.read_text()
on_tick = main[main.find('protected override void OnTick()'):main.find('protected override void OnStop()')]
if 'CommercialOnTickArbitration();' not in on_tick:
    raise SystemExit('RC7B parity-fix wrapper not active in OnTick')
if 'Round21ReserveH1Lane();' in on_tick:
    raise SystemExit('RC7B candidate OnTick still contains direct blind reservation')
ledger = arb.read_text()
for token in ('private void CommercialOnTickArbitration()', 'if (!Growth2Enabled)', 'Round21ReserveH1Lane();', 'CommercialTryExecuteDeferredM30();'):
    if token not in ledger:
        raise SystemExit('RC7B parity-fix control isolation invariant failed: ' + token)

compile_cs = [p for p in base.glob('*.cs') if p.name != 'BTC-Harmonic-Guard.cs']
direct_total = sum(p.read_text().count('ExecuteMarketOrder(') for p in compile_cs)
central = (base / 'Commercial.IntentExecution.cs').read_text().count('ExecuteMarketOrder(')
if direct_total != 1 or central != 1 or out.read_text().count('ExecuteMarketOrder(') != 0:
    raise SystemExit(f'RC7B parity-fix single execution boundary failed direct={direct_total} central={central}')

print('Commercial RC7B parity isolation applied: Round22 control reservation restored; candidate arbitration unchanged')
