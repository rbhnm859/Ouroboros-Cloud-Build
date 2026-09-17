from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
exec(compile(Path('tmp/harmonybot-v26-build/fix_v281_performance_stage5.py').read_text(encoding='utf-8'),'fix_v281_performance_stage5.py','exec'),{})
s=p.read_text(encoding='utf-8')

def match_bracket(text, start, op, cl):
    depth=0
    in_str=False; quote=''; esc=False
    for i in range(start,len(text)):
        c=text[i]
        if in_str:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==quote: in_str=False
            continue
        if c in ('\"', "'"): in_str=True; quote=c; continue
        if c==op: depth+=1
        elif c==cl:
            depth-=1
            if depth==0: return i
    raise SystemExit('unbalanced '+op+cl)

# Locate the generated method by name first, then structurally parse its parameter list/body.
name=re.search(r'\bBuildSwingPoints\s*\(',s)
if not name: raise SystemExit('BuildSwingPoints name missing after full patch chain')
# Prefer the declaration occurrence: it must have List<...> before the method name on the same declaration segment.
candidates=list(re.finditer(r'\bBuildSwingPoints\s*\(',s))
decl=None
for c in candidates:
    line_start=s.rfind('\n',0,c.start())+1
    prefix=s[line_start:c.start()]
    if re.search(r'\bList\s*<[^>]+>\s*$',prefix): decl=(c,line_start,prefix); break
if decl is None: raise SystemExit('BuildSwingPoints declaration missing; calls='+str(len(candidates)))
c,line_start,prefix=decl
open_par=s.find('(',c.start()); close_par=match_bracket(s,open_par,'(',')')
params=s[open_par+1:close_par]
open_brace=s.find('{',close_par)
if open_brace<0: raise SystemExit('BuildSwingPoints body missing')
close_brace=match_bracket(s,open_brace,'{','}')
ret=re.search(r'List\s*<\s*([^>]+?)\s*>\s*$',prefix)
if not ret: raise SystemExit('BuildSwingPoints return type missing')
typ=ret.group(1).strip()
parts=[x.strip() for x in params.split(',')]
if len(parts)!=4: raise SystemExit('Unexpected BuildSwingPoints arity: '+params)
parsed=[]
for x in parts:
    mm=re.search(r'([A-Za-z_][A-Za-z0-9_<>,.?\[\]]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*$',x)
    if not mm: raise SystemExit('Cannot parse parameter: '+x)
    parsed.append(mm.groups())
if parsed[0][0].split('.')[-1] != 'Bars' or any(t!='int' for t,n in parsed[1:]):
    raise SystemExit('Unexpected BuildSwingPoints types: '+repr(parsed))
barsArg=parsed[0][1]; endArg=parsed[1][1]; lookArg=parsed[2][1]; depthArg=parsed[3][1]
indent=re.match(r'\s*',prefix).group(0)

onstart=re.search(r'(?m)^\s*protected\s+override\s+void\s+OnStart\s*\(',s)
if not onstart: raise SystemExit('OnStart missing')
fields=f'''{indent}private Bars _coreSwingBars;\n{indent}private int _coreSwingEndIndex = -1, _coreSwingLookback = -1, _coreSwingDepth = -1, _coreSwingBarsCount = -1;\n{indent}private object _coreSwingCache;\n{indent}private long _coreSwingHits, _coreSwingMisses;\n'''
s=s[:onstart.start()]+fields+s[onstart.start():]
# Re-find after field insertion.
candidates=list(re.finditer(r'\bBuildSwingPoints\s*\(',s)); declc=None
for cc in candidates:
    ls=s.rfind('\n',0,cc.start())+1
    if re.search(r'\bList\s*<[^>]+>\s*$',s[ls:cc.start()]): declc=cc; break
open_par=s.find('(',declc.start()); close_par=match_bracket(s,open_par,'(',')'); open_brace=s.find('{',close_par); close_brace=match_bracket(s,open_brace,'{','}')
fast=f'''\n{indent}    if (ReferenceEquals(_coreSwingBars, {barsArg}) && _coreSwingBarsCount == {barsArg}.Count && _coreSwingEndIndex == {endArg} && _coreSwingLookback == {lookArg} && _coreSwingDepth == {depthArg} && _coreSwingCache is List<{typ}>) {{ _coreSwingHits++; return (List<{typ}>)_coreSwingCache; }}\n{indent}    _coreSwingMisses++;'''
s=s[:open_brace+1]+fast+s[open_brace+1:]
body_start=open_brace+1+len(fast); close_brace=match_bracket(s,open_brace,'{','}'); body=s[body_start:close_brace]

def repl(mm):
    var=mm.group(1)
    return f'''{indent}    _coreSwingBars = {barsArg}; _coreSwingBarsCount = {barsArg}.Count; _coreSwingEndIndex = {endArg}; _coreSwingLookback = {lookArg}; _coreSwingDepth = {depthArg}; _coreSwingCache = {var};\n{indent}    return {var};'''
body,n=re.subn(r'(?m)^\s*return\s+([A-Za-z_][A-Za-z0-9_]*)\s*;',repl,body)
if n<1: raise SystemExit('BuildSwingPoints has no simple return to cache')
s=s[:body_start]+body+s[close_brace:]

onstop=re.search(r'(?m)^(\s*)protected\s+override\s+void\s+OnStop\s*\(\s*\)\s*\n\s*\{',s)
if not onstop: raise SystemExit('OnStop missing')
pos=onstop.end(); oi=onstop.group(1)
s=s[:pos]+'\n'+oi+'    Print("[PERF-CORE] SwingParamCache hits={0} misses={1}", _coreSwingHits, _coreSwingMisses);'+s[pos:]
for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible','[PERF-STAGE5]','[PERF-CORE]','BuildSwingPoints','Gartley','Cypher']:
    if token not in s: raise SystemExit('Core integrity failure: '+token)
p.write_text(s,encoding='utf-8')
print('CORE_SIGNATURE='+params)
print('CORE_CALL_OCCURRENCES='+str(len(candidates)))
print('Applied structural parameterized swing/pivot memoization; Grid/risk/geometry semantics preserved')
