from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
# Keep proven Stage5 EMA/ATR + once-per-bar EMA refresh; intentionally remove ineffective swing-cache experiment.
exec(compile(Path('tmp/harmonybot-v26-build/fix_v281_performance_stage5.py').read_text(encoding='utf-8'),'fix_v281_performance_stage5.py','exec'),{})
s=p.read_text(encoding='utf-8')

# SmallAccountMode is an explicit operating mode. Change ONLY the two effective minimum-distance
# methods. Do not globally replace equity predicates because some occurrences participate in
# numeric ternaries and a global textual rewrite can create bool + double expressions.
def rewrite_effective_method(src, method):
    pat=re.compile(r'(private\s+double\s+'+re.escape(method)+r'\s*\(\s*\)\s*\{)(?P<body>.*?)(\n\s*\})',re.S)
    m=pat.search(src)
    if not m: raise SystemExit(method+' missing')
    body=m.group('body')
    old='SmallAccountMode && Account.Equity <= SmallAccountThreshold'
    n=body.count(old)
    if n < 1: raise SystemExit(method+' equity-gated precedence point missing')
    body=body.replace(old,'SmallAccountMode')
    return src[:m.start('body')]+body+src[m.end('body'):],n
count=0
for method in ['EffectiveMinStopLossPips','EffectiveMinTakeProfitPips']:
    s,n=rewrite_effective_method(s,method); count+=n

# Compile-sanity guard against the exact regression seen in the previous candidate.
# Also require the two effective methods to honor explicit SmallAccountMode.
for method in ['EffectiveMinStopLossPips','EffectiveMinTakeProfitPips']:
    m=re.search(r'private\s+double\s+'+method+r'\s*\(\s*\)\s*\{(?P<body>.*?)\n\s*\}',s,re.S)
    if not m or 'SmallAccountMode' not in m.group('body'):
        raise SystemExit(method+' does not honor explicit SmallAccountMode')
if re.search(r'\b(?:true|false|SmallAccountMode)\s*\+\s*[0-9A-Za-z_(.]',s):
    raise SystemExit('bool-plus-numeric regression detected')

# Preserve all commercial invariants. No risk inflation, no Grid removal, no pattern removal.
for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','SmallAccountMinTPPips','RiskPercent','capitalInfeasible','Gartley','Bat','Butterfly','Crab','Cypher','Shark','FiveZero']:
    if token not in s: raise SystemExit('commercial integrity missing: '+token)
if 'private static Bars _coreSwingBars' in s or 'CoreCacheSwingResult' in s:
    raise SystemExit('ineffective core swing cache leaked into one-pass build')

p.write_text(s,encoding='utf-8')
print('ONEPASS_SMALL_ACCOUNT_REWRITES='+str(count))
print('Applied method-scoped explicit SmallAccountMode precedence; RiskPercent unchanged; Fib Grid and harmonic engine preserved')
print('Retained proven Stage5 EMA/ATR fast path; removed ineffective swing-cache experiment')
