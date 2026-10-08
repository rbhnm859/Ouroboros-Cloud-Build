"""V74-R17 strict tick-state observation and custody boundary."""
import base64,datetime as dt,gzip,hashlib,json,math,re
from pathlib import Path
import numpy as np
from v74_r15_contract import validate_sidecar,ContractError

INNER='[V74-R17-TICK]'
FRAME='[V74-R17-FRAME]'
SCHEMA='V74_R17_TICK_V1'
MINUTES=12
CHANNELS=28
STATIC=9
HEX64=re.compile(r'^[0-9a-f]{64}$')

def _ts(s):
    try:
        return dt.datetime.strptime(s,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc)
    except Exception as e:
        raise ContractError('R17 invalid UTC timestamp') from e

def parse_inner(line):
    try:
        payload=line.split(INNER,1)[1].strip()
        parts=[v.split('=',1) for v in payload.split()]
        kv=dict(parts)
        expected={'schema','setup','bar','decision','minutes','channels','static','values'}
        if len(kv)!=len(parts) or set(kv)!=expected or kv['schema']!=SCHEMA:
            raise ContractError('R17 inner schema/fields')
        bar=int(kv['bar']);decision=_ts(kv['decision'])
        minutes=int(kv['minutes']);channels=int(kv['channels'])
        if minutes!=MINUTES or channels!=CHANNELS or bar<0:
            raise ContractError('R17 shape header')
        static=[float(x) for x in kv['static'].split(',')]
        values=[[float(x) for x in cell.split(',')] for cell in kv['values'].split(';')]
        if len(static)!=STATIC or not all(math.isfinite(x) for x in static):
            raise ContractError('R17 static contract')
        if len(values)!=MINUTES or any(len(v)!=CHANNELS for v in values):
            raise ContractError('R17 matrix shape')
        if not all(math.isfinite(x) for row in values for x in row):
            raise ContractError('R17 matrix nonfinite')
        if static[0]<0 or not (0<=static[1]<=1) or static[2]<0 or static[8]<=0:
            raise ContractError('R17 static range')
        return {'setup':kv['setup'],'bar':bar,'decision':decision,'static':static,'values':values}
    except ContractError:
        raise
    except Exception as e:
        raise ContractError('R17 malformed inner frame') from e

def parse_frame(line):
    try:
        parts=[x.split('=',1) for x in line.split(FRAME,1)[1].strip().split()]
        kv=dict(parts)
        if len(kv)!=len(parts) or set(kv)!={'schema','setup','bar','sha256','data'} or kv['schema']!='V74_R17_TICK_V2':
            raise ContractError('R17 envelope fields')
        raw=gzip.decompress(base64.b64decode(kv['data'],validate=True))
        if len(raw)>48000 or hashlib.sha256(raw).hexdigest()!=kv['sha256']:
            raise ContractError('R17 envelope checksum/size')
        z=parse_inner(raw.decode('utf-8',errors='strict'))
        if z['setup']!=kv['setup'] or z['bar']!=int(kv['bar']):
            raise ContractError('R17 envelope identity')
        return z
    except ContractError:
        raise
    except Exception as e:
        raise ContractError('R17 corrupt frame') from e

def load_tick_frames(root,windows):
    result={};stats={}
    for w in windows: stats[w]={'r15_frames':0,'r17_frames':0,'coverage':0.0}
    for p in sorted(Path(root).rglob('*-R15.log')):
        found=[w for w in windows if w in str(p)]
        if len(found)!=1: continue
        w=found[0]
        seal=validate_sidecar(p,require_hash=False)
        stats[w]['r15_frames']+=int(seal['frames'])
        with p.open(errors='strict') as f:
            for line in f:
                if FRAME not in line: continue
                z=parse_frame(line);key=(w,z['setup'],z['bar'])
                if key in result: raise ContractError('R17 duplicate tick frame')
                result[key]=z;stats[w]['r17_frames']+=1
    for w in windows:
        den=stats[w]['r15_frames']
        stats[w]['coverage']=stats[w]['r17_frames']/den if den else 0.0
        if den<=0: raise ContractError('R17 missing R15 denominator '+w)
    if not result: raise ContractError('R17 tick telemetry absent')
    return result,stats

def load_tick_custody(root,windows):
    found={}
    for p in Path(root).rglob('R17_TICK_CUSTODY.json'):
        d=json.loads(p.read_text())
        w=d.get('window')
        if w not in windows: continue
        if w in found: raise ContractError('R17 duplicate tick custody '+w)
        if d.get('data_mode')!='ticks' or d.get('source')!='ctrader_server_tick_cache':
            raise ContractError('R17 wrong data source '+str(w))
        sha=str(d.get('sha256',''))
        if not HEX64.match(sha) or int(d.get('file_count',0))<=0:
            raise ContractError('R17 invalid tick custody '+str(w))
        if d.get('validation_used') or d.get('fresh_used') or d.get('burned_used'):
            raise ContractError('R17 custody scope breach '+str(w))
        found[w]=d
    missing=[w for w in windows if w not in found]
    if missing: raise ContractError('R17 missing tick custody '+','.join(missing))
    return found

def action_native_encode(z,sign):
    if sign not in (-1,1): raise ContractError('R17 action sign')
    v=np.asarray(z['values'],dtype=float)
    if v.shape!=(MINUTES,CHANNELS) or not np.isfinite(v).all():
        raise ContractError('R17 encoder matrix')
    a=v.copy()
    for c in (4,7,9,*range(20,28)): a[:,c]*=sign
    if sign<0:
        up=a[:,11].copy();down=a[:,12].copy()
        a[:,11]=down;a[:,12]=up

    s=np.asarray(z['static'],dtype=float).copy()
    s[3]*=sign;s[6]*=sign;s[7]*=sign
    if sign<0:
        lo=s[4];hi=s[5];s[4]=-hi;s[5]=-lo

    pieces=[
        a[-1],
        a[-3:].mean(0),a[-6:].mean(0),a.mean(0),
        a[-6:].std(0),a.std(0),
        a.min(0),a.max(0),
        s
    ]
    out=np.concatenate(pieces)
    if not np.isfinite(out).all(): raise ContractError('R17 encoded nonfinite')
    return out,a

def tick_quality(frames):
    counts=[]
    for z in frames.values():
        v=np.asarray(z['values'],dtype=float)
        counts.extend(np.expm1(v[:,0]).tolist())
    if not counts:return {'median_ticks_per_minute':0.0,'p10_ticks_per_minute':0.0,'p90_ticks_per_minute':0.0}
    q=np.quantile(np.asarray(counts),[.1,.5,.9])
    return {'p10_ticks_per_minute':float(q[0]),'median_ticks_per_minute':float(q[1]),'p90_ticks_per_minute':float(q[2])}
