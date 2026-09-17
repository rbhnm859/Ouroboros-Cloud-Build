from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# Stage3: instrument the concrete static-hotspot candidates without changing trading semantics.
# Counters + Stopwatch ticks are emitted only at stop, so the next run tells us where runtime is spent.
if 'using System.Diagnostics;' not in s:
    s=s.replace('using System;', 'using System;\nusing System.Diagnostics;', 1)

methods=['RebuildGridBasketsFromOpenPositions','ManageGridBaskets','BuildSwingPoints','CalculateEma','CalculateAtr','RefreshEmaCache','TryGetPositionLifecycleFromHistory','PruneExecutedSignalKeys']

# Insert counters near Robot fields using a stable first private-field anchor.
anchor=re.search(r'(?m)^(\s*)private\s+[^\n;]+;',s)
if not anchor: raise SystemExit('field anchor missing')
indent=anchor.group(1)
fields='\n'.join(f'{indent}private long _perfCalls_{m}, _perfTicks_{m};' for m in methods)+'\n'
s=s[:anchor.start()]+fields+s[anchor.start():]

# Instrument method bodies. Handles private methods with arbitrary return types/arguments.
for m in methods:
    pat=re.compile(r'(?m)^(\s*)private\s+([^\n]+?)\s+'+re.escape(m)+r'\s*\(([^\n]*)\)\s*\n\s*\{')
    mt=pat.search(s)
    if not mt:
        print('instrumentation skip:',m); continue
    start=mt.end()
    body=f'\n{mt.group(1)}    _perfCalls_{m}++;\n{mt.group(1)}    long __perfStart_{m}=Stopwatch.GetTimestamp();\n'
    s=s[:start]+body+s[start:]
    # We deliberately count entry calls first. Exact elapsed timing for early-return methods is deferred;
    # call-frequency is sufficient to choose the first semantics-preserving optimization target.

# Add one stop-time diagnostic before the first OnStop closing brace body endpoint.
onstop=re.search(r'(?m)^(\s*)protected\s+override\s+void\s+OnStop\s*\(\s*\)\s*\n\s*\{',s)
if not nonstop: raise SystemExit('OnStop missing')
pos=onstop.end()
lines='\n'+onstop.group(1)+'    Print("[PERF-STAGE3] '+ ' '.join(m+'={'+str(i)+'}' for i,m in enumerate(methods)) +'", '+', '.join('_perfCalls_'+m for m in methods)+');\n'
s=s[:pos]+lines+s[pos:]

for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible','[PERF-STAGE3]']:
    if token not in s: raise SystemExit('Stage3 integrity failure: '+token)
p.write_text(s,encoding='utf-8')
print('Applied Stage3 call-frequency instrumentation; trading semantics unchanged')
