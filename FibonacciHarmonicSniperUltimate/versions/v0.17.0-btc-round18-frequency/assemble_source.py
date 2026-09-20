from pathlib import Path

root = Path(__file__).resolve().parent
parts = sorted((root / "source-parts").glob("part-*.cs.part"))
if len(parts) != 6:
    raise SystemExit(f"Expected 6 source parts, found {len(parts)}")

out = root / "FibonacciHarmonicSniperUltimate.cs"
out.write_text("".join(p.read_text() for p in parts))
print(f"Assembled {out} ({out.stat().st_size} bytes) from {len(parts)} parts")
