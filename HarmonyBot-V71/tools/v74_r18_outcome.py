"""V74-R18 strict execution-semantic outcome parser."""
import datetime as dt
import math
from collections import Counter,defaultdict
from pathlib import Path
from v74_r15_contract import validate_sidecar,ContractError

TAG='[V74-R18-OUTCOME]'
SCHEMA='V74_R18_OUTCOME_V1'
SOURCES={'EARLY','LATE','SURVIVAL','REACTION','FAILURE'}
EXEC_CAUSES={
    'TP_FIRST','SL_FIRST','STRUCTURAL_INVALIDATION',
    'TIME_EXPIRE','SESSION_EXPIRE','PARENT_TARGET_TERMINATION','CENSORED'
}
NOFILL_CAUSES={'NO_FILL_SESSION','NO_FILL_SPREAD','NO_FILL_GEOMETRY','NO_FILL_MIN_STOP'}
ALL_CAUSES=EXEC_CAUSES|NOFILL_CAUSES|{'RUNTIME_DIVERGENCE'}

def _utc(s):
    try:
        z=dt.datetime.strptime(s,'%Y-%m-%dT%H:%M:%S.%fZ')
        return z.replace(tzinfo=dt.timezone.utc)
    except Exception as exc:
        raise ContractError('R18 invalid UTC timestamp') from exc

def _bool(s):
    if s=='true':return True
    if s=='false':return False
    raise ContractError('R18 invalid bool')

def parse_outcome(line):
    try:
        payload=line.split(TAG,1)[1].strip()
        parts=[x.split('=',1) for x in payload.split()]
        kv=dict(parts)
        expected={
            'schema','setup','family','source','route','dir','decision','exit','cause','executed',
            'planned_entry','fill','stop','target','exit_px','risk','gross_r','net_r','planned_rr',
            'entry_spread_pips','extra_cost_pips','min_cap_feasible'
        }
        if len(parts)!=len(kv) or set(kv)!=expected or kv['schema']!=SCHEMA:
            raise ContractError('R18 outcome fields/schema')
        if kv['source'] not in SOURCES or kv['cause'] not in ALL_CAUSES:
            raise ContractError('R18 unknown source/cause')
        if kv['dir'] not in ('BUY','SELL'):
            raise ContractError('R18 invalid direction')
        executed=_bool(kv['executed'])
        min_cap=_bool(kv['min_cap_feasible'])
        decision=_utc(kv['decision']);exit_at=_utc(kv['exit'])
        if exit_at<decision: raise ContractError('R18 exit before decision')
        nums={}
        for k in ('planned_entry','fill','stop','target','exit_px','risk','gross_r','net_r',
                  'planned_rr','entry_spread_pips','extra_cost_pips'):
            nums[k]=float(kv[k])
            if not math.isfinite(nums[k]):raise ContractError('R18 nonfinite '+k)
        if nums['risk']<0 or nums['entry_spread_pips']<0 or nums['extra_cost_pips']<0:
            raise ContractError('R18 negative risk/cost')
        if kv['cause']=='RUNTIME_DIVERGENCE':
            raise ContractError('R18 runtime semantic divergence')
        if executed and kv['cause'] in NOFILL_CAUSES:
            raise ContractError('R18 executed no-fill contradiction')
        if (not executed) and kv['cause'] not in NOFILL_CAUSES:
            raise ContractError('R18 non-executed outcome without no-fill cause')
        if not executed and abs(nums['net_r'])>1e-12:
            raise ContractError('R18 no-fill has nonzero net R')
        if executed and nums['risk']<=0:
            raise ContractError('R18 executed zero-risk action')
        return {
            'setup':kv['setup'],'family':kv['family'],'source':kv['source'],'route':kv['route'],
            'direction':kv['dir'],'decision':decision,'exit':exit_at,'cause':kv['cause'],
            'executed':executed,'min_cap_feasible':min_cap,**nums
        }
    except ContractError:
        raise
    except Exception as exc:
        raise ContractError('R18 malformed outcome') from exc

def load_outcomes(root,windows):
    out={};stats={w:{
        'outcomes':0,'executed':0,'nofill':0,'censored':0,'tp':0,'sl':0,
        'expiry':0,'structural':0,'parent_termination':0,'min_cap_infeasible':0
    } for w in windows}
    seen_sidecars=set()
    for p in sorted(Path(root).rglob('*-R15.log')):
        matches=[w for w in windows if w in str(p)]
        if len(matches)!=1: continue
        w=matches[0];validate_sidecar(p,require_hash=False);seen_sidecars.add(w)
        with p.open(errors='strict') as f:
            for line in f:
                if TAG not in line:continue
                z=parse_outcome(line)
                key=(w,z['setup'],z['source'],z['route'])
                if key in out:raise ContractError('R18 duplicate outcome '+repr(key))
                out[key]=z;s=stats[w];s['outcomes']+=1
                if z['executed']:s['executed']+=1
                else:s['nofill']+=1
                if not z['min_cap_feasible']:s['min_cap_infeasible']+=1
                c=z['cause']
                if c=='TP_FIRST':s['tp']+=1
                elif c=='SL_FIRST':s['sl']+=1
                elif c=='STRUCTURAL_INVALIDATION':s['structural']+=1
                elif c in ('TIME_EXPIRE','SESSION_EXPIRE'):s['expiry']+=1
                elif c=='PARENT_TARGET_TERMINATION':s['parent_termination']+=1
                elif c=='CENSORED':s['censored']+=1
    missing=[w for w in windows if w not in seen_sidecars]
    if missing:raise ContractError('R18 missing annual sidecars '+','.join(missing))
    if not out:raise ContractError('R18 outcome telemetry absent')
    return out,stats

def semantic_class(cause):
    if cause=='TP_FIRST':return 0
    if cause in ('SL_FIRST','STRUCTURAL_INVALIDATION'):return 1
    if cause in ('TIME_EXPIRE','SESSION_EXPIRE','PARENT_TARGET_TERMINATION'):return 2
    return None

def executable_for_model(z):
    return bool(z['executed'] and semantic_class(z['cause']) is not None)

def cause_distribution(outcomes):
    c=Counter(z['cause'] for z in outcomes.values())
    return dict(sorted(c.items()))
