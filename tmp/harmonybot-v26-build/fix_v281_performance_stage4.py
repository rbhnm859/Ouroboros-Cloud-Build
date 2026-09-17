from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# Stage4: safe memoization for pure EMA/ATR helpers. Keys include Bars identity/count,
# period and shift so values invalidate automatically on new bars. Trading rules unchanged.
onstart=re.search(r'(?m)^\s*protected\s+override\s+void\s+OnStart\s*\(',s)
if not onstart: raise SystemExit('OnStart missing')
fields='''        private readonly Dictionary<string, double> _stage4EmaCache = new Dictionary<string, double>();
        private readonly Dictionary<string, double> _stage4AtrCache = new Dictionary<string, double>();
        private long _stage4EmaHits, _stage4EmaMisses, _stage4AtrHits, _stage4AtrMisses;
'''
s=s[:onstart.start()]+fields+s[onstart.start():]

def instrument(name, cache, hits, misses):
    global s
    pat=re.compile(r'(?m)^(\s*)private\s+double\s+'+name+r'\s*\(\s*Bars\s+(\w+)\s*,\s*int\s+(\w+)(?:\s*,\s*int\s+(\w+))?\s*\)\s*\n\s*\{')
    m=pat.search(s)
    if not m: raise SystemExit(name+' signature missing')
    indent,bars,period,shift=m.group(1),m.group(2),m.group(3),m.group(4)
    sh=shift if shift else '0'
    body='''\n{0}    var _s4key = System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode({1}).ToString() + ":" + {1}.Count + ":" + {2} + ":" + {3};
{0}    double _s4cached;
{0}    if ({4}.TryGetValue(_s4key, out _s4cached)) {{ {5}++; return _s4cached; }}
{0}    {6}++;
'''.format(indent,bars,period,sh,cache,hits,misses)
    s=s[:m.end()]+body+s[m.end():]
    # Replace final return in this method only by locating balanced braces.
    start=m.end()+len(body); depth=1; i=start
    while i < len(s) and depth:
        if s[i]=='{': depth+=1
        elif s[i]=='}': depth-=1
        i+=1
    chunk=s[m.end():i-1]
    returns=list(re.finditer(r'(?m)^(\s*)return\s+([^;]+);',chunk))
    if not returns: raise SystemExit(name+' return missing')
    r=returns[-1]; expr=r.group(2); repl=r.group(1)+'var _s4result = '+expr+';\n'+r.group(1)+cache+'[_s4key] = _s4result;\n'+r.group(1)+'return _s4result;'
    chunk=chunk[:r.start()]+repl+chunk[r.end():]
    s=s[:m.end()]+chunk+s[i-1:]

instrument('CalculateEma','_stage4EmaCache','_stage4EmaHits','_stage4EmaMisses')
instrument('CalculateAtr','_stage4AtrCache','_stage4AtrHits','_stage4AtrMisses')

onstop=re.search(r'(?m)^(\s*)protected\s+override\s+void\s+OnStop\s*\(\s*\)\s*\n\s*\{',s)
if not onstop: raise SystemExit('OnStop missing')
pos=onstop.end(); ind=onstop.group(1)
s=s[:pos]+'\n'+ind+'    Print("[PERF-STAGE4] EMA hit={0} miss={1} ATR hit={2} miss={3}", _stage4EmaHits, _stage4EmaMisses, _stage4AtrHits, _stage4AtrMisses);'+s[pos:]
for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible','[PERF-STAGE4]','_stage4EmaCache','_stage4AtrCache']:
    if token not in s: raise SystemExit('Stage4 integrity failure: '+token)
p.write_text(s,encoding='utf-8')
print('Applied Stage4 safe EMA/ATR memoization; trading rules unchanged')
