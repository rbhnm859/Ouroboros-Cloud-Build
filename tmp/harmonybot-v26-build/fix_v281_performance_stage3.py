from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# Stage3: instrument concrete hotspot candidates without changing trading semantics.
if 'using System.Diagnostics;' not in s:
    s=s.replace('using System;', 'using System;\nusing System.Diagnostics;', 1)

methods=['RebuildGridBasketsFromOpenPositions','ManageGridBaskets','BuildSwingPoints','CalculateEma','CalculateAtr','RefreshEmaCache','TryGetPositionLifecycleFromHistory','PruneExecutedSignalKeys']
anchor=re.search(r'(?m)^(\s*)private\s+[^\n;]+;',s)
if not anchor: raise SystemExit('field anchor missing')
indent=anchor.group(1)
fields='\n'.join(f'{indent}private long _perfCalls_{m};' for m in methods)+'\n'
s=s[:anchor.start()]+fields+s[anchor.start():]

for m in methods:
    pat=re.compile(r'(?m)^(\s*)private\s+([^\n]+?)\s+'+re.escape(m)+r'\s*\(([^\n]*)\)\s*\n\s*\{')
    mt=pat.search(s)
    if not mt:
        print('instrumentation skip:',m); continue
    start=mt.end()
    body=f'\n{mt.group(1)}    _perfCalls_{m}++;\n'
    s=s[:start]+body+s[start:]

onstop=re.search(r'(?m)^(\s*)protected\s+override\s+void\s+OnStop\s*\(\s*\)\s*\n\s*\{',s)
if not onstop: raise SystemExit('OnStop missing')
pos=onstop.end()
lines='\n'+onstop.group(1)+'    Print("[PERF-STAGE3] '+ ' '.join(m+'={'+str(i)+'}' for i,m in enumerate(methods)) +'", '+', '.join('_perfCalls_'+m for m in methods)+');\n'
s=s[:pos]+lines+s[pos:]

for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible','[PERF-STAGE3]']:
    if token not in s: raise SystemExit('Stage3 integrity failure: '+token)
p.write_text(s,encoding='utf-8')
print('Applied Stage3 call-frequency instrumentation; trading semantics unchanged')
