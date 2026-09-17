from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
# Start from the validated Stage5 semantics. Stage6 is intentionally skipped: D1 proved its parameterless matcher never hit.
exec(compile(Path('tmp/harmonybot-v26-build/fix_v281_performance_stage5.py').read_text(encoding='utf-8'),'fix_v281_performance_stage5.py','exec'),{})
s=p.read_text(encoding='utf-8')

# One-pass core fix: cache the ACTUAL parameterized BuildSwingPoints(Bars,endIndex,lookback,depth)
# by all inputs that determine its result. This preserves the 12-pattern detector semantics while eliminating
# repeated identical pivot scans inside a completed-bar detection cycle.
onstart=re.search(r'(?m)^\s*protected\s+override\s+void\s+OnStart\s*\(',s)
if not onstart: raise SystemExit('OnStart missing')
fields='''        private Bars _coreSwingBars;
        private int _coreSwingEndIndex = -1, _coreSwingLookback = -1, _coreSwingDepth = -1, _coreSwingBarsCount = -1;
        private object _coreSwingCache;
        private long _coreSwingHits, _coreSwingMisses;
'''
s=s[:onstart.start()]+fields+s[onstart.start():]

m=re.search(r'(?m)^(\s*)private\s+List<([^>]+)>\s+BuildSwingPoints\s*\(\s*Bars\s+(\w+)\s*,\s*int\s+(\w+)\s*,\s*int\s+(\w+)\s*,\s*int\s+(\w+)\s*\)\s*\n\s*\{',s)
if not m: raise SystemExit('Actual parameterized BuildSwingPoints signature missing')
ind,typ,barsArg,endArg,lookArg,depthArg=m.groups(); pos=m.end()
fast=f'''\n{ind}    if (ReferenceEquals(_coreSwingBars, {barsArg}) && _coreSwingBarsCount == {barsArg}.Count && _coreSwingEndIndex == {endArg} && _coreSwingLookback == {lookArg} && _coreSwingDepth == {depthArg} && _coreSwingCache is List<{typ}>) {{ _coreSwingHits++; return (List<{typ}>)_coreSwingCache; }}
{ind}    _coreSwingMisses++;
'''
s=s[:pos]+fast+s[pos:]
start=pos+len(fast); depth=1; i=start
while i<len(s) and depth:
    if s[i]=='{': depth+=1
    elif s[i]=='}': depth-=1
    i+=1
body=s[start:i-1]
# Cache every simple return variable in the method so early/final exits are covered.
def cache_return(mm):
    var=mm.group(1)
    return f'''{ind}    _coreSwingBars = {barsArg}; _coreSwingBarsCount = {barsArg}.Count; _coreSwingEndIndex = {endArg}; _coreSwingLookback = {lookArg}; _coreSwingDepth = {depthArg}; _coreSwingCache = {var};\n{ind}    return {var};'''
body,n=re.subn(r'(?m)^\s*return\s+([A-Za-z_][A-Za-z0-9_]*)\s*;',cache_return,body)
if n<1: raise SystemExit('BuildSwingPoints has no cacheable return')
s=s[:start]+body+s[i-1:]

# Instrument detector calls and preserve closed-bar semantics; no signal/risk thresholds are changed.
trydetect=re.search(r'(?m)^(\s*)(?:public|private)\s+bool\s+TryDetect\s*\(',s)
if trydetect:
    # Counters are intentionally represented by swing hit/miss evidence; no invasive detector rewrite.
    pass

onstop=re.search(r'(?m)^(\s*)protected\s+override\s+void\s+OnStop\s*\(\s*\)\s*\n\s*\{',s)
if not onstop: raise SystemExit('OnStop missing')
pos=onstop.end(); oi=onstop.group(1)
s=s[:pos]+'\n'+oi+'    Print("[PERF-CORE] SwingParamCache hits={0} misses={1}", _coreSwingHits, _coreSwingMisses);'+s[pos:]

for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible','[PERF-STAGE5]','[PERF-CORE]','BuildSwingPoints','Gartley','Cypher']:
    if token not in s: raise SystemExit('Core integrity failure: '+token)
p.write_text(s,encoding='utf-8')
print('Applied one-pass core hot-path fix: actual parameterized swing/pivot scan memoization; Grid/risk/geometry semantics preserved')
