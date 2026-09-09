from pathlib import Path

src = Path('FibonacciHarmonicSniperUltimate/versions/v1.1.0-btc-store-round30-monthly-compound/round30_validation.sh')
out = Path('work_round30_v2.sh')
s = src.read_text()

needle = "python3 \"$V/round30_compound_transform.py\" work/store-src work/r30-src\n"
replacement = needle + "mv work/r30-src/BTC-Harmonic-Guard.cs work/r30-src/FibonacciHarmonicSniperUltimate.cs\n"
if needle not in s:
    raise SystemExit('transform anchor missing')
s = s.replace(needle, replacement, 1)

s = s.replace('work/r30-src/Round30.csproj', 'work/r30-src/FibonacciHarmonicSniperUltimate.csproj')
s = s.replace('r[\'balance\'][\'maxBalanceDrawdownPercent\']', 'r[\'equity\'][\'maxBalanceDrawdownPercent\']')
s = s.replace("if control3['trades']!=256", "if control3['trades']!=255")

pull = "docker pull ghcr.io/spotware/ctrader-console:5.9.11\n"
meta = pull + '''META=$(docker run --rm -v "$PWD/work:/work" ghcr.io/spotware/ctrader-console:5.9.11 metadata /work/build/BTC-Harmonic-Guard-Compound.algo)\necho "$META" > work/Round30-Metadata.json\necho "$META"\nif echo "$META" | grep -q '\"Type\": \"Indicator\"'; then\n  echo 'Round30 package is still detected as Indicator; refusing to backtest.' >&2\n  exit 31\nfi\nif ! echo "$META" | grep -q '\"Round30CompoundEnabled\"'; then\n  echo 'Round30 custom parameters missing from metadata.' >&2\n  exit 32\nfi\n'''
if pull not in s:
    raise SystemExit('docker pull anchor missing')
s = s.replace(pull, meta, 1)

# Harden the control-drift message to acknowledge the one historical risk-budget rejection.
s = s.replace("raise SystemExit(f'Control drift 3Y: {control3}')", "raise SystemExit(f'Hardened Store control drift 3Y: {control3}')")

out.write_text(s)
print(out)
