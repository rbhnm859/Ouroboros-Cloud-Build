#!/usr/bin/env python3
"""V74-R16 research-only first-passage microstructure admission."""
import argparse,datetime as dt,json,math,pathlib,time
import numpy as np
from v74_model_lib import load_rows,event_identity,metrics,FAMILIES,FEATURE_NAMES
from v74_r15_contract import audit_raw_outcomes,ContractError
from v74_r15_supply import make_samples,key
from v74_r16_contract import load_micro,action_native_encode,first_passage_prior
from v74_r16_model import FirstPassageResidual

RESEARCH=[f'Y{y}' for y in range(2016,2021)]
K=275
DIR=FEATURE_NAMES.index('direction_buy')

def route_rr(s):
    r=s['row'];src=s['source'];b=s['base']
    if src in ('EARLY','LATE'):
        bank='sequential' if src=='EARLY' else 'late_auction'
        return float(r[bank+'_rr'][key(s['m'],b,s['fraction'])])
    prefix={'SURVIVAL':'survival_fresh','REACTION':'reaction_commit','FAILURE':'failure_continuation'}[src]
    if b.startswith('SURVIVAL_PROOF_'): prefix='high_conviction';rk=b[len('SURVIVAL_PROOF_'):]
    elif src=='SURVIVAL': rk=b[len('SURVIVAL_'):]
    elif src=='REACTION': rk=b[len('REACTION_'):]
    else: rk='FC230'
    return float(r[prefix+'_rr'][rk])

def action_state(s):
    r=s['row'];src=s['source'];base=s['base']
    if src in ('EARLY','LATE'):
        bank='sequential_entry_state' if src=='EARLY' else 'late_auction_entry_state';route=key(s['m'],base,s['fraction'])
    elif src=='SURVIVAL' and base.startswith('SURVIVAL_PROOF_'):
        bank='high_conviction_entry_state';route=base[len('SURVIVAL_PROOF_'):]
    elif src=='SURVIVAL': bank='survival_fresh_entry_state';route=base[len('SURVIVAL_'):]
    elif src=='REACTION': bank='reaction_commit_entry_state';route=base[len('REACTION_'):]
    else: bank='failure_continuation_entry_state';route='FC230'
    v=r.get(bank,{}).get(route)
    if v is None or len(v)!=80 or not all(math.isfinite(float(x)) for x in v):
        raise ContractError('R16 missing/nonfinite action-local state '+bank+'/'+route)
    return np.asarray(v,dtype=np.float32)

def sign_for(s):
    sign=1 if float(s['row']['features'][DIR])>=.5 else -1
    if s['source']=='FAILURE': sign=-sign
    return sign

def feature_blocks(s,z):
    rr=route_rr(s);state=action_state(s);micro,native=action_native_encode(z,sign_for(s))
    prior=first_passage_prior(native,state,rr)
    src=np.array([int(s['source']==x) for x in ('EARLY','LATE','SURVIVAL','REACTION','FAILURE')],dtype=float)
    mech=np.array([int(s['action']=='CONTINUATION'),rr/4.0,s['bar']/180.0],dtype=float)
    fam=np.array([int(s['family']==f) for f in FAMILIES],dtype=float)
    harmonic=np.asarray(s['row']['features'],dtype=float)
    metadata=np.r_[src,mech,fam]
    route_geometry=state[56:64]
    return {
      'full':np.r_[harmonic,state,micro,metadata,prior],
      'no_micro':np.r_[harmonic,route_geometry,metadata,prior],
      'no_harmonic':np.r_[state,micro,src,mech,prior],
      'no_physics':np.r_[harmonic,state,micro,metadata],
    },prior

def prepare(root):
    audit_raw_outcomes(root,RESEARCH)
    bank=load_micro(root,RESEARCH)
    rows=load_rows(root,RESEARCH,strict_r15=True)
    samples=make_samples(rows)
    out=[];seen=set()
    for s in samples:
        event=(s['window'],event_identity(s['setup']))
        ident=(*event,s['bar'],s['source'],s['base'],s['route'],s.get('fraction',''))
        if ident in seen: continue
        seen.add(ident)
        z=bank.get((s['window'],s['setup'],s['bar']))
        if z is None: raise ContractError('R16 missing micro frame '+str(ident))
        rr=route_rr(s)
        if not math.isfinite(rr) or rr<2.0: raise ContractError('R16 illegal RR')
        blocks,prior=feature_blocks(s,z)
        out.append({'event':event,'year':s['window'],'family':s['family'],'decision':z['decision'],
                    'bar':s['bar'],'bars':s['bars'],'source':s['source'],'route':s['route'],
                    'r':float(s['y']),'win':float(s['y']>0),'rr':rr,'prior':prior,'x':blocks})
    if not out: raise ContractError('R16 empty action supply')
    return out

def train_indices(samples,years):
    boundary=int(max(years)[1:])+1
    end=dt.datetime(boundary,1,1,tzinfo=dt.timezone.utc)
    return np.array([i for i,s in enumerate(samples) if s['year'] in years and
                     s['decision'].year==int(s['year'][1:]) and
                     s['decision']+dt.timedelta(minutes=s['bars'])<end],dtype=int)

def fit(samples,years,kind,shuffle=False):
    ix=train_indices(samples,years)
    if len(ix)<100: raise ContractError('R16 insufficient training support')
    x=np.array([samples[i]['x'][kind] for i in ix],dtype=np.float32)
    yw=np.array([samples[i]['win'] for i in ix]);rv=np.array([samples[i]['r'] for i in ix])
    prior=np.array([samples[i]['prior'] for i in ix])
    if shuffle:
        rng=np.random.default_rng(16074);p=rng.permutation(len(ix));yw=yw[p];rv=rv[p]
    use_physics=(kind!='no_physics') and not shuffle
    return FirstPassageResidual(use_physics=use_physics).fit(
        x,yw,rv,prior,[samples[i]['year'] for i in ix],[samples[i]['event'] for i in ix])

def predict(model,samples,year,kind):
    ix=np.array([i for i,s in enumerate(samples) if s['year']==year],dtype=int)
    if not len(ix): raise ContractError('R16 empty forward year')
    x=np.array([samples[i]['x'][kind] for i in ix],dtype=np.float32)
    prior=np.array([samples[i]['prior'] for i in ix])
    return ix,model.predict(x,prior)

def representatives(samples,ix,pred):
    best={}
    for j,i in enumerate(ix):
        s=samples[i];k=s['event'];score=float(pred['score'][j])
        item=(score,-s['bar'],s['route'])
        if k not in best or item>best[k][0]: best[k]=(item,j,i)
    return sorted(best.values(),key=lambda z:(-z[0][0],z[2]))

def wilson_lower(w,n,z=1.645):
    if n<=0:return 0.0
    p=w/n;d=1+z*z/n
    return (p+z*z/(2*n)-z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/d

def topk(samples,reps,pred=None):
    r=reps[:K];selected=[samples[x[2]] for x in r]
    wins=sum(s['win'] for s in selected);n=len(selected)
    m=metrics([{'r':s['r'],'bars':s['bars']} for s in selected])
    support=None
    if pred is not None and r: support=float(np.median([pred['support'][x[1]] for x in r]))
    return {'n':n,'precision':wins/n if n else 0.0,'precision_lcb90':wilson_lower(wins,n),
            'fdr':1-wins/n if n else 1.0,'support_median':support,'metrics':m}

def fold(samples,test):
    train=[y for y in RESEARCH if y<test]
    results={}
    for kind in ('full','no_micro','no_harmonic','no_physics'):
        model=fit(samples,train,kind);ix,p= predict(model,samples,test,kind);reps=representatives(samples,ix,p)
        results[kind]={'top275':topk(samples,reps,p),'dro_weights':model.dro_weights,'training_years':train}
    neg=fit(samples,train,'full',shuffle=True);ix,npred=predict(neg,samples,test,'full')
    results['permutation_control']=topk(samples,representatives(samples,ix,npred),npred)
    full=results['full']['top275'];abl=max(results[k]['top275']['precision'] for k in ('no_micro','no_harmonic','no_physics'))
    results['ablation_lift']=full['precision']-abl
    return results

def gate_fold(f):
    z=f['full']['top275'];m=z['metrics']
    return bool(z['n']==K and z['precision']>=.72 and z['fdr']<=.28 and z['precision_lcb90']>=.66 and
                m['mean_r']>=.90 and m['pf_r']>=3.30 and m['average_rr']>=2.30 and m['lcb_r']>0 and
                (z['support_median'] is None or z['support_median']>=.90) and
                f['ablation_lift']>=.02 and f['permutation_control']['precision']<.45)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('out');args=ap.parse_args()
    start=time.monotonic();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    samples=prepare(args.root);folds={}
    for test in ('Y2018','Y2019','Y2020'):
        folds[test]=fold(samples,test)
        print('[R16-RESEARCH-FOLD]',test,json.dumps(folds[test],allow_nan=False),flush=True)
    passed=all(gate_fold(f) for f in folds.values())
    worst=min(f['full']['top275']['precision'] for f in folds.values())
    blocker='RESEARCH_PRE_GATE_PASS__BURNED_REGENERATION_AUTHORIZED' if passed else (
        'A_NEW_MICROSTRUCTURE_INFORMATION_INSUFFICIENT' if worst<.45 else
        'B_FIRST_PASSAGE_LEARNER_OR_ROBUSTNESS_INSUFFICIENT')
    manifest={'architecture':'V74_R16_MNFPA','research_pre_gate':passed,'research_information_pass':passed,
              'burned_authorized':passed,'burned_status':'NOT_RUN','physical_pass':None,
              'alpha_gate':False,'v74_gate':False,'execution_semantics_ready':False,
              'promotion_blocker':blocker,'folds':folds,'research_years':RESEARCH,
              'validation_used':False,'fresh_used':False,'burned_used':False,
              'legal_actions':len(samples),'runtime_seconds':round(time.monotonic()-start,3),
              'gate_contract':{'k':K,'precision':.72,'fdr_max':.28,'precision_lcb90':.66,
                               'mean_r':.90,'pf_r':3.30,'avg_rr':2.30,'lcb_r_positive':True,
                               'ablation_lift':.02,'permutation_precision_max':.45}}
    (out/'V74_R16_RESEARCH_MANIFEST.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    (out/'research_pass.txt').write_text(('true' if passed else 'false')+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='folds'},indent=2),flush=True)

if __name__=='__main__':
    try: main()
    except Exception as exc:
        import sys
        if len(sys.argv)>2:
            out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
            fail={'architecture':'V74_R16_MNFPA','research_status':'NOT_RUN_TELEMETRY_OR_ENGINEERING_FAIL',
                  'research_pre_gate':False,'burned_authorized':False,'burned_status':'NOT_RUN',
                  'physical_pass':None,'alpha_gate':False,'v74_gate':False,
                  'promotion_blocker':type(exc).__name__+': '+str(exc),
                  'validation_used':False,'fresh_used':False,'burned_used':False}
            (out/'V74_R16_RESEARCH_MANIFEST.json').write_text(json.dumps(fail,indent=2)+'\n')
            (out/'research_pass.txt').write_text('false\n')
        raise
