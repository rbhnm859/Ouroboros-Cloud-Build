#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
src=Path('FibonacciHarmonicSniperUltimate/monthly-growth/growth_validation.sh').read_text()
anchor="python3 FibonacciHarmonicSniperUltimate/store-v1/store_v1_transform.py work/store-src/BTC-Harmonic-Guard-Control.cs work/store-src/BTC-Harmonic-Guard.cs\n"
if anchor not in src: raise SystemExit('Store transform anchor missing')
src=src.replace(anchor,anchor+"python3 FibonacciHarmonicSniperUltimate/store-v1/store_v1_keyfix.py work/store-src\n",1)
src=src.replace("float(r['balance']['maxBalanceDrawdownPercent'])","float(r['equity']['maxBalanceDrawdownPercent'])")
# Runtime persistence exceptions invalidate the experiment before strategy scoring.
needle="run_case responsive-3y   '08/09/2023 00:00' '08/09/2026 00:00' 65 0 0.35 1.70 1.40 5 0.12\n"
if needle not in src: raise SystemExit('3Y screen anchor missing')
src=src.replace(needle,needle+"if grep -R '\\[STORE EXCEPTION\\]\\|\\[STORE PERSIST FAIL\\]' work/conservative-3y/report.log work/balanced-3y/report.log work/responsive-3y/report.log; then echo 'Store persistence/runtime exception detected'; exit 1; fi\n",1)
Path('/tmp/growth_validation_v2.sh').write_text(src)
PY
chmod +x /tmp/growth_validation_v2.sh
exec /tmp/growth_validation_v2.sh
