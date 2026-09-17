from pathlib import Path
import re

p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# V28.2 Strategy Quality RC: diagnostic-only observability layer.
# Preserve trading decisions, RiskPercent, Fibonacci Grid and structural SL semantics.
class_m=re.search(r'(public\s+class\s+HarmonyBotPro\s*:\s*Robot\s*\{)',s)
if not class_m:
    raise SystemExit('HarmonyBotPro class anchor missing')
marker='''\n        private const string CommercialIteration = "V28.2-Strategy-Quality-RC";\n        private long _v282GeometryAccepted;\n        private long _v282CapitalRejected;\n        private long _v282GridAttributed;\n'''
s=s[:class_m.end()]+marker+s[class_m.end():]

if 'GeometryQualityScore' not in s:
    raise SystemExit('GeometryQualityScore missing')

helper='''\n        private string V282GeometryBucket(double q)\n        {\n            if (q >= 90.0) return "Q90+";\n            if (q >= 80.0) return "Q80-90";\n            if (q >= 70.0) return "Q70-80";\n            return "Q<70";\n        }\n\n        private void V282AuditCandidate(string pattern, double quality, double structuralSlPips, double effectiveSlPips, double allInRiskPct, bool capitalFeasible, string stage)\n        {\n            if (capitalFeasible) _v282GeometryAccepted++; else _v282CapitalRejected++;\n            Print("[V282-QUALITY] stage={0} pattern={1} bucket={2} quality={3:F2} structuralSL={4:F1} effectiveSL={5:F1} allInRiskPct={6:F3} capitalFeasible={7}",\n                stage, pattern ?? "NA", V282GeometryBucket(quality), quality, structuralSlPips, effectiveSlPips, allInRiskPct, capitalFeasible);\n        }\n\n        private void V282AuditGrid(string pattern, string action, double plannedRiskPct)\n        {\n            _v282GridAttributed++;\n            Print("[V282-GRID] pattern={0} action={1} plannedRiskPct={2:F3}", pattern ?? "NA", action ?? "NA", plannedRiskPct);\n        }\n'''
onstop=re.search(r'\n\s*protected\s+override\s+void\s+OnStop\s*\(',s)
insert=onstop.start() if nonstop else s.rfind('}')
if insert < 0:
    raise SystemExit('class closing brace missing')
s=s[:insert]+helper+s[insert:]

onstop2=re.search(r'(protected\s+override\s+void\s+OnStop\s*\([^)]*\)\s*\{)',s)
if not nonstop2:
    raise SystemExit('OnStop missing')
audit='''\n            Print("[V282-SUMMARY] iteration={0} geometryAccepted={1} capitalRejected={2} gridAttributed={3}", CommercialIteration, _v282GeometryAccepted, _v282CapitalRejected, _v282GridAttributed);\n'''
s=s[:nonstop2.end()]+audit+s[nonstop2.end():]

for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMode','SmallAccountMinSLPips','RiskPercent','capitalInfeasible','MinRR','Gartley','Bat','Butterfly','Crab','Cypher','Shark','FiveZero']:
    if token not in s:
        raise SystemExit('V28.2 integrity missing: '+token)

p.write_text(s,encoding='utf-8')
print('Applied V28.2 Strategy Quality RC diagnostics')
print('Preserved harmonic families, Fibonacci Grid, structural SL and base RiskPercent')
print('Added geometry quality buckets, capital-feasibility and Grid attribution audit hooks')
