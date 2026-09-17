from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
exec(compile(Path('tmp/harmonybot-v26-build/fix_v281_performance_stage5.py').read_text(encoding='utf-8'),'fix_v281_performance_stage5.py','exec'),{})
s=p.read_text(encoding='utf-8')

def match_bracket(text,start,op,cl):
    depth=0; instr=False; quote=''; esc=False
    for i in range(start,len(text)):
        c=text[i]
        if instr:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==quote: instr=False
            continue
        if c in ('\"',"'"): instr=True; quote=c; continue
        if c==op: depth+=1
        elif c==cl:
            depth-=1
            if depth==0:return i
    raise SystemExit('unbalanced '+op+cl)

def locate(text):
    for c in re.finditer(r'\bBuildSwingPoints\s*\(',text):
        ls=text.rfind('\n',0,c.start())+1; prefix=text[ls:c.start()]
        rt=re.search(r'\bList\s*<\s*([^>]+?)\s*>\s*$',prefix)
        if rt:
            op=text.find('(',c.start()); cp=match_bracket(text,op,'(',')'); ob=text.find('{',cp); cb=match_bracket(text,ob,'{','}')
            return c,ls,prefix,rt.group(1).strip(),op,cp,ob,cb
    raise SystemExit('BuildSwingPoints declaration missing')

c,ls,prefix,typ,op,cp,ob,cb=locate(s); params=s[op+1:cp]
parts=[x.strip() for x in params.split(',')]
if len(parts)!=4: raise SystemExit('Unexpected arity: '+params)
parsed=[]
for x in parts:
    m=re.search(r'([A-Za-z_][A-Za-z0-9_.<>,?\[\]]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*$',x)
    if not m: raise SystemExit('Cannot parse parameter '+x)
    parsed.append(m.groups())
if parsed[0][0].split('.')[-1]!='Bars' or any(t!='int' for t,n in parsed[1:]): raise SystemExit('Unexpected signature '+repr(parsed))
barsArg,endArg,lookArg,depthArg=[x[1] for x in parsed]; indent=re.match(r'\s*',prefix).group(0)

onstart=re.search(r'(?m)^\s*protected\s+override\s+void\s+OnStart\s*\(',s)
if not onstart: raise SystemExit('OnStart missing')
fields=f'''{indent}private Bars _coreSwingBars;\n{indent}private int _coreSwingEndIndex=-1,_coreSwingLookback=-1,_coreSwingDepth=-1,_coreSwingBarsCount=-1;\n{indent}private object _coreSwingCache;\n{indent}private long _coreSwingHits,_coreSwingMisses;\n'''
s=s[:onstart.start()]+fields+s[onstart.start():]

# Helper centralizes cache assignment, so inline/early/final returns are all safe and control flow is unchanged.
c,ls,prefix,typ,op,cp,ob,cb=locate(s)
helper=f'''\n{indent}private List<{typ}> CoreCacheSwingResult(List<{typ}> result, Bars bars, int endIndex, int lookback, int depth)\n{indent}{{\n{indent}    _coreSwingBars=bars; _coreSwingBarsCount=bars.Count; _coreSwingEndIndex=endIndex; _coreSwingLookback=lookback; _coreSwingDepth=depth; _coreSwingCache=result;\n{indent}    return result;\n{indent}}}\n\n'''
s=s[:ls]+helper+s[ls:]

c,ls,prefix,typ,op,cp,ob,cb=locate(s)
fast=f'''\n{indent}    if (ReferenceEquals(_coreSwingBars,{barsArg}) && _coreSwingBarsCount=={barsArg}.Count && _coreSwingEndIndex=={endArg} && _coreSwingLookback=={lookArg} && _coreSwingDepth=={depthArg} && _coreSwingCache is List<{typ}>) {{ _coreSwingHits++; return (List<{typ}>)_coreSwingCache; }}\n{indent}    _coreSwingMisses++;'''
s=s[:ob+1]+fast+s[ob+1:]
body_start=ob+1+len(fast); cb=match_bracket(s,ob,'{','}'); body=s[body_start:cb]
# Replace every return expression in this method, including `if (...) return pivots;` and final returns.
body,n=re.subn(r'\breturn\s+([^;\r\n]+)\s*;',lambda m:f'return CoreCacheSwingResult({m.group(1).strip()}, {barsArg}, {endArg}, {lookArg}, {depthArg});',body)
if n<1: raise SystemExit('No BuildSwingPoints return paths found')
s=s[:body_start]+body+s[cb:]

onstop=re.search(r'(?m)^(\s*)protected\s+override\s+void\s+OnStop\s*\(\s*\)\s*\n\s*\{',s)
if not onstop: raise SystemExit('OnStop missing')
pos=onstop.end(); oi=onstop.group(1)
s=s[:pos]+'\n'+oi+'    Print("[PERF-CORE] SwingParamCache hits={0} misses={1}", _coreSwingHits, _coreSwingMisses);'+s[pos:]
for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible','[PERF-STAGE5]','[PERF-CORE]','BuildSwingPoints','CoreCacheSwingResult','Gartley','Cypher']:
    if token not in s: raise SystemExit('Core integrity failure: '+token)
p.write_text(s,encoding='utf-8')
print('CORE_SIGNATURE='+params); print('CORE_RETURN_PATHS='+str(n)); print('Applied safe all-return-path parameterized swing cache; trading/risk/Grid/geometry semantics preserved')
