from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# Reuse validated Stage4 pure EMA/ATR memoization first.
exec(compile(Path('tmp/harmonybot-v26-build/fix_v281_performance_stage4.py').read_text(encoding='utf-8'), 'fix_v281_performance_stage4.py', 'exec'), {})
s=p.read_text(encoding='utf-8')

# Stage5 targets the remaining hot paths without changing trading rules.
# RefreshEmaCache is redundant within the same Bars.Count: EMA inputs cannot change
# until a new bar exists. Preserve tick-level grid management because basket exits
# can be price-sensitive intrabar.
onstart=re.search(r'(?m)^\s*protected\s+override\s+void\s+OnStart\s*\(',s)
if not onstart: raise SystemExit('OnStart missing')
fields='''        private int _stage5LastEmaRefreshBarsCount = -1;
        private long _stage5EmaRefreshSkipped, _stage5EmaRefreshExecuted, _stage5GridCalls;
'''
s=s[:onstart.start()]+fields+s[onstart.start():]

# Add same-bar fast path to RefreshEmaCache only. This cache updates indicators from
# completed bar data, so repeated calls with identical Bars.Count are pure duplicates.
m=re.search(r'(?m)^(\s*)private\s+([^\n]+?)\s+RefreshEmaCache\s*\(([^\n]*)\)\s*\n\s*\{',s)
if not m: raise SystemExit('RefreshEmaCache missing')
ind=m.group(1); pos=m.end()
fast='''\n{0}    if (Bars.Count == _stage5LastEmaRefreshBarsCount) {{ _stage5EmaRefreshSkipped++; return; }}
{0}    _stage5LastEmaRefreshBarsCount = Bars.Count;
{0}    _stage5EmaRefreshExecuted++;
'''.format(ind)
s=s[:pos]+fast+s[pos:]

# Count grid calls but deliberately keep every call: Fibonacci Grid remains fully active.
g=re.search(r'(?m)^(\s*)private\s+([^\n]+?)\s+ManageGridBaskets\s*\(([^\n]*)\)\s*\n\s*\{',s)
if not g: raise SystemExit('ManageGridBaskets missing')
s=s[:g.end()]+'\n'+g.group(1)+'    _stage5GridCalls++; // preserve tick-level Fibonacci Grid management\n'+s[g.end():]

onstop=re.search(r'(?m)^(\s*)protected\s+override\s+void\s+OnStop\s*\(\s*\)\s*\n\s*\{',s)
if not onstop: raise SystemExit('OnStop missing')
pos=onstop.end(); ind=onstop.group(1)
s=s[:pos]+'\n'+ind+'    Print("[PERF-STAGE5] EmaRefresh executed={0} skipped={1} GridCalls={2}", _stage5EmaRefreshExecuted, _stage5EmaRefreshSkipped, _stage5GridCalls);'+s[pos:]

for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','capitalInfeasible','[PERF-STAGE4]','[PERF-STAGE5]','ManageGridBaskets','RefreshEmaCache']:
    if token not in s: raise SystemExit('Stage5 integrity failure: '+token)
p.write_text(s,encoding='utf-8')
print('Applied Stage5 same-bar EMA refresh fast path; Fibonacci Grid tick management preserved')
