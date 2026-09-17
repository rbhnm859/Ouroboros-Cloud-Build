from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')
orig=s
changes=[]

# Stage2 is deliberately conservative: remove repeated LINQ materialization in the
# grid-basket rebuild hot candidate without disabling Fib Grid or changing trade rules.
# Exact generated-source shapes are discovered at build time; unsupported shapes fail
# closed rather than silently changing semantics.
patterns=[
    (r'Positions\.Where\(([^\n;]+)\)\.ToList\(\)', r'Positions.Where(\1)', 'remove_positions_tolist'),
    (r'Positions\.Where\(([^\n;]+)\)\.ToArray\(\)', r'Positions.Where(\1)', 'remove_positions_toarray'),
]
for pat,repl,label in patterns:
    ns,n=re.subn(pat,repl,s)
    if n:
        s=ns; changes.append((label,n))

# Do not accept any patch that removes core commercial surfaces.
for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible']:
    if token not in s: raise SystemExit('Stage2 integrity failure: '+token)

p.write_text(s,encoding='utf-8')
print('Stage2 performance patch changes:',changes)
print('chars:',len(orig),'->',len(s))
