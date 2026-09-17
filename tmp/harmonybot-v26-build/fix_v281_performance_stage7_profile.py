from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
# Start from the exact commercial one-pass candidate so profiling matches production semantics.
exec(compile(Path('tmp/harmonybot-v26-build/fix_v281_commercial_onepass.py').read_text(encoding='utf-8'),'fix_v281_commercial_onepass.py','exec'),{})
s=p.read_text(encoding='utf-8')

# Stage7 instruments elapsed ticks as well as call counts. No trading branch, parameter,
# risk rule, harmonic geometry rule or Fibonacci Grid rule is changed.
targets=['ManageGridBaskets','RefreshEmaCache','CalculateEma','CalculateAtr','BuildSwingPoints','PruneExecutedSignalKeys','TryGetPositionLifecycleFromHistory']

onstart=re.search(r'(?m)^\s*protected\s+override\s+void\s+OnStart\s*\(',s)
if not onstart: raise SystemExit('OnStart missing')
fields=''.join('        private long _s7Calls_%s, _s7Ticks_%s;\n'%(x,x) for x in targets if x!='BuildSwingPoints')
fields+='        private static long _s7Calls_BuildSwingPoints, _s7Ticks_BuildSwingPoints;\n'
s=s[:onstart.start()]+fields+s[onstart.start():]

def method_span(src,name):
    m=re.search(r'(?m)^(\s*)(?:private|protected|public|internal)\s+(?:static\s+)?[^\n]+?\b'+re.escape(name)+r'\s*\([^\n]*\)\s*\n\s*\{',src)
    if not m: raise SystemExit(name+' missing')
    brace=src.find('{',m.start()); depth=0
    for i in range(brace,len(src)):
        if src[i]=='{': depth+=1
        elif src[i]=='}':
            depth-=1
            if depth==0: return m,i+1
    raise SystemExit(name+' unbalanced')

# Stopwatch.GetTimestamp has very low overhead. A try/finally guarantees elapsed-time
# accounting for early returns while preserving the original return values/exceptions.
for name in targets:
    m,end=method_span(s,name); indent=m.group(1); brace=s.find('{',m.start())
    body=s[brace+1:end-1]
    pre='\n%s    _s7Calls_%s++;\n%s    long _s7t0_%s = System.Diagnostics.Stopwatch.GetTimestamp();\n%s    try\n%s    {'%(indent,name,indent,name,indent,indent)
    post='\n%s    }\n%s    finally { _s7Ticks_%s += System.Diagnostics.Stopwatch.GetTimestamp() - _s7t0_%s; }\n%s'%(indent,indent,name,name,indent)
    wrapped=pre+body+post
    s=s[:brace+1]+wrapped+s[end-1:]

onstop=re.search(r'(?m)^(\s*)protected\s+override\s+void\s+OnStop\s*\(\s*\)\s*\n\s*\{',s)
if not onstop: raise SystemExit('OnStop missing')
pos=onstop.end(); ind=onstop.group(1)
for name in targets:
    line='\n%s    Print("[PERF-STAGE7] %s calls={0} ms={1:F3}", _s7Calls_%s, 1000.0 * _s7Ticks_%s / System.Diagnostics.Stopwatch.Frequency);'%(ind,name,name,name)
    s=s[:pos]+line+s[pos:]; pos+=len(line)

for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible','[PERF-STAGE7]','RiskPercent']:
    if token not in s: raise SystemExit('Stage7 integrity failure: '+token)
p.write_text(s,encoding='utf-8')
print('Applied Stage7 elapsed-time profiler; commercial trading semantics unchanged')
