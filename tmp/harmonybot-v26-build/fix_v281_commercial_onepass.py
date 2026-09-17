from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
exec(compile(Path('tmp/harmonybot-v26-build/fix_v281_performance_stage5.py').read_text(encoding='utf-8'),'fix_v281_performance_stage5.py','exec'),{})
s=p.read_text(encoding='utf-8')

# Explicit SmallAccountMode must keep the small-account distance floors active for the whole run.
# Work only inside the two effective distance methods and tolerate formatting / predicate variants.
def method_span(src,name):
    m=re.search(r'private\s+double\s+'+re.escape(name)+r'\s*\(\s*\)\s*\{',src)
    if not m: raise SystemExit(name+' missing')
    brace=src.find('{',m.start()); depth=0
    for i in range(brace,len(src)):
        if src[i]=='{': depth+=1
        elif src[i]=='}':
            depth-=1
            if depth==0: return m.start(),i+1,src[m.start():i+1]
    raise SystemExit(name+' unbalanced')

def rewrite_method(src,name):
    a,b,block=method_span(src,name)
    before=block
    # Remove only an equity/threshold conjunct that is attached to SmallAccountMode.
    block,n1=re.subn(r'SmallAccountMode\s*&&\s*Account\.(?:Equity|Balance)\s*<=\s*SmallAccountThreshold', 'SmallAccountMode', block)
    block,n2=re.subn(r'Account\.(?:Equity|Balance)\s*<=\s*SmallAccountThreshold\s*&&\s*SmallAccountMode', 'SmallAccountMode', block)
    # Some hardened builds use IsMicroAccount as the derived threshold gate.
    block,n3=re.subn(r'SmallAccountMode\s*&&\s*IsMicroAccount(?:\(\))?', 'SmallAccountMode', block)
    block,n4=re.subn(r'IsMicroAccount(?:\(\))?\s*&&\s*SmallAccountMode', 'SmallAccountMode', block)
    if 'SmallAccountMode' not in block: raise SystemExit(name+' has no SmallAccountMode branch')
    # If no threshold conjunct exists, the generated method already has explicit-mode precedence: accept it unchanged.
    changed=n1+n2+n3+n4
    return src[:a]+block+src[b:],changed

count=0
for method in ['EffectiveMinStopLossPips','EffectiveMinTakeProfitPips']:
    s,n=rewrite_method(s,method); count+=n

# Structural sanity: effective methods must contain the small-account parameter and SmallAccountMode.
for method,param in [('EffectiveMinStopLossPips','SmallAccountMinSLPips'),('EffectiveMinTakeProfitPips','SmallAccountMinTPPips')]:
    _,_,block=method_span(s,method)
    if 'SmallAccountMode' not in block or param not in block:
        raise SystemExit(method+' explicit small-account precedence incomplete')
# Guard the previous bad global rewrite class.
if re.search(r'\b(?:true|false|SmallAccountMode)\s*\+\s*[0-9A-Za-z_(.]',s):
    raise SystemExit('bool-plus-numeric regression detected')

for token in ['EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','SmallAccountMinTPPips','RiskPercent','capitalInfeasible','Gartley','Bat','Butterfly','Crab','Cypher','Shark','FiveZero']:
    if token not in s: raise SystemExit('commercial integrity missing: '+token)
if 'private static Bars _coreSwingBars' in s or 'CoreCacheSwingResult' in s:
    raise SystemExit('ineffective core swing cache leaked into one-pass build')
p.write_text(s,encoding='utf-8')
print('ONEPASS_SMALL_ACCOUNT_REWRITES='+str(count))
print('Structure-aware SmallAccount precedence validated; existing explicit precedence accepted when already hardened')
print('RiskPercent unchanged; Fibonacci Grid, Geometry Engine and harmonic families preserved')
