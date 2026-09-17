from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# Stage4: memoize pure DataSeries EMA/ATR helpers by series identity/count + arguments.
# Cache invalidates automatically when the underlying series grows. Trading rules unchanged.
onstart=re.search(r'(?m)^\s*protected\s+override\s+void\s+OnStart\s*\(',s)
if not onstart: raise SystemExit('OnStart missing')
fields='''        private readonly Dictionary<string, double> _stage4EmaCache = new Dictionary<string, double>();
        private readonly Dictionary<string, double> _stage4AtrCache = new Dictionary<string, double>();
        private long _stage4EmaHits, _stage4EmaMisses, _stage4AtrHits, _stage4AtrMisses;
'''
s=s[:onstart.start()]+fields+s[onstart.start():]

def find_method(name):
    # Actual generated V28.1 helpers use DataSeries, e.g.
    # CalculateEma(DataSeries series, int period, int endIndex).
    pat=re.compile(r'(?m)^(\s*)private\s+double\s+'+re.escape(name)+r'\s*\(\s*DataSeries\s+(\w+)\s*,\s*int\s+(\w+)\s*,\s*int\s+(\w+)\s*\)\s*\n\s*\{')
    m=pat.search(s)
    if not m:
        # Emit nearby declaration text so future signature drift is immediately diagnosable.
        decl=re.search(r'(?m)^.*\b'+re.escape(name)+r'\s*\([^\n]*',s)
        raise SystemExit(name+' signature missing; found='+repr(decl.group(0).strip() if decl else None))
    return m

def instrument(name, cache, hits, misses):
    global s
    m=find_method(name)
    indent,series,period,endidx=m.group(1),m.group(2),m.group(3),m.group(4)
    body='''\n{0}    var _s4key = System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode({1}).ToString() + ":" + {1}.Count + ":" + {2} + ":" + {3};
{0}    double _s4cached;
{0}    if ({4}.TryGetValue(_s4key, out _s4cached)) {{ {5}++; return _s4cached; }}
{0}    {6}++;
'''.format(indent,series,period,endidx,cache,hits,misses)
    original_end=m.end()
    s=s[:original_end]+body+s[original_end:]
    # Find this method's balanced closing brace after insertion.
    start=original_end+len(body); depth=1; i=start
    while i < len(s) and depth:
        if s[i]=='{': depth+=1
        elif s[i]=='}': depth-=1
        i+=1
    chunk=s[original_end:i-1]
    returns=list(re.finditer(r'(?m)^(\s*)return\s+([^;]+);',chunk))
    if not returns: raise SystemExit(name+' return missing')
    # Cache only the final normal result; early validation returns retain original behavior.
    r=returns[-1]; expr=r.group(2)
    repl=r.group(1)+'var _s4result = '+expr+';\n'+r.group(1)+cache+'[_s4key] = _s4result;\n'+r.group(1)+'return _s4result;'
    chunk=chunk[:r.start()]+repl+chunk[r.end():]
    s=s[:original_end]+chunk+s[i-1:]

instrument('CalculateEma','_stage4EmaCache','_stage4EmaHits','_stage4EmaMisses')
instrument('CalculateAtr','_stage4AtrCache','_stage4AtrHits','_stage4AtrMisses')

onstop=re.search(r'(?m)^(\s*)protected\s+override\s+void\s+OnStop\s*\(\s*\)\s*\n\s*\{',s)
if not onstop: raise SystemExit('OnStop missing')
pos=onstop.end(); ind=onstop.group(1)
s=s[:pos]+'\n'+ind+'    Print("[PERF-STAGE4] EMA hit={0} miss={1} ATR hit={2} miss={3}", _stage4EmaHits, _stage4EmaMisses, _stage4AtrHits, _stage4AtrMisses);'+s[pos:]
for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible','[PERF-STAGE4]','_stage4EmaCache','_stage4AtrCache','DataSeries']:
    if token not in s: raise SystemExit('Stage4 integrity failure: '+token)
p.write_text(s,encoding='utf-8')
print('Applied Stage4 DataSeries EMA/ATR memoization; trading rules unchanged')
