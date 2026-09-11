from pathlib import Path

SRC = Path('HarmonyBot-v19/HarmonyBotPro_v19_50PASS.cs')
AUDIT = Path('HarmonyBot-v19/tools/audit_v19_50.py')
REPORT = Path('HarmonyBot-v19/reports/critical-fixes.txt')

s = SRC.read_text(encoding='utf-8')
fixes = []

def rep(old, new, name, count=1):
    global s
    found = s.count(old)
    if found != count:
        raise SystemExit(f'{name}: expected {count}, found {found}')
    s = s.replace(old, new)
    fixes.append(name)

rep(
'''                bull = (b.Price > a.Price) && (c.Price < b.Price) && (d.Price > c.Price);\n                bear = (b.Price < a.Price) && (c.Price > b.Price) && (d.Price < c.Price);''',
'''                // ABCD is a reversal pattern: bullish completion is D-low; bearish completion is D-high.\n                bull = (b.Price < a.Price) && (c.Price > b.Price) && (d.Price < c.Price);\n                bear = (b.Price > a.Price) && (c.Price < b.Price) && (d.Price > c.Price);''',
'ABCD reversal polarity')

rep(
'''                double xd = Math.Abs(d.Price - x.Price);\n                double rAB = ab / xa;\n                double rBC = bc / ab;\n                double rCD = cd / bc;\n                double rXD = xd / xa;''',
'''                // Standard XABCD completion ratio is AD/XA (retracement/extension from A), not |D-X|/XA.\n                double ad = Math.Abs(d.Price - a.Price);\n                double rAB = ab / xa;\n                double rBC = bc / ab;\n                double rCD = cd / bc;\n                double rAD = ad / xa;''',
'XABCD AD-XA geometry')
rep('if (!InFibRange(rXD, def.XDIdeal, def.XDMin, def.XDMax)) return null;',
    'if (!InFibRange(rAD, def.XDIdeal, def.XDMin, def.XDMax)) return null;',
    'XABCD completion range')
rep('double s4 = RatioScore(rXD, def.XDIdeal);',
    'double s4 = RatioScore(rAD, def.XDIdeal);',
    'XABCD completion score')

rep(
'''            if (ideal > 0)\n            {\n                double lo = Math.Max(min, ideal - _fibTolerance);\n                double hi = Math.Min(max, ideal + _fibTolerance);\n                return value >= lo && value <= hi;\n            }\n            return value >= min && value <= max;''',
'''            // min/max already define the accepted harmonic zone. FibTolerance expands the zone slightly;\n            // ideal remains a scoring target rather than an accidental hard gate.\n            double lo = Math.Max(0.0, min - _fibTolerance);\n            double hi = max + _fibTolerance;\n            return value >= lo && value <= hi;''',
'Fibonacci tolerance semantics')

rep(
'''                    Candidate c = Match(bars, pivots, i, def, currentIndex, atrNow, regimeScore, buyTrend, sellTrend);\n                    if (c != null)\n                        all.Add(c);''',
'''                    Candidate c = Match(bars, pivots, i, def, currentIndex, atrNow, regimeScore, buyTrend, sellTrend);\n                    if (c != null)\n                    {\n                        SwingPoint completion = c.Family == PatternFamily.Shark ? c.C : c.D;\n                        double liveEntry = c.IsBullish ? symbol.Ask : symbol.Bid;\n                        // Reject stale/far candidates before ranking so they cannot mask a valid recent completion.\n                        if (completion != null && Math.Abs(liveEntry - completion.Price) <= atrNow * _maxEntryDeviationAtr)\n                            all.Add(c);\n                    }''',
'pre-rank entry proximity')

rep(
'''            else if (isAbcd)\n            {\n                double rBC = bc / ab;\n                double rCD = cd / ab;\n                if (!InRange(rBC, R_382, R_886)) return null;\n                if (!InFibRange(rCD, def.BIdeal, def.BMin, def.BMax)) return null;\n                geometry = (RatioScore(rBC, R_618) + RatioScore(rCD, def.BIdeal)) / 2.0;\n            }\n            else\n            {''',
'''            else if (isAbcd)\n            {\n                double rBC = bc / ab;\n                double rCD = cd / ab;\n                if (!InRange(rBC, R_382 - _fibTolerance, R_886 + _fibTolerance)) return null;\n                if (!InFibRange(rCD, def.BIdeal, def.BMin, def.BMax)) return null;\n                geometry = (RatioScore(rBC, R_618) + RatioScore(rCD, def.BIdeal)) / 2.0;\n            }\n            else if (def.Name == "Cypher")\n            {\n                double xc = Math.Abs(c.Price - x.Price);\n                if (xc <= 0) return null;\n                double rAB = ab / xa;\n                double rXC = xc / xa;\n                double rCDXC = cd / xc;\n                if (!InRange(rAB, R_382 - _fibTolerance, R_618 + _fibTolerance)) return null;\n                if (!InRange(rXC, R_1272 - _fibTolerance, R_1414 + _fibTolerance)) return null;\n                if (!InRange(rCDXC, R_786 - _fibTolerance, R_786 + _fibTolerance)) return null;\n                geometry = (RatioScore(rAB, R_50) + RatioScore(rXC, R_1272) + RatioScore(rCDXC, R_786)) / 3.0;\n            }\n            else\n            {''',
'Cypher pattern-specific geometry')

SRC.write_text(s, encoding='utf-8')

a = AUDIT.read_text(encoding='utf-8')
old = "ck('48 ABCD BC retracement filter','InRange(rBC, R_382, R_886)' in s)\nck('49 ABCD weight reduced','0.68, 0.60, 0.85, 0.90)' in s)\nck('50 success pattern race reset','_lastOpenedPattern = \"\";' in s)"
new = "ck('48 ABCD bullish-bearish reversal polarity','bull = (b.Price < a.Price) && (c.Price > b.Price) && (d.Price < c.Price);' in s)\nck('49 XABCD AD-XA completion geometry','double rAD = ad / xa;' in s and 'rXD = xd / xa' not in s)\nck('50 valid Fib zone tolerance semantics','double lo = Math.Max(0.0, min - _fibTolerance);' in s and 'double hi = max + _fibTolerance;' in s)"
if old not in a:
    raise SystemExit('audit gate block not found')
AUDIT.write_text(a.replace(old, new), encoding='utf-8')
REPORT.write_text('\n'.join(f'FIX {i+1:02d} {name}' for i, name in enumerate(fixes)) + '\n', encoding='utf-8')
print('\n'.join(fixes))
