"""V74-R16 strict microstructure observation boundary."""
import base64, datetime as dt, gzip, hashlib, math
from pathlib import Path
import numpy as np
from v74_r15_contract import validate_sidecar, ContractError

INNER='[V74-R16-MICRO]'
FRAME='[V74-R16-FRAME]'
SCHEMA='V74_R16_MICRO_V1'
LENGTH=24
CHANNELS=18
STATIC=6

def _ts(s):
    try:
        x=dt.datetime.strptime(s,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc)
        if x.second: raise ValueError()
        return x
    except Exception as e:
        raise ContractError('R16 invalid UTC completed-minute timestamp') from e

def parse_micro(line):
    try:
        payload=line.split(INNER,1)[1].strip()
        parts=[v.split('=',1) for v in payload.split()]
        kv=dict(parts)
        expected={'schema','setup','bar','anchor','index','decision','times','static','values'}
        if len(kv)!=len(parts) or set(kv)!=expected or kv['schema']!=SCHEMA:
            raise ContractError('R16 inner fields/schema')
        bar,anchor,index=(int(kv[k]) for k in ('bar','anchor','index'))
        if anchor<0 or index<32 or bar<0 or index-anchor!=bar:
            raise ContractError('R16 index/anchor mismatch')
        decision=_ts(kv['decision'])
        times=[_ts(x) for x in kv['times'].split(',')]
        if len(times)!=LENGTH or times[-1]!=decision or any(a>=b for a,b in zip(times,times[1:])):
            raise ContractError('R16 time order/decision mismatch')
        static=[float(x) for x in kv['static'].split(',')]
        values=[[float(x) for x in cell.split(',')] for cell in kv['values'].split(';')]
        if len(static)!=STATIC or not all(math.isfinite(x) for x in static):
            raise ContractError('R16 static vector')
        if static[0]<0 or static[1]<0 or abs(static[2]**2+static[3]**2-1)>1e-5:
            raise ContractError('R16 spread/session contract')
        if len(values)!=LENGTH or any(len(v)!=CHANNELS for v in values):
            raise ContractError('R16 micro shape')
        if not all(math.isfinite(x) for row in values for x in row):
            raise ContractError('R16 nonfinite micro')
        return {'setup':kv['setup'],'bar':bar,'anchor':anchor,'index':index,'decision':decision,
                'times':times,'static':static,'values':values}
    except ContractError:
        raise
    except Exception as e:
        raise ContractError('R16 malformed micro') from e

def parse_frame(line):
    try:
        parts=[x.split('=',1) for x in line.split(FRAME,1)[1].strip().split()]
        kv=dict(parts)
        if len(kv)!=len(parts) or set(kv)!={'schema','setup','bar','sha256','data'} or kv['schema']!='V74_R16_MICRO_V2':
            raise ContractError('R16 envelope fields')
        compressed=base64.b64decode(kv['data'],validate=True)
        if len(compressed)>7000: raise ContractError('R16 compressed size')
        raw=gzip.decompress(compressed)
        if len(raw)>24000 or hashlib.sha256(raw).hexdigest()!=kv['sha256']:
            raise ContractError('R16 checksum/size')
        z=parse_micro(raw.decode('utf-8',errors='strict'))
        if z['setup']!=kv['setup'] or z['bar']!=int(kv['bar']):
            raise ContractError('R16 envelope identity')
        return z
    except ContractError:
        raise
    except Exception as e:
        raise ContractError('R16 corrupt frame') from e

def load_micro(root,windows):
    result={};total=0
    for p in sorted(Path(root).rglob('*-R15.log')):
        found=[w for w in windows if w in str(p)]
        if len(found)!=1: continue
        seal=validate_sidecar(p,require_hash=False)
        count=0
        with p.open(errors='strict') as f:
            for line in f:
                if FRAME not in line: continue
                z=parse_frame(line);key=(found[0],z['setup'],z['bar'])
                if key in result: raise ContractError('R16 duplicate decision frame')
                result[key]=z;count+=1
        if count!=seal['frames']:
            raise ContractError('R16 frame census mismatch with sealed decision frames')
        total+=count
    if not total: raise ContractError('R16 telemetry absent: semantic regeneration required')
    return result

def action_native_encode(z,sign):
    if sign not in (-1,1): raise ContractError('R16 action sign')
    v=np.asarray(z['values'],dtype=float)
    if v.shape!=(LENGTH,CHANNELS) or not np.isfinite(v).all():
        raise ContractError('R16 encoder input')
    a=v.copy()
    for c in (0,1,5,6,7,12,13,14,15): a[:,c]*=sign
    upper=v[:,3].copy();lower=v[:,4].copy()
    a[:,3]=lower if sign>0 else upper
    a[:,4]=upper if sign>0 else lower
    pieces=[a[-1],a[-3:].mean(0),a[-5:].mean(0),a[-10:].mean(0),
            a[-5:].std(0),a[-10:].std(0),a[-10:].min(0),a[-10:].max(0)]
    stat=np.asarray(z['static'],dtype=float)
    out=np.concatenate(pieces+[stat])
    if not np.isfinite(out).all(): raise ContractError('R16 encoded nonfinite')
    return out,a

def first_passage_prior(native,route_state,rr):
    if native.shape!=(LENGTH,CHANNELS): raise ContractError('R16 prior shape')
    if len(route_state)!=80: raise ContractError('R16 route state width')
    risk_atr=max(.20,min(4.0,float(route_state[57])*4.0))
    mu=float(np.mean(native[-5:,0]))/risk_atr
    sigma=max(.015,float(np.std(native[-10:,0]))/risk_atr)
    a=1.0;b=max(2.0,float(rr));s2=sigma*sigma
    if abs(mu)<1e-7: return a/(a+b)
    x1=max(-50.0,min(50.0,-2.0*mu*a/s2))
    x2=max(-50.0,min(50.0,-2.0*mu*(a+b)/s2))
    num=1.0-math.exp(x1);den=1.0-math.exp(x2)
    p=a/(a+b) if abs(den)<1e-12 else num/den
    return max(.005,min(.995,float(p)))
