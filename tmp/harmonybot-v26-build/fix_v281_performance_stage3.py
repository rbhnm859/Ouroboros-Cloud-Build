from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# Stage3 call-frequency instrumentation. Trading semantics remain unchanged.
main_methods=['RebuildGridBasketsFromOpenPositions','ManageGridBaskets','CalculateEma','CalculateAtr','RefreshEmaCache','TryGetPositionLifecycleFromHistory','PruneExecutedSignalKeys']

# Main Robot counters.
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

# BuildSwingPoints is static in HarmonicPatternDetector. Its diagnostic counter must
# therefore also be static; this changes profiling state only, never trading decisions.
bsp=re.search(r'(?m)^(\s*)private\s+([^\n]+?)\s+BuildSwingPoints\s*\(([^\n]*)\)\s*\n\s*\{',s)
if not bsp: raise SystemExit('BuildSwingPoints missing')
bsp_indent=bsp.group(1)
s=s[:bsp.start()]+bsp_indent+'private static long _perfCalls_BuildSwingPoints;\n'+s[bsp.start():]
bsp=re.search(r'(?m)^(\s*)private\s+([^\n]+?)\s+BuildSwingPoints\s*\(([^\n]*)\)\s*\n\s*\{',s)
s=s[:bsp.end()]+'\n'+bsp.group(1)+'    _perfCalls_BuildSwingPoints++;\n'+s[bsp.end():]

onstop=re.search(r'(?m)^(\s*)protected\s+override\s+void\s+OnStop\s*\(\s*\)\s*\n\s*\{',s)
if not onstop: raise SystemExit('OnStop missing')
pos=onstop.end()
fmt=' '.join(m+'={'+str(i)+'}' for i,m in enumerate(main_methods))
args=', '.join('_perfCalls_'+m for m in main_methods)
s=s[:pos]+'\n'+onstop.group(1)+'    Print("[PERF-STAGE3] '+fmt+'", '+args+');\n'+s[pos:]

for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible','[PERF-STAGE3]','private static long _perfCalls_BuildSwingPoints','_perfCalls_BuildSwingPoints++']:
    if token not in s: raise SystemExit('Stage3 integrity failure: '+token)
p.write_text(s,encoding='utf-8')
print('Applied Stage3 static-safe call-frequency instrumentation; trading semantics unchanged')
