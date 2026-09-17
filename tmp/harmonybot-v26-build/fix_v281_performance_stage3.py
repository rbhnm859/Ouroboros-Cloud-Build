from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# Stage3 call-frequency instrumentation. Trading semantics remain unchanged.
# BuildSwingPoints belongs to the nested HarmonicDetector, while the other hot paths
# belong to the main Robot. Keep counters in the same declaring type as each method.
main_methods=['RebuildGridBasketsFromOpenPositions','ManageGridBaskets','CalculateEma','CalculateAtr','RefreshEmaCache','TryGetPositionLifecycleFromHistory','PruneExecutedSignalKeys']

# Main Robot counters: insert immediately before OnStart, which is unambiguously inside HarmonyBotPro.
onstart=re.search(r'(?m)^\s*protected\s+override\s+void\s+OnStart\s*\(',s)
if not onstart: raise SystemExit('OnStart missing')
fields=''.join(f'        private long _perfCalls_{m};\n' for m in main_methods)
s=s[:onstart.start()]+fields+s[onstart.start():]

for m in main_methods:
    pat=re.compile(r'(?m)^(\s*)private\s+([^\n]+?)\s+'+re.escape(m)+r'\s*\(([^\n]*)\)\s*\n\s*\{')
    mt=pat.search(s)
    if not mt:
        print('instrumentation skip:',m); continue
    s=s[:mt.end()]+'\n'+mt.group(1)+'    _perfCalls_'+m+'++;\n'+s[mt.end():]

# BuildSwingPoints is a nested HarmonicDetector method. Give that declaring type its own counter.
bsp=re.search(r'(?m)^(\s*)private\s+([^\n]+?)\s+BuildSwingPoints\s*\(([^\n]*)\)\s*\n\s*\{',s)
if not bsp: raise SystemExit('BuildSwingPoints missing')
bsp_indent=bsp.group(1)
s=s[:bsp.start()]+bsp_indent+'private long _perfCalls_BuildSwingPoints;\n'+s[bsp.start():]
bsp=re.search(r'(?m)^(\s*)private\s+([^\n]+?)\s+BuildSwingPoints\s*\(([^\n]*)\)\s*\n\s*\{',s)
s=s[:bsp.end()]+'\n'+bsp.group(1)+'    _perfCalls_BuildSwingPoints++;\n'+s[bsp.end():]

# Main Robot stop-time counters. Nested BuildSwingPoints remains detector-local.
onstop=re.search(r'(?m)^(\s*)protected\s+override\s+void\s+OnStop\s*\(\s*\)\s*\n\s*\{',s)
if not onstop: raise SystemExit('OnStop missing')
pos=onstop.end()
fmt=' '.join(m+'={'+str(i)+'}' for i,m in enumerate(main_methods))
args=', '.join('_perfCalls_'+m for m in main_methods)
s=s[:pos]+'\n'+onstop.group(1)+'    Print("[PERF-STAGE3] '+fmt+'", '+args+');\n'+s[pos:]

for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible','[PERF-STAGE3]','_perfCalls_BuildSwingPoints++']:
    if token not in s: raise SystemExit('Stage3 integrity failure: '+token)
p.write_text(s,encoding='utf-8')
print('Applied Stage3 scope-safe call-frequency instrumentation; trading semantics unchanged')
