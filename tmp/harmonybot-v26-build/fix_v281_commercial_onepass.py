from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
# Keep proven Stage5 EMA/ATR + once-per-bar EMA refresh; intentionally remove ineffective swing-cache experiment.
exec(compile(Path('tmp/harmonybot-v26-build/fix_v281_performance_stage5.py').read_text(encoding='utf-8'),'fix_v281_performance_stage5.py','exec'),{})
s=p.read_text(encoding='utf-8')

# SmallAccountMode is an explicit operating mode. Do not silently disable its 25-pip floor/fallback
# merely because compounding moves equity above the classification threshold. RiskPercent remains unchanged.
old='SmallAccountMode && Account.Equity <= SmallAccountThreshold'
count=s.count(old)
if count < 1:
    raise SystemExit('Small-account equity-gated precedence point missing')
s=s.replace(old,'SmallAccountMode')

# Audit the generated effective stop/TP methods and ensure the explicit mode is referenced.
for method in ['EffectiveMinStopLossPips','EffectiveMinTakeProfitPips']:
    m=re.search(r'private\s+double\s+'+method+r'\s*\(\s*\)\s*\{(?P<body>.*?)\n\s*\}',s,re.S)
    if not m or 'SmallAccountMode' not in m.group('body'):
        raise SystemExit(method+' does not honor explicit SmallAccountMode')

# Preserve all commercial invariants. No risk inflation, no Grid removal, no pattern removal.
for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','SmallAccountMinTPPips','RiskPercent','capitalInfeasible','Gartley','Bat','Butterfly','Crab','Cypher','Shark','FiveZero']:
    if token not in s: raise SystemExit('commercial integrity missing: '+token)
if 'private static Bars _coreSwingBars' in s or 'CoreCacheSwingResult' in s:
    raise SystemExit('ineffective core swing cache leaked into one-pass build')

p.write_text(s,encoding='utf-8')
print('ONEPASS_SMALL_ACCOUNT_REWRITES='+str(count))
print('Applied persistent explicit SmallAccountMode precedence; RiskPercent unchanged; Fib Grid and harmonic engine preserved')
print('Retained proven Stage5 EMA/ATR fast path; removed ineffective swing-cache experiment')
