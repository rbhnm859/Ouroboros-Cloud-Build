#!/usr/bin/env python3
"""V74-R18 controlled experiment B: outcome/execution semantic correction.

The action supply, R17 features and learner are intentionally held fixed.
Only the training/evaluation outcome semantics are changed from sign-of-R proxy
to explicit tick first-passage causes emitted by the C# runtime.
This experiment can never authorize burned OOF because R17 representatives()
is still an offline across-stage selector rather than an ENTER/DEFER/REJECT policy.
"""
import argparse,datetime as dt,hashlib,json,math,pathlib,time,warnings
from collections import Counter
import numpy as np
from sklearn.exceptions import ConvergenceWarning

from v74_model_lib import load_rows,event_identity,metrics
from v74_r15_supply import make_samples,key
from v74_r15_contract import ContractError
from v74_r17_contract import load_tick_frames,action_native_encode,tick_quality
from v74_r17_model import TickCompetingRisk
from evaluate_v74_r17 import feature_blocks
from v74_r18_outcome import load_outcomes,semantic_class,executable_for_model,cause_distribution

RESEARCH=[f'Y{y}' for y in range(2016,2021)]
TESTS=('Y2018','Y2019','Y2020')
K=275

def legacy_cause(r):
    r=float(r)
    if r>0:return 0
    if r<=-.75:return 1
    return 2

def exact_route_key(s):
    src=s['source'];b=s['base']
    if src in ('EARLY','LATE'):
        return key(s['m'],b,s['fraction'])
    if src=='SURVIVAL' and b.startswith('SURVIVAL_PROOF_'):
        return b[len('SURVIVAL_PROOF_'):]
    if src=='SURVIVAL':
        return b[len('SURVIVAL_'):]
    if src=='REACTION':
        return b[len('REACTION_'):]
    if src=='FAILURE':
        return 'FC230'
    raise ContractError('R18 unknown source '+str(src))

def load_custody(root):
    root=pathlib.Path(root);found={}
    for p in root.rglob('R18_SEMANTIC_CUSTODY.json'):
        d=json.loads(p.read_text())
        w=d.get('window')
        if w not in RESEARCH:continue
        if w in found:raise ContractError('R18 duplicate semantic custody '+w)
        if d.get('schema')!='V74_R18_SEMANTIC_CUSTODY_V1' or d.get('data_mode')!='ticks':
            raise ContractError('R18 bad semantic custody '+str(w))
        if d.get('burned_used') or d.get('validation_used') or d.get('fresh_used'):
            raise ContractError('R18 forbidden custody scope '+str(w))
        sha=str(d.get('evidence_sha256',''))
        if len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):
            raise ContractError('R18 invalid evidence hash '+str(w))
        side=list(p.parent.rglob('*-R15.log'))
        if len(side)!=1:raise ContractError('R18 annual sidecar cardinality '+str(w))
        h=hashlib.sha256(side[0].read_bytes()).hexdigest()
        if h!=sha:raise ContractError('R18 evidence hash mismatch '+str(w))
        found[w]=d
    miss=[w for w in RESEARCH if w not in found]
    if miss:raise ContractError('R18 missing semantic custody '+','.join(miss))
    return found

def prepare(root):
    custody=load_custody(root)
    frames,frame_stats=load_tick_frames(root,RESEARCH)
    outcomes,outcome_stats=load_outcomes(root,RESEARCH)
    rows=load_rows(root,RESEARCH,strict_r15=True)
    raw=make_samples(rows)

    out=[];seen=set()
    raw_unique=0;missing_tick=0;missing_outcome=0;nofill=0;censored=0
    duplicate_hypothesis_dropped=0
    mismatch=Counter();year_counts=Counter();year_joined=Counter();year_exec=Counter()
    min_cap_bad=Counter()

    for s in raw:
        event=(s['window'],event_identity(s['setup']))
        ident=(*event,s['bar'],s['source'],s['base'],s['route'],s.get('fraction',''))
        if ident in seen:
            duplicate_hypothesis_dropped+=1
            continue
        seen.add(ident);raw_unique+=1;year_counts[s['window']]+=1

        z=frames.get((s['window'],s['setup'],s['bar']))
        if z is None:
            missing_tick+=1
            continue
        rk=exact_route_key(s)
        o=outcomes.get((s['window'],s['setup'],s['source'],rk))
        if o is None:
            missing_outcome+=1
            continue
        year_joined[s['window']]+=1
        if not o['min_cap_feasible']:min_cap_bad[s['window']]+=1
        if not o['executed']:
            nofill+=1
            continue
        if o['cause']=='CENSORED':
            censored+=1
            continue
        sc=semantic_class(o['cause'])
        if sc is None:
            censored+=1
            continue
        year_exec[s['window']]+=1

        blocks=feature_blocks(s,z)
        oldr=float(s['y']);oldc=legacy_cause(oldr)
        mismatch[(oldc,sc)]+=1
        hold=max(1,int(math.ceil(max(0.0,(o['exit']-o['decision']).total_seconds())/60.0)))
        out.append({
            'event':event,'year':s['window'],'family':s['family'],
            'decision':o['decision'],'exit':o['exit'],
            'bar':s['bar'],'bars':hold,'source':s['source'],'route':s['route'],
            'exact_route':rk,'semantic_r':float(o['net_r']),'semantic_cause':int(sc),
            'semantic_tp':float(sc==0),'legacy_r':oldr,'legacy_cause':oldc,
            'legacy_tp':float(oldc==0),'rr':float(o['planned_rr']),'x':blocks,
            'cause_name':o['cause'],'min_cap_feasible':o['min_cap_feasible']
        })

    if not out:raise ContractError('R18 no executable semantic samples')
    coverage={w:(year_joined[w]/year_counts[w] if year_counts[w] else 0.0) for w in RESEARCH}
    executable_coverage={w:(year_exec[w]/year_counts[w] if year_counts[w] else 0.0) for w in RESEARCH}
    total_cmp=sum(mismatch.values())
    mismatch_rate=sum(v for (a,b),v in mismatch.items() if a!=b)/max(1,total_cmp)
    diagnostics={
        'raw_actions':len(raw),'event_native_unique_actions':raw_unique,
        'duplicate_hypothesis_dropped':duplicate_hypothesis_dropped,
        'missing_tick':missing_tick,'missing_outcome':missing_outcome,
        'nofill':nofill,'censored':censored,'modeled_actions':len(out),
        'join_coverage':coverage,'executable_coverage':executable_coverage,
        'legacy_vs_semantic_cause_mismatch_rate':mismatch_rate,
        'legacy_vs_semantic_confusion':{f'{a}->{b}':v for (a,b),v in sorted(mismatch.items())},
        'min_cap_infeasible_by_year':dict(min_cap_bad),
        'outcome_stats':outcome_stats,'cause_distribution':cause_distribution(outcomes),
        'frame_stats':frame_stats,'tick_quality':tick_quality(frames),
        'custody':{w:{
            'tick_sha256':custody[w]['tick_sha256'],
            'evidence_sha256':custody[w]['evidence_sha256'],
            'file_count':custody[w]['file_count']
        } for w in RESEARCH}
    }
    return out,diagnostics

def train_indices(samples,years):
    boundary=int(max(years)[1:])+1
    end=dt.datetime(boundary,1,1,tzinfo=dt.timezone.utc)
    return np.array([
        i for i,s in enumerate(samples)
        if s['year'] in years
        and s['decision'].year==int(s['year'][1:])
        and s['exit']<end
    ],dtype=int)

def fit(samples,years,kind,mode,shuffle=False):
    ix=train_indices(samples,years)
    if len(ix)<100:raise ContractError('R18 insufficient training support')
    x=np.asarray([samples[i]['x'][kind] for i in ix],dtype=np.float32)
    if mode=='semantic':
        cause=np.asarray([samples[i]['semantic_cause'] for i in ix],dtype=int)
        rv=np.asarray([samples[i]['semantic_r'] for i in ix],dtype=float)
    else:
        cause=np.asarray([samples[i]['legacy_cause'] for i in ix],dtype=int)
        rv=np.asarray([samples[i]['legacy_r'] for i in ix],dtype=float)
    if shuffle:
        rng=np.random.default_rng(18074)
        p=rng.permutation(len(ix));cause=cause[p];rv=rv[p]
    with warnings.catch_warnings(record=True) as wrn:
        warnings.simplefilter('always',ConvergenceWarning)
        model=TickCompetingRisk().fit(
            x,cause,rv,
            [samples[i]['year'] for i in ix],
            [samples[i]['event'] for i in ix],
            [samples[i]['family'] for i in ix]
        )
    conv=sum(1 for w in wrn if issubclass(w.category,ConvergenceWarning))
    return model,conv

def predict(model,samples,year,kind):
    ix=np.array([i for i,s in enumerate(samples) if s['year']==year],dtype=int)
    if not len(ix):raise ContractError('R18 empty forward year')
    x=np.asarray([samples[i]['x'][kind] for i in ix],dtype=np.float32)
    return ix,model.predict(x,[samples[i]['family'] for i in ix])

def representatives(samples,ix,pred):
    # Deliberately preserves the R17 offline selector ONLY for controlled comparison.
    # Its non-executability is a hard blocker and prevents burned authorization.
    best={}
    for j,i in enumerate(ix):
        s=samples[i];k=s['event'];score=float(pred['score'][j])
        item=(score,-s['bar'],s['exact_route'])
        if k not in best or item>best[k][0]:best[k]=(item,j,i)
    return sorted(best.values(),key=lambda z:(-z[0][0],z[2]))

def wilson_lower(w,n,z=1.645):
    if n<=0:return 0.0
    p=w/n;d=1+z*z/n
    return (p+z*z/(2*n)-z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/d

def topk(samples,reps,pred,mode):
    r=reps[:K];selected=[samples[x[2]] for x in r]
    vals=[s['semantic_r'] if mode=='semantic' else s['legacy_r'] for s in selected]
    mm=metrics([{'r':v,'bars':s['bars']} for v,s in zip(vals,selected)])
    tp=sum((s['semantic_cause']==0 if mode=='semantic' else s['legacy_cause']==0) for s in selected)
    support=float(np.median([pred['support'][x[1]] for x in r])) if r else None
    return {
        'n':len(selected),'precision':mm['win_rate'],'precision_lcb90':wilson_lower(sum(v>0 for v in vals),len(vals)),
        'fdr':1-mm['win_rate'] if vals else 1.0,'tp_first_rate':tp/len(selected) if selected else 0.0,
        'support_median':support,'metrics':mm,
        'cause_distribution':dict(Counter(s['cause_name'] for s in selected)) if mode=='semantic' else None
    }

def weighted_calibration(samples,ix,pred,mode,bins=10):
    counts=Counter(samples[i]['event'] for i in ix)
    w=np.asarray([1.0/counts[samples[i]['event']] for i in ix],dtype=float)
    y=np.asarray([
        samples[i]['semantic_tp'] if mode=='semantic' else samples[i]['legacy_tp']
        for i in ix
    ],dtype=float)
    p=np.asarray(pred['p_tp'],dtype=float)
    sw=max(1e-12,float(w.sum()))
    brier=float(np.sum(w*(p-y)**2)/sw)
    ece=0.0
    for b in range(bins):
        lo=b/bins;hi=(b+1)/bins
        m=(p>=lo)&((p<hi) if b<bins-1 else (p<=hi))
        if not np.any(m):continue
        ww=w[m];mass=float(ww.sum())/sw
        ece+=mass*abs(float(np.sum(ww*p[m])/ww.sum())-float(np.sum(ww*y[m])/ww.sum()))
    return {'event_balanced_brier':brier,'event_balanced_ece10':ece,
            'effective_events':len(counts),'actions':len(ix)}

def logloss(samples,ix,pred,mode):
    loss=[];weights=[];counts=Counter(samples[i]['event'] for i in ix)
    for j,i in enumerate(ix):
        c=samples[i]['semantic_cause'] if mode=='semantic' else samples[i]['legacy_cause']
        p=pred['p_tp'][j] if c==0 else (pred['p_sl'][j] if c==1 else pred['p_exp'][j])
        loss.append(-math.log(max(1e-6,float(p))))
        weights.append(1.0/counts[samples[i]['event']])
    return float(np.average(np.asarray(loss),weights=np.asarray(weights))) if loss else 999.0

def model_result(samples,train,test,kind,mode):
    model,conv=fit(samples,train,kind,mode)
    ix,p=predict(model,samples,test,kind)
    reps=representatives(samples,ix,p)
    return {
        'top275':topk(samples,reps,p,mode),
        'logloss':logloss(samples,ix,p,mode),
        'calibration':weighted_calibration(samples,ix,p,mode),
        'convergence_warnings':conv,
        'dro_weights':model.dro_weights,
        'training_years':train
    },ix,p

def fold(samples,test):
    train=[y for y in RESEARCH if y<test]
    result={}
    full,ix,p=model_result(samples,train,test,'full','semantic')
    result['semantic_full']=full
    for kind in ('no_tick','tick_only','no_harmonic'):
        result['semantic_'+kind]=model_result(samples,train,test,kind,'semantic')[0]
    legacy,_,_=model_result(samples,train,test,'full','legacy')
    result['legacy_full_same_support']=legacy

    neg_model,neg_conv=fit(samples,train,'full','semantic',shuffle=True)
    nix,npred=predict(neg_model,samples,test,'full')
    result['permutation_control']={
        'top275':topk(samples,representatives(samples,nix,npred),npred,'semantic'),
        'convergence_warnings':neg_conv
    }
    result['semantic_precision_lift_vs_legacy']=
        result['semantic_full']['top275']['precision']-result['legacy_full_same_support']['top275']['precision']
    result['tick_precision_lift']=
        result['semantic_full']['top275']['precision']-result['semantic_no_tick']['top275']['precision']
    result['tick_logloss_delta']=
        result['semantic_no_tick']['logloss']-result['semantic_full']['logloss']
    return result

def strict_metric_gate(f,join_coverage):
    z=f['semantic_full']['top275'];m=z['metrics']
    warnings_total=sum(
        f[k].get('convergence_warnings',0)
        for k in ('semantic_full','semantic_no_tick','semantic_tick_only','semantic_no_harmonic')
    )+f['permutation_control'].get('convergence_warnings',0)
    return bool(
        join_coverage>=.98 and z['n']==K and z['precision']>=.72 and z['fdr']<=.28
        and z['precision_lcb90']>=.66 and m['mean_r']>=.90 and m['pf_r']>=3.30
        and m['average_rr']>=2.30 and m['lcb_r']>0
        and (z['support_median'] is None or z['support_median']>=.90)
        and f['tick_precision_lift']>=.05 and f['tick_logloss_delta']>0
        and f['semantic_precision_lift_vs_legacy']>=.05
        and f['permutation_control']['top275']['precision']<.45
        and warnings_total==0
    )

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('out');args=ap.parse_args()
    start=time.monotonic();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    samples,diag=prepare(args.root)
    folds={}
    for test in TESTS:
        folds[test]=fold(samples,test)
        print('[R18-SEMANTIC-FOLD]',test,json.dumps(folds[test],allow_nan=False),flush=True)

    metric_gate=all(strict_metric_gate(folds[y],diag['join_coverage'][y]) for y in TESTS)
    worst=min(folds[y]['semantic_full']['top275']['precision'] for y in TESTS)
    lift=min(folds[y]['semantic_precision_lift_vs_legacy'] for y in TESTS)
    any_conv=any(
        folds[y][k].get('convergence_warnings',0)>0
        for y in TESTS
        for k in ('semantic_full','semantic_no_tick','semantic_tick_only','semantic_no_harmonic')
    )
    sequential_ready=False
    research_pre_gate=False
    if any_conv:
        blocker='R18_MODEL_CONVERGENCE_FAIL'
    elif metric_gate:
        blocker='R18_SEMANTIC_METRIC_GATE_PASS__SEQUENTIAL_POLICY_NOT_EXECUTABLE'
    elif worst<.45 and diag['legacy_vs_semantic_cause_mismatch_rate']>=.05:
        blocker='R18_OUTCOME_MISMATCH_PROVEN_BUT_SEMANTIC_CORRECTION_INSUFFICIENT'
    elif worst<.45:
        blocker='R18_OUTCOME_LABEL_MISMATCH_NOT_DOMINANT__CAUSAL_ACTION_TIME_NEXT'
    else:
        blocker='R18_SEMANTIC_LIFT_PRESENT__CAUSAL_ACTION_TIME_NEXT'

    manifest={
        'architecture':'V74_R18_OUTCOME_EXECUTION_SEMANTIC_REBASE',
        'experiment':'B_OUTCOME_SEMANTIC_CORRECTION',
        'semantic_metric_gate':metric_gate,
        'research_pre_gate':research_pre_gate,
        'research_information_pass':metric_gate,
        'sequential_policy_ready':sequential_ready,
        'burned_authorized':False,'burned_status':'NOT_RUN',
        'physical_pass':None,'alpha_gate':False,'v74_gate':False,
        'execution_semantics_ready':False,'runtime_policy_semantics_parity':False,
        'promotion_blocker':blocker,
        'folds':folds,'diagnostics':diag,
        'research_years':RESEARCH,
        'validation_used':False,'fresh_used':False,'burned_used':False,
        'runtime_seconds':round(time.monotonic()-start,3),
        'gate_contract':{
            'k':K,'precision':.72,'fdr_max':.28,'precision_lcb90':.66,
            'mean_r':.90,'pf_r':3.30,'avg_rr':2.30,'lcb_r_positive':True,
            'join_coverage':.98,'tick_precision_lift':.05,
            'tick_logloss_delta_positive':True,'semantic_precision_lift_vs_legacy':.05,
            'permutation_precision_max':.45,'convergence_warnings':0
        },
        'interpretation':{
            'controlled_component':'OUTCOME_LABEL_AND_EXECUTION_SEMANTICS_ONLY',
            'action_supply':'R17_FROZEN',
            'feature_architecture':'R17_FROZEN',
            'learner':'R17_FROZEN',
            'offline_representatives_preserved_for_control':True,
            'burned_forbidden_until_sequential_policy_rebuilt':True
        }
    }
    (out/'V74_R18_SEMANTIC_MANIFEST.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    (out/'research_pass.txt').write_text('false\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='folds'},indent=2),flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        import sys
        if len(sys.argv)>2:
            out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
            fail={
                'architecture':'V74_R18_OUTCOME_EXECUTION_SEMANTIC_REBASE',
                'experiment':'B_OUTCOME_SEMANTIC_CORRECTION',
                'research_status':'NOT_RUN_TELEMETRY_OR_ENGINEERING_FAIL',
                'research_pre_gate':False,'burned_authorized':False,'burned_status':'NOT_RUN',
                'alpha_gate':False,'v74_gate':False,'execution_semantics_ready':False,
                'runtime_policy_semantics_parity':False,
                'promotion_blocker':type(exc).__name__+': '+str(exc),
                'validation_used':False,'fresh_used':False,'burned_used':False
            }
            (out/'V74_R18_SEMANTIC_MANIFEST.json').write_text(json.dumps(fail,indent=2)+'\n')
            (out/'research_pass.txt').write_text('false\n')
        raise
