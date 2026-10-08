"""Strict R15 observation boundary. No outcome-derived fields are accepted."""
import datetime as dt
import math
from pathlib import Path
from v74_model_lib import event_identity
SCHEMA='V74_R15_TRAJECTORY_V1'
LENGTH=32
CHANNELS=18
MARKER='[V74-R15-TRAJECTORY]'
class ContractError(ValueError): pass

def timestamp(s):
    try:
        value=dt.datetime.strptime(s,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc)
        if value.second: raise ValueError()
        return value
    except (ValueError,TypeError): raise ContractError('invalid UTC completed-minute timestamp')

def parse_trajectory(line):
    try:
        payload=line.split(MARKER,1)[1].strip()
        parts=[v.split('=',1) for v in payload.split()]
        if any(len(v)!=2 for v in parts): raise ContractError('malformed token')
        kv=dict(parts)
        expected={'schema','setup','bar','anchor','index','decision','times','spread','sin','cos','values'}
        if len(kv)!=len(parts) or set(kv)!=expected or kv['schema']!=SCHEMA:
            raise ContractError('missing, duplicate, unknown field or schema')
        bar,anchor,index=(int(kv[k]) for k in ('bar','anchor','index'))
        if anchor<0 or index<32 or bar<0 or index-anchor!=bar: raise ContractError('decision index/anchor mismatch')
        identity=event_identity(kv['setup'])
        if len(identity.split('|'))!=3: raise ContractError('invalid event identity')
        decision=timestamp(kv['decision']);times=[timestamp(s) for s in kv['times'].split(',')]
        if len(times)!=LENGTH or times[-1]!=decision or any(a>=b for a,b in zip(times,times[1:])):
            raise ContractError('timestamp length/order/decision mismatch')
        values=[[float(v) for v in cell.split(',')] for cell in kv['values'].split(';')]
        static=[float(kv[k]) for k in ('spread','sin','cos')]
        if len(values)!=LENGTH or any(len(v)!=CHANNELS for v in values) or not all(math.isfinite(x) for v in values for x in v):
            raise ContractError('trajectory length or nonfinite values')
        if not all(math.isfinite(x) for x in static) or static[0]<0 or abs(static[1]**2+static[2]**2-1)>1e-6:
            raise ContractError('spread/session phase invalid')
        phase=2*math.pi*(decision.hour*60+decision.minute)/1440
        if abs(static[1]-math.sin(phase))>1e-6 or abs(static[2]-math.cos(phase))>1e-6:
            raise ContractError('session timestamp mismatch')
        return {'setup':kv['setup'],'event':identity,'bar':bar,'decision':decision,'times':times,'values':values,'static':static,'anchor':anchor,'index':index}
    except (KeyError,IndexError,ValueError) as e:
        if isinstance(e,ContractError): raise
        raise ContractError('malformed trajectory') from e

def load_trajectories(root,windows):
    # Strict caller-controlled year paths. Do not even open excluded year logs.
    result={}
    for p in sorted(Path(root).rglob('*.log')):
        found=[w for w in windows if w in str(p)]
        if len(found)!=1: continue
        window=found[0]
        with p.open(errors='strict') as f:
            for line in f:
                if MARKER not in line: continue
                z=parse_trajectory(line);key=(window,z['setup'],z['bar'])
                if key in result and result[key]!=z: raise ContractError('conflicting duplicate decision')
                result[key]=z
    if not result: raise ContractError('no R15 telemetry: old semantic cache rejected')
    return result

def observation(z,static):
    """Exact allowlist, deliberately drops any training labels on callers' rows."""
    if len(static)!=53 or not all(math.isfinite(float(x)) for x in static):
        raise ContractError('event-static feature contract')
    return {'values':z['values'],'static':list(static)+z['static'],'bar':z['bar']}
