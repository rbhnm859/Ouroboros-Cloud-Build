from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

# Commercial integrity corrections for pattern definitions that were materially
# inconsistent with the documented structures. This patch intentionally does
# not broaden signal filters; it corrects geometry while other v28 changes
# recover frequency from valid candidates.

# Crab: defining completion is the 1.618 XA projection. Keep B/BC ranges but
# stop accepting 1.13-1.5 XA completions as Crab.
old = 'new PatternDef("Crab", PatternFamily.Reversal, 0.35, 0.62, R_618, 0.382, 0.886, R_618, R_224, R_3618, R_2618, R_113, R_1618, R_1618, 0.70, 0.90, 0.50, 0.95),'
new = 'new PatternDef("Crab", PatternFamily.Reversal, 0.35, 0.62, R_50, 0.382, 0.886, R_618, R_224, R_3618, R_2618, R_1618, R_1618, R_1618, 0.70, 0.90, 0.50, 0.95),'
if old not in s:
    raise SystemExit('legacy Crab definition missing')
s = s.replace(old, new, 1)

# Deep Gartley: B is still a 0.618 XA retracement; the deeper feature is the
# D/PRZ near 0.886 XA, with a 1.618-2.618 BC projection.
old = 'new PatternDef("Deep Gartley", PatternFamily.Reversal, 0.70, 0.85, R_786, 0.382, 0.886, R_618, R_1272, R_1618, R_1272, 0.95, 1.05, 1.0, 0.68, 0.75, 0.75, 1.0),'
new = 'new PatternDef("Deep Gartley", PatternFamily.Reversal, 0.588, 0.648, R_618, 0.382, 0.886, R_618, R_1618, R_2618, R_20, R_786, R_886, R_886, 0.68, 0.75, 0.75, 1.0),'
if old not in s:
    raise SystemExit('legacy Deep Gartley definition missing')
s = s.replace(old, new, 1)

# Release assertions.
if '"Crab", PatternFamily.Reversal' not in s or 'R_1618, R_1618, R_1618' not in s:
    raise SystemExit('Crab 1.618 XA integrity assertion failed')
if '"Deep Gartley", PatternFamily.Reversal, 0.588, 0.648, R_618' not in s:
    raise SystemExit('Deep Gartley B-point integrity assertion failed')

p.write_text(s, encoding='utf-8')
print('Applied v28 Crab and Deep Gartley pattern-integrity corrections')
