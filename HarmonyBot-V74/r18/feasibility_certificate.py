#!/usr/bin/env python3
"""R18 research-only, fail-closed event feasibility certificate.

Consumes pinned 2016-2020 R18 semantic shadow outcome artifacts. This tests a
NECESSARY condition, not a sufficient or deployable oracle. No brokerage calls,
protected OOF, optimizer, trade placement, or workflow dispatch.
"""
from __future__ import annotations
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import zipfile

SOURCE_RUN = 37824462498
SOURCE_HEAD = '61a164b453ca3e65b1670050ea2dd30ec7b5592d'
EXPECTED_SHA256 = {
    2016: '9a26b45dac0a5bc22b4a43eedf0952ed2da532924ba1674dd9582a7a0d0cfb67',
    2017: '000b71c1daecf71a9b2553152ab6a41cb653a548e9112a77b9e885cc3468d8aa',
    2018: '578c95a7066c5167b0fe73aff5155125ec4346773ba7e0eb85cc836f5b29091e',
    2019: 'a6ee2899e43eb1a098645e21a5ec5259816426b722bcdd84d1caa1fd60e9fdba',
    2020: '4e2610491a0ee0826ef0dfc3051d551156463c908f735e12f4a25d99d08c4efa',
}
TAG = '[V74-R18-OUTCOME] '
CAUSES = frozenset(('TP_FIRST', 'SL_FIRST', 'STRUCTURAL_INVALIDATION',
    'TIME_EXPIRE', 'SESSION_EXPIRE', 'PARENT_TARGET_TERMINATION',
    'CENSORED', 'NO_FILL_SESSION', 'NO_FILL_SPREAD', 'NO_FILL_GEOMETRY',
    'NO_FILL_MIN_STOP', 'RUNTIME_DIVERGENCE'))
REQUIRED = frozenset(('schema','setup','source','route','cause','executed',
    'decision','exit','dir','fill','stop','target','risk','gross_r','net_r',
    'extra_cost_pips','min_cap_feasible'))

class IntegrityError(ValueError):
    pass

def sha256_file(path):
    dig = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            dig.update(chunk)
    return dig.hexdigest()

def parse_line(s):
    if TAG not in s: return None
    body = s.split(TAG, 1)[1]
    pairs = [tok.split('=',1) for tok in body.strip().split()]
    if any(len(kv)!=2 for kv in pairs): raise IntegrityError('malformed outcome fields')
    data = dict(pairs)
    if len(data)!=len(pairs) or not REQUIRED <= data.keys():
        raise IntegrityError('duplicate/missing outcome field')
    if data['schema']!='V74_R18_OUTCOME_V1' or data['cause'] not in CAUSES:
        raise IntegrityError('unknown outcome schema/cause')
    if data['dir'] not in ('BUY','SELL') or data['executed'] not in ('true','false'):
        raise IntegrityError('unknown direction/execution flag')
    if data['min_cap_feasible'] not in ('true','false'):
        raise IntegrityError('invalid minimum-capital flag')
    try:
        decision=dt.datetime.strptime(data['decision'],'%Y-%m-%dT%H:%M:%S.%fZ')
        exit_at=dt.datetime.strptime(data['exit'],'%Y-%m-%dT%H:%M:%S.%fZ')
        vals={k:float(data[k]) for k in ('fill','stop','target','risk','gross_r','net_r','extra_cost_pips')}
    except (ValueError,OverflowError) as exc:
        raise IntegrityError('invalid outcome timestamp/number') from exc
    if any(not math.isfinite(x) for x in vals.values()) or exit_at < decision:
        raise IntegrityError('invalid outcome time/numeric finiteness')
    executed=data['executed']=='true'
    nofill=data['cause'].startswith('NO_FILL')
    if executed == nofill or data['cause']=='RUNTIME_DIVERGENCE':
        raise IntegrityError('outcome execution/cause contradiction')
    setup=data['setup'].split('|')
    if len(setup)<3: raise IntegrityError('invalid canonical event setup')
    event='|'.join((setup[0],setup[1],setup[-1]))
    if executed:
        if vals['risk']<=0 or vals['extra_cost_pips']<0:
            raise IntegrityError('non-positive risk / negative costs')
        fill,stop,target=vals['fill'],vals['stop'],vals['target']
        if not math.isclose(abs(fill-stop),vals['risk'],rel_tol=1e-8,abs_tol=1e-7):
            raise IntegrityError('risk/stop price divergence')
        if data['dir']=='BUY' and not stop<fill<target:
            raise IntegrityError('invalid BUY target geometry')
        if data['dir']=='SELL' and not target<fill<stop:
            raise IntegrityError('invalid SELL target geometry')
        # Use recorded cost in R rather than guessing broker pip size.
        cost_r=vals['gross_r']-vals['net_r']
        if cost_r < -1e-7: raise IntegrityError('negative effective cost')
        target_r=abs(target-fill)/vals['risk']-max(0.0,cost_r)
    else:
        target_r=None
    return {'event':event,'action':(data['setup'],data['source'],data['route']),
        'executed':executed,'cause':data['cause'], 'net_r':vals['net_r'],
        'net_target_rr':target_r,'min_cap':data['min_cap_feasible']=='true',
        'decision':decision,'exit':exit_at}

def audit_year(path, year, expected_digest, n_required=250, win_rate=.70, min_net_rr=2.0):
    if sha256_file(path)!=expected_digest:
        raise IntegrityError(f'Y{year}: artifact digest mismatch')
    seen=set(); cause_counts=Counter(); best={}; any_executed=set(); all_positive=set();
    counters=Counter()
    with zipfile.ZipFile(path) as z:
        logs=[n for n in z.namelist() if n.endswith('-R15.log')]
        if len(logs)!=1: raise IntegrityError(f'Y{year}: missing/ambiguous canonical R15 outcome log')
        custody=json.loads(z.read('R18_SEMANTIC_CUSTODY.json'))
        if custody.get('window')!=f'Y{year}' or custody.get('schema')!='V74_R18_SEMANTIC_CUSTODY_V1' or custody.get('burned_used') or custody.get('fresh_used') or custody.get('validation_used'):
            raise IntegrityError(f'Y{year}: custody mismatch or protected data used')
        with z.open(logs[0]) as stream:
            for raw in stream:
                if b'[V74-R18-OUTCOME]' not in raw: continue
                row=parse_line(raw.decode('utf-8','strict'))
                if not row: continue
                if row['action'] in seen: raise IntegrityError(f'Y{year}: repeated action identity')
                seen.add(row['action']);counters['total_outcomes']+=1
                cause_counts[row['cause']]+=1
                if not row['executed']:
                    counters['not_filled']+=1;continue
                counters['shadow_executed']+=1;any_executed.add(row['event'])
                if row['net_r']>0: all_positive.add(row['event'])
                if not row['min_cap']:
                    counters['min_cap_proxy_infeasible']+=1;continue
                if row['net_target_rr']+1e-10<min_net_rr:
                    counters['net_rr_below_minimum']+=1;continue
                counters['eligible_shadow_actions']+=1
                prior=best.get(row['event'])
                if prior is None or row['net_r']>prior['net_r']:
                    best[row['event']]=row
    if not counters['total_outcomes']: raise IntegrityError(f'Y{year}: empty outcome artifact')
    won=sum(v['net_r']>0 for v in best.values())
    need_wins=math.ceil(n_required*win_rate-1e-10)
    n_events=len(best)
    return {
      'year':year,'sha256':expected_digest,'source_run':SOURCE_RUN,
      'source_head':SOURCE_HEAD,'observed_outcomes':counters['total_outcomes'],
      'cause_counts':dict(sorted(cause_counts.items())),
      'shadow_executed_actions':counters['shadow_executed'],
      'unfiltered_executed_events':len(any_executed),
      'unfiltered_positive_events':len(all_positive),
      'shadow_eligible_actions':counters['eligible_shadow_actions'],
      'shadow_eligible_events':n_events,
      'shadow_positive_events_event_oracle':won,
      'minimum_trades':n_required,'required_winning_events':need_wins,
      'trades_shortfall_lower_bound':max(0,n_required-n_events),
      'winners_shortfall_lower_bound':max(0,need_wins-won),
      'unconstrained_optimistic_win_fraction_at_n_required':min(won,n_required)/n_required,
      'can_meet_necessary_count_conditions':n_events>=n_required and won>=need_wins,
      'filters':dict(sorted(counters.items())),
      'limitations':['shadow fill is not verified broker execution',
        'min_cap is the R18 runtime proxy, not a proven volume+margin gate',
        'perfect foresight best-route per event, not a causal policy',
        'basket overlaps and pending exposure ignored: optimistic bound',
        'new harmonic-native actions not included: no global impossibility claim']
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--artifact-dir',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    if args.output.is_dir(): raise IntegrityError('output must be a file')
    annual=[]
    for year, digest in EXPECTED_SHA256.items():
        src=args.artifact_dir/f'v74-r18-semantic-Y{year}.zip'
        if not src.is_file(): raise IntegrityError(f'Y{year}: pinned artifact absent')
        annual.append(audit_year(src,year,digest))
    result={'schema':'V74_R18_EVENT_FEASIBILITY_CERT_V1',
      'scope':'2016-2020; existing pinned R18 shadow actions ONLY',
      'audit_type':'necessary-condition certificate; not a backtest/alpha gate',
      'protected_years_used':False,'burned_status':'NOT_RUN',
      'alpha_gate':False,'v74_gate':False,'promotion_authorized':False,
      'all_years_pass_necessary_conditions':all(y['can_meet_necessary_count_conditions'] for y in annual),
      'years':annual}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(args.output),'rows':[(y['year'],y['shadow_eligible_events'],y['shadow_positive_events_event_oracle']) for y in annual],
       'necessary_conditions_pass':result['all_years_pass_necessary_conditions'],'promotion_authorized':False}))

if __name__=='__main__': main()
