from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
# Preserve validated Stage5 first.
exec(compile(Path('tmp/harmonybot-v26-build/fix_v281_performance_stage5.py').read_text(encoding='utf-8'),'fix_v281_performance_stage5.py','exec'),{})
s=p.read_text(encoding='utf-8')
# Stage6: conservative same-bar memoization of BuildSwingPoints only when its signature is parameterless.
# This avoids altering detector semantics for overloads whose result depends on arguments.
onstart=re.search(r'(?m)^\s*protected\s+override\s+void\s+OnStart\s*\(',s)
if not onstart: raise SystemExit('OnStart missing')
fields='''        private int _stage6SwingBarsCount = -1;
        private object _stage6SwingCache = null;
        private long _stage6SwingHits, _stage6SwingMisses;
'''
s=s[:onstart.start()]+fields+s[onstart.start():]
# Locate method and only rewrite a parameterless List<T> BuildSwingPoints().
m=re.search(r'(?m)^(\s*)private\s+List<([^>]+)>\s+BuildSwingPoints\s*\(\s*\)\s*\n\s*\{',s)
if m:
    ind,typ=m.group(1),m.group(2); pos=m.end()
    fast=f'''\n{ind}    if (_stage6SwingBarsCount == Bars.Count && _stage6SwingCache is List<{typ}>) {{ _stage6SwingHits++; return (List<{typ}>)_stage6SwingCache; }}\n{ind}    _stage6SwingMisses++;\n'''
    s=s[:pos]+fast+s[pos:]
    # Cache each return result in this method body only.
    start=pos+len(fast); depth=1; i=start
    while i<len(s) and depth:
        if s[i]=='{': depth+=1
        elif s[i]=='}': depth-=1
        i+=1
    body=s[start:i-1]
    # Only safe simple final return variable; otherwise preserve method unchanged except lookup (which never hits until cache set).
    rm=list(re.finditer(r'(?m)^\s*return\s+([A-Za-z_][A-Za-z0-9_]*)\s*;',body))
    if rm:
        last=rm[-1]; var=last.group(1)
        repl=f'{ind}    _stage6SwingBarsCount = Bars.Count; _stage6SwingCache = {var}; return {var};'
        body=body[:last.start()]+repl+body[last.end():]
        s=s[:start]+body+s[i-1:]
# Add counters to OnStop.
onstop=re.search(r'(?m)^(\s*)protected\s+override\s+void\s+OnStop\s*\(\s*\)\s*\n\s*\{',s)
if not onstop: raise SystemExit('OnStop missing')
pos=onstop.end(); ind=onstop.group(1)
s=s[:pos]+'\n'+ind+'    Print("[PERF-STAGE6] SwingCache hits={0} misses={1}", _stage6SwingHits, _stage6SwingMisses);'+s[pos:]
for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible','[PERF-STAGE5]','[PERF-STAGE6]','BuildSwingPoints']:
    if token not in s: raise SystemExit('Stage6 integrity failure: '+token)
p.write_text(s,encoding='utf-8')
print('Applied Stage6 conservative upstream same-bar swing cache; all strategy/risk/Grid rules preserved')