#!/usr/bin/env python3
"""Research-only nested expanding CTRSTA experiment. Burned paths never opened.
Precision@275 is retrospective rank information, separately reported from causal
ENTER/DEFER/REJECT scheduling. It cannot alone authorize burned evaluation.
"""
import argparse,hashlib,json,math,pathlib,time
from collections import defaultdict
import numpy as np
from sklearn.metrics import log_loss
from v74_model_lib import load_rows,load_r15_trajectories,event_identity,metrics
from v74_r15_contract import observation,ContractError,audit_raw_outcomes
from v74_r15_encoder import encode
from v74_r15_model import CTRSTA
from v74_r15_supply import make_samples,key
RESEARCH=[f'Y{y}' for y in range(2016,2021)]
K=275

def route_rr(s):
    r=s['row'];src=s['source'];b=s['base']
    if src in ('EARLY','LATE'):
        k=key(s['m'],b,s['fraction'])
        bank='sequential' if src=='EARLY' else 'late_auction'
        return float(r[bank+'_rr'][k])
    prefix={'SURVIVAL':'survival_fresh','REACTION':'reaction_commit','FAILURE':'failure_continuation'}[src]
    if b.startswith('SURVIVAL_PROOF_'):prefix='high_conviction';rk=b[len('SURVIVAL_PROOF_'):]
    elif src=='SURVIVAL':rk=b[len('SURVIVAL_'):]
    elif src=='REACTION':rk=b[len('REACTION_'):]
    else:rk='FC230'
    return float(r[prefix+'_rr'][rk])

def prepare(root):
    audit_raw_outcomes(root,RESEARCH)
    bank=load_r15_trajectories(root,RESEARCH);rows=load_rows(root,RESEARCH)
    samples=make_samples(rows)
    if not samples:raise ContractError('no research action supply')
    seen=set();result=[];encoded={}
    for s in samples:
        event=(s['window'],event_identity(s['setup']))
        # Future payoff never determines deduplication or action identity.
        identity=(*event,s['bar'],s['source'],s['base'],s['route'],s.get('fraction',''))
        if identity in seen:continue
        seen.add(identity)
        z=bank.get((s['window'],s['setup'],s['bar']))
        if z is None:raise ContractError('missing trajectory for legal action '+str(identity))
        rr=route_rr(s)
        if not math.isfinite(rr) or rr<2:raise ContractError('illegal net RR')
        ck=(s['window'],s['setup'],s['bar'])
        if ck not in encoded:
            obs=observation(z,s['row']['features'])
            encoded[ck]=(encode(obs),encode(obs,False))
        mechanism=1 if s['action']=='CONTINUATION' else 0
        cats=np.array([int(s['source']==v) for v in ('EARLY','LATE','SURVIVAL','REACTION','FAILURE')]+[mechanism,rr/4,int(s['row']['action']=='CONTINUATION')])
        # Summary ablation uses the same event static and legal action metadata.
        result.append({'event':event,'year':s['window'],'family':s['family'],'bar':s['bar'],
                       'decision':z['decision'],'mechanism':mechanism,'source':s['source'],'route':s['route'],
                       'rr':rr,'r':s['y'],'bars':s['bars'],
                       'x':np.r_[encoded[ck][0],cats].astype(np.float32),'summary':np.r_[encoded[ck][1],cats].astype(np.float32)})
    # Keep outcome labels in training target constructor only.
    groups=defaultdict(list)
    for i,s in enumerate(result):groups[s['event']].append(i)
    targets=np.zeros((len(result),10))
    for indexes in groups.values():
        for i in indexes:
            s=result[i];remaining=[j for j in indexes if result[j]['bar']>=s['bar']]
            vals=[max([result[j]['r'] for j in remaining if result[j]['mechanism']==m]+[-1]) for m in (0,1)]
            if max(vals)<=0:regime=np.array([0.,0.,1.])
            else:
                a=np.exp(np.clip(np.array([vals[0],vals[1],0.])*2,-20,20));regime=a/a.sum()
            hazards=[]
            for m in (0,1):
                actions=[j for j in remaining if result[j]['mechanism']==m]
                best=min(actions,key=lambda j:(-result[j]['r'],result[j]['bar'],result[j]['route'])) if actions else None
                hazards.append(float(best is not None and result[best]['r']>0 and result[best]['bar']==s['bar'])*regime[m])
            future=max([result[j]['r'] for j in indexes if result[j]['bar']>s['bar']]+[0.])
            # Top-tail utility target accounts for competing routes in same event.
            regret=s['r']-max(vals)
            top=float(s['r']>0)*math.exp(max(-12,regret))
            targets[i]=[*regime,*hazards,s['r'],future,float(s['r']>0),top,s['mechanism']]
    return result,targets

def fit(samples,targets,years,kind):
    ix=np.array([i for i,s in enumerate(samples) if s['year'] in years])
    if not len(ix):raise ContractError('empty training years')
    # Boundary purge: training labels must resolve before the first held-out year.
    boundary=int(max(years)[1:])+1
    ix=np.array([i for i in ix if samples[i]['decision'].year==int(samples[i]['year'][1:]) and
                 samples[i]['decision'].timestamp()+samples[i]['bars']*60 < __import__('datetime').datetime(boundary,1,1,tzinfo=__import__('datetime').timezone.utc).timestamp()])
    return CTRSTA().fit(np.array([samples[i][kind] for i in ix]),targets[ix],
                       [samples[i]['year'] for i in ix],[samples[i]['family'] for i in ix],[samples[i]['event'] for i in ix])

def predict(model,samples,year,kind):
    ix=[i for i,s in enumerate(samples) if s['year']==year]
    if not ix:raise ContractError('empty forward year')
    pred=model.predict(np.array([samples[i][kind] for i in ix]),[samples[i]['mechanism'] for i in ix],[samples[i]['family'] for i in ix])
    return ix,pred

def representatives(samples,ix,pred):
    # Inference arbitration: selects by predicted quality, never oracle outcomes.
    best={}
    for j,i in enumerate(ix):
        s=samples[i];k=s['event'];v=float(pred['score'][j])
        if k not in best or (v,-s['bar'],s['route'])>best[k][0]:best[k]=((v,-s['bar'],s['route']),j,i)
    return sorted(best.values(),key=lambda v:(-v[0][0],v[2]))

def precision(samples,reps):
    selected=[samples[v[2]] for v in reps[:K]]
    return {'n':len(selected),'precision':sum(s['r']>0 for s in selected)/len(selected) if selected else 0.,
            'fdr':sum(s['r']<=0 for s in selected)/len(selected) if selected else 1.,
            'metrics':metrics([{'r':s['r'],'bars':s['bars']} for s in selected])}

def chronological(samples,ix,pred,threshold):
    stages=defaultdict(list)
    for j,i in enumerate(ix):stages[samples[i]['decision']].append((j,i))
    used=set();selected=[];busy_until=None;decisions=defaultdict(int)
    for t,candidates in sorted(stages.items()):
        eligible=[]
        for j,i in candidates:
            s=samples[i]
            if s['event'] in used:continue
            if pred['regime'][j,2]>.65 or pred['enter'][j]<=0:decisions['REJECT']+=1;continue
            if pred['wait'][j]>pred['enter'][j]+.05:decisions['DEFER']+=1;continue
            if pred['score'][j]<threshold:decisions['REJECT']+=1;continue
            eligible.append((float(pred['score'][j]),i))
        if busy_until is not None and t<busy_until:continue
        if eligible:
            _,i=max(eligible,key=lambda v:(v[0],-v[1]));s=samples[i];used.add(s['event']);selected.append(s)
            # Conservative fixed occupancy horizon, not R/hour optimisation.
            busy_until=t+__import__('datetime').timedelta(minutes=180)
            decisions['ENTER']+=1
    return {'metrics':metrics([{'r':s['r'],'bars':s['bars']} for s in selected]),'decisions':dict(decisions),
            'occupancy_semantics':'CONSERVATIVE_FIXED_180_MINUTES__RUNTIME_PARITY_UNVERIFIED'}

def conditional_information(samples,targets,ix,pred):
    # Cross-fitted log-score gain estimates, not a proof of the true MI ceiling.
    regime=targets[ix,:3];p=np.maximum(pred['regime'],1e-9)
    labels=regime.argmax(1);events=CounterEvents(samples,ix)
    w=np.array([1/events[samples[i]['event']] for i in ix]);w/=w.sum()
    return {'regime_cross_entropy_bits':float(np.sum(w*(-np.sum(regime*np.log2(p),axis=1)))),
            'winner_conditional_cross_entropy_bits':float(np.sum(w*(-targets[ix,7]*np.log2(np.maximum(pred['p'],1e-9))-(1-targets[ix,7])*np.log2(np.maximum(1-pred['p'],1e-9))))),
            'label_distribution':{k:int((labels==m).sum()) for m,k in enumerate(('REVERSAL','CONTINUATION','NOEDGE'))}}

def CounterEvents(samples,ix):
    from collections import Counter
    return Counter(samples[i]['event'] for i in ix)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('out');args=ap.parse_args()
    start=time.monotonic();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    samples,targets=prepare(args.root);folds={};inner_records={}
    for test in ('Y2018','Y2019','Y2020'):
        train=[y for y in RESEARCH if y<test];fold={}
        for kind in ('summary','x'):
            # Nested prior-year cross-fitting sets admission threshold and uncertainty.
            inner=[];errors={0:[],1:[]}
            for val in train[1:]:
                past=[y for y in train if y<val]
                cache_key=(tuple(past),val,kind)
                if cache_key not in inner_records:
                    model=fit(samples,targets,past,kind);ii,pp=predict(model,samples,val,kind)
                    inner_records[cache_key]=(ii,pp)
                ii,pp=inner_records[cache_key]
                reps=representatives(samples,ii,pp)
                inner.extend(v[0][0] for v in reps[:K])
                for j,i in enumerate(ii):errors[samples[i]['mechanism']].append(samples[i]['r']-float(pp['q'][j]))
            if not inner:raise ContractError('nested forward OOF missing')
            threshold=float(np.quantile(inner,.05))
            model=fit(samples,targets,train,kind)
            model.error={m:max(1,float(np.std(v))) if v else 10 for m,v in errors.items()}
            ix,pred=predict(model,samples,test,kind);reps=representatives(samples,ix,pred)
            info=conditional_information(samples,targets,ix,pred)
            # Baseline entropies use only prior train-year target distribution.
            train_ix=[i for i,s in enumerate(samples) if s['year'] in train]
            prior=np.mean(targets[train_ix,:3],axis=0);prior=np.maximum(prior,1e-9)
            event_counts=CounterEvents(samples,ix)
            iw=np.array([1/event_counts[samples[i]['event']] for i in ix]);iw/=iw.sum()
            h0=float(np.sum(iw*(-np.sum(targets[ix,:3]*np.log2(prior),axis=1))))
            info['regime_log_score_gain_bits']=h0-info['regime_cross_entropy_bits']
            p0=float(np.mean(targets[train_ix,7]));base=-targets[ix,7]*math.log2(max(1e-9,p0))-(1-targets[ix,7])*math.log2(max(1e-9,1-p0))
            info['winner_log_score_gain_bits']=float(np.sum(iw*base))-info['winner_conditional_cross_entropy_bits']
            train_z=targets[train_ix,:3].argmax(1);test_z=targets[ix,:3].argmax(1)
            conditional_prior={m:float(np.mean(targets[np.array(train_ix)[train_z==m],7])) if (train_z==m).any() else p0 for m in range(3)}
            cp=np.clip(np.array([conditional_prior[m] for m in test_z]),1e-9,1-1e-9)
            conditional_base=-targets[ix,7]*np.log2(cp)-(1-targets[ix,7])*np.log2(1-cp)
            info['conditional_winner_log_score_gain_bits']=float(np.sum(iw*conditional_base))-info['winner_conditional_cross_entropy_bits']
            fold[kind]={'precision_at_275':precision(samples,reps),'chronological':chronological(samples,ix,pred,threshold),
                        'threshold_training_only':threshold,'information':info,'year_dro':model.dro_weights,'training_years':train}
        fold['information_delta_bits']=fold['x']['information']['winner_log_score_gain_bits']-fold['summary']['information']['winner_log_score_gain_bits']
        folds[test]=fold;print('[R15-RESEARCH-FOLD]',test,json.dumps(fold),flush=True)
    stable=all(v['x']['precision_at_275']['n']==K and v['x']['precision_at_275']['precision']>=.75 and v['information_delta_bits']>.01 for v in folds.values())
    worst=min(v['x']['precision_at_275']['precision'] for v in folds.values())
    case='C_INFORMATION_CANDIDATE' if stable else 'A_TELEMETRY_INFORMATION_INSUFFICIENT' if worst<.45 else 'B_STATE_LEARNER_INSUFFICIENT'
    # Predictive proxies lack calibrated mean/precision LCB and exact slot parity.
    # Even an information PASS cannot silently authorize burned evaluation.
    manifest={'architecture':'V74_R15_CTRSTA','research_information_pass':stable,'research_pre_gate':False,
              'burned_authorized':False,'burned_status':'NOT_RUN','physical_pass':None,'alpha_gate':False,'v74_gate':False,
              'execution_semantics_ready':False,'promotion_blocker':case if not stable else 'CALIBRATED_LCB_AND_RUNTIME_STOPPING_PARITY_REQUIRED',
              'folds':folds,'research_years':RESEARCH,'validation_used':False,'fresh_used':False,
              'burned_used':False,'runtime_seconds':round(time.monotonic()-start,3),'legal_actions':len(samples),
              'non_regression':'NOT_EVALUATED__CHAMPION_UNCHANGED','information_estimator':'CROSS_FITTED_LOG_SCORE_GAIN_PROXY__NOT_TRUE_MI_BOUND'}
    (out/'V74_R15_RESEARCH_MANIFEST.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    (out/'research_pass.txt').write_text('false\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='folds'},indent=2),flush=True)
if __name__=='__main__':
    try:main()
    except Exception as exc:
        import sys
        if len(sys.argv)>2:
            out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
            failure={'architecture':'V74_R15_CTRSTA','research_status':'NOT_RUN_TELEMETRY_OR_ENGINEERING_FAIL',
                     'physical_status':'NOT_RUN','physical_pass':None,'alpha_gate':False,'alpha_status':'NOT_RUN',
                     'v74_gate':False,'promotion_blocker':type(exc).__name__+': '+str(exc),
                     'burned_status':'NOT_RUN','burned_used':False,'validation_used':False,'fresh_used':False,
                     'non_regression':'NOT_EVALUATED__CHAMPION_UNCHANGED'}
            (out/'V74_R15_RESEARCH_MANIFEST.json').write_text(json.dumps(failure,indent=2)+'\n')
            (out/'research_pass.txt').write_text('false\n')
        raise
