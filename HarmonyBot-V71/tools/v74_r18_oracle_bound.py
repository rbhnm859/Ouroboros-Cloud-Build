#!/usr/bin/env python3
"""V74-R18 label/geometry ceiling audit (evaluator only, no backtest, no ticks).

Question answered with evidence instead of tuning:
  Can the current V73/V74 opportunity universe and the current fixed-RR entry
  geometry ever produce the V74 gate targets (WR >= .70, MeanR >= .90,
  AvgRR >= 2.30, PF_R >= 3.30) at the contract K=275, and if not, WHICH
  component is binding: supply, geometry, entry timing, censoring, capital
  feasibility, or the learner?

Input: sealed annual outcome telemetry (V74-R18-OUTCOME) plus the frozen
V73/V74 action-supply rows. It deliberately never reads R17 tick frames, so it
stays valid on pinned pre-rebase artifacts whose tick feed was still the legacy
newest-to-oldest order.

HARD BOUNDARY
  Every "oracle" number is computed with perfect foresight and is therefore an
  ACHIEVABILITY CEILING, never evidence of alpha. It can only falsify claims.
  alpha_gate / v74_gate / research_pre_gate always stay false here.

Pre-registered precedence for the binding-constraint verdict:
  1. SUPPLY_OR_GEOMETRY_BOUNDED : no stratum with n>=250 reaches y>=0.20
  2. CAPITAL_FEASIBILITY        : min_cap infeasible share > 0.25
  3. ENTRY_TIMING               : global y < 0 and adverse entry slip > 0.15R
  4. CENSORING                  : expiry share of executed > 0.35
  5. LEARNER                    : otherwise
"""
import argparse,collections,datetime as dt,json,math,pathlib,time

import numpy as np

from v74_model_lib import load_rows,event_identity,metrics
from v74_r15_contract import ContractError
from v74_r15_supply import make_samples,key
from v74_r18_outcome import load_outcomes,semantic_class

RESEARCH=[f'Y{y}' for y in range(2016,2021)]
TESTS=('Y2018','Y2019','Y2020')
K=275
K_CERT=250
TARGET_WR=.70
TARGET_MEAN_R=.90
TARGET_PF=3.30
TARGET_AVG_RR=2.30
MIN_STRATUM_N=250

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
    raise ContractError('R18 oracle unknown source '+str(src))

def first_passage_p(y,a,b=1.0):
    """P(hit +a before -b) for X = mu t + sigma W, with y = 2 mu / sigma^2."""
    if abs(y)<1e-12:
        return b/(a+b)
    den=1.0-math.exp(-y*(a+b))
    if den==0.0:
        return 1.0 if y>0 else 0.0
    return (1.0-math.exp(-y*b))/den

def invert_y(p,a,b=1.0):
    """Solve first_passage_p(y,a,b)=p for y in [-20,20] (monotone in y)."""
    p=min(1.0,max(0.0,float(p)))
    lo,hi=-20.0,20.0
    if p<=first_passage_p(lo,a,b):
        return lo
    if p>=first_passage_p(hi,a,b):
        return hi
    for _ in range(200):
        mid=(lo+hi)/2.0
        if first_passage_p(mid,a,b)<p:
            lo=mid
        else:
            hi=mid
    return (lo+hi)/2.0

def required_p_for_mean_r(mean_r,rr):
    """MeanR = P*rr - (1-P) >= mean_r  =>  P >= (mean_r+1)/(rr+1)."""
    return (mean_r+1.0)/(rr+1.0)

def wilson_lower(w,n,z=1.645):
    if n<=0:
        return 0.0
    p=w/n;d=1+z*z/n
    return (p+z*z/(2*n)-z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/d

def bucket_hour(h):
    if 7<=h<12:return 'LDN'
    if 12<=h<16:return 'LDN_NY_OVERLAP'
    if 16<=h<21:return 'NY'
    if h>=21 or h<2:return 'ASIA_LATE'
    return 'ASIA'

def bucket_risk(risk):
    if not math.isfinite(risk) or risk<=0:return 'NA'
    if risk<2.0:return 'RISK_LT_2'
    if risk<5.0:return 'RISK_2_5'
    if risk<12.0:return 'RISK_5_12'
    return 'RISK_GE_12'

def bucket_rr(rr):
    if not math.isfinite(rr):return 'NA'
    if rr<2.3:return 'RR_LT_2.3'
    if rr<3.0:return 'RR_2.3_3'
    if rr<4.0:return 'RR_3_4'
    return 'RR_GE_4'

def is_resolved(r):
    return r['semantic_class'] in (0,1)

def prepare(root):
    rows=load_rows(root,RESEARCH,strict_r15=True)
    raw=make_samples(rows)
    outcomes,outcome_stats=load_outcomes(root,RESEARCH)
    seen=set();records=[];counts=collections.Counter()
    for s in raw:
        event=(s['window'],event_identity(s['setup']))
        ident=(*event,s['bar'],s['source'],s['base'],s['route'],s.get('fraction',''))
        if ident in seen:
            counts['duplicate_dropped']+=1
            continue
        seen.add(ident);counts['event_native_unique']+=1
        o=outcomes.get((s['window'],s['setup'],s['source'],exact_route_key(s)))
        if o is None:
            counts['missing_outcome']+=1
            continue
        counts['joined']+=1
        sc=semantic_class(o['cause'])
        hold=max(1,int(math.ceil(max(0.0,(o['exit']-o['decision']).total_seconds())/60.0)))
        records.append({
            'year':s['window'],'event':event,'family':s['family'],'action':s['action'],
            'source':s['source'],'route':s['route'],'bar':int(s['bar']),
            'decision':o['decision'],'bars':hold,
            'cause':o['cause'],'executed':bool(o['executed']),
            'semantic_class':(None if sc is None else int(sc)),
            'net_r':float(o['net_r']),'planned_rr':float(o['planned_rr']),'risk':float(o['risk']),
            'planned_entry':float(o['planned_entry']),'fill':float(o['fill']),
            'stop':float(o['stop']),'target':float(o['target']),
            'entry_spread_pips':float(o['entry_spread_pips']),
            'extra_cost_pips':float(o['extra_cost_pips']),
            'min_cap_feasible':bool(o['min_cap_feasible']),
            'direction_up':bool(o['direction']=='BUY'),
        })
    if not records:
        raise ContractError('R18 oracle bound: no joined records')
    return records,dict(counts),outcome_stats

def metrics_of(rows):
    if not rows:
        return {'n':0,'precision':0.0,'precision_lcb90':0.0,'metrics':{},
                'cause_counts':{},'tp_first_rate':0.0}
    wins=sum(1 for r in rows if r['net_r']>0)
    tps=sum(1 for r in rows if r['semantic_class']==0)
    return {
        'n':len(rows),
        'precision':wins/len(rows),
        'precision_lcb90':wilson_lower(wins,len(rows)),
        'tp_first_rate':tps/len(rows),
        'metrics':metrics([{'r':r['net_r'],'bars':r['bars']} for r in rows]),
        'cause_counts':dict(collections.Counter(r['cause'] for r in rows)),
    }

def by_event(records):
    g=collections.defaultdict(list)
    for r in records:
        g[r['event']].append(r)
    return g

SOURCE_ORDER={'EARLY':0,'LATE':1,'SURVIVAL':2,'REACTION':3,'FAILURE':4}

def oracle_admission_oracle_route(records):
    g=by_event(records)
    return [max(rs,key=lambda r:(r['net_r'],-r['bar'])) for rs in g.values()]

def oracle_admission_causal_route(records):
    g=by_event(records)
    out=[]
    for rs in g.values():
        pool=[r for r in rs if r['executed']] or rs
        out.append(min(pool,key=lambda r:(SOURCE_ORDER.get(r['source'],9),r['bar'],-r['planned_rr'])))
    return out

def stratum_key(r):
    return (str(r['family']),str(r['source']),str(r['action']),
            bucket_hour(r['decision'].hour),bucket_risk(r['risk']),bucket_rr(r['planned_rr']))

def single_key(r,name):
    d=r['decision']
    table={
        'family':str(r['family']),'source':str(r['source']),'action':str(r['action']),
        'route':str(r['route']),'session':bucket_hour(d.hour),'weekday':d.strftime('%a'),
        'month':d.strftime('%m'),'risk':bucket_risk(r['risk']),'rr':bucket_rr(r['planned_rr']),
        'feasible':('FEASIBLE' if r['min_cap_feasible'] else 'INFEASIBLE'),
        'source_x_session':str(r['source'])+'|'+bucket_hour(d.hour),
        'family_x_session':str(r['family'])+'|'+bucket_hour(d.hour),
        'family_x_risk':str(r['family'])+'|'+bucket_risk(r['risk']),
        'source_x_rr':str(r['source'])+'|'+bucket_rr(r['planned_rr']),
        'session_x_rr':bucket_hour(d.hour)+'|'+bucket_rr(r['planned_rr']),
    }
    return table.get(name,'NA')

KEYS=('family','source','action','session','weekday','month','risk','rr','feasible',
      'source_x_session','family_x_session','family_x_risk','source_x_rr','session_x_rr')

def stratum_stats(records):
    out={}
    resolved_rows=[r for r in records if is_resolved(r)]
    for name in KEYS:
        cells=collections.defaultdict(list)
        for r in resolved_rows:
            cells[single_key(r,name)].append(r)
        rows=[]
        for value,rs in cells.items():
            n=len(rs)
            if n<MIN_STRATUM_N:
                continue
            tp=sum(1 for r in rs if r['semantic_class']==0)
            sl=sum(1 for r in rs if r['semantic_class']==1)
            p=tp/(tp+sl) if (tp+sl) else 0.0
            rr=float(np.mean([r['planned_rr'] for r in rs])) if rs else TARGET_AVG_RR
            rows.append({'key':name,'value':value,'n':n,'tp_first':tp,'sl_first':sl,
                         'p_tp_first':p,'mean_planned_rr':rr,'y_implied':invert_y(p,rr),
                         'y_required_70':invert_y(TARGET_WR,rr),
                         'mean_net_r':float(np.mean([r['net_r'] for r in rs]))})
        rows.sort(key=lambda x:-x['y_implied'])
        out[name]=rows[:10]
    flat=[row for name in KEYS for row in out[name]]
    flat.sort(key=lambda x:-x['y_implied'])
    return {'by_key':out,'best':(flat[0] if flat else None),'top':flat[:20]}

def first_passage_edge(records):
    resolved_rows=[r for r in records if is_resolved(r)]
    tp=sum(1 for r in resolved_rows if r['semantic_class']==0)
    sl=sum(1 for r in resolved_rows if r['semantic_class']==1)
    n=tp+sl
    p=tp/n if n else 0.0
    rr=float(np.mean([r['planned_rr'] for r in resolved_rows])) if n else TARGET_AVG_RR
    executed=[r for r in records if r['executed']]
    expiry=sum(1 for r in executed if r['cause'] in ('TIME_EXPIRE','SESSION_EXPIRE'))
    infeasible=sum(1 for r in records if not r['min_cap_feasible'])
    return {
        'resolved_actions':n,'tp_first':tp,'sl_first':sl,
        'p_tp_first_resolved':p,
        'driftless_bound_at_rr':(1.0/(1.0+rr)),
        'y_implied':invert_y(p,rr),
        'y_required_for_wr_70':invert_y(TARGET_WR,rr),
        'y_required_for_meanr_090':invert_y(required_p_for_mean_r(TARGET_MEAN_R,rr),rr),
        'mean_planned_rr':rr,
        'executed':len(executed),
        'expiry_share_of_executed':(expiry/len(executed)) if executed else 0.0,
        'min_cap_infeasible_share':(infeasible/len(records)) if records else 0.0,
    }

def entry_slippage(records):
    per_year=collections.defaultdict(list)
    per_source=collections.defaultdict(list)
    degraded=0;executed=0
    for r in records:
        if not r['executed']:
            continue
        executed+=1
        sign=1.0 if r['direction_up'] else -1.0
        slip=sign*(r['fill']-r['planned_entry'])/max(r['risk'],1e-12)
        per_year[r['year']].append(slip)
        per_source[str(r['source'])].append(slip)
        rr_real=abs(r['target']-r['fill'])/max(abs(r['fill']-r['stop']),1e-12)
        if rr_real<2.0:
            degraded+=1
    def stats(xs):
        if not xs:
            return {'n':0}
        a=np.asarray(xs,dtype=float);q=np.quantile(a,[.1,.5,.9])
        return {'n':int(a.size),'mean_R':float(a.mean()),'p10_R':float(q[0]),
                'median_R':float(q[1]),'p90_R':float(q[2]),
                'adverse_share_over_005R':float((a>0.05).mean())}
    by_year={y:stats(v) for y,v in sorted(per_year.items())}
    all_slip=[x for v in per_year.values() for x in v]
    return {'by_year':by_year,'by_source':{s:stats(v) for s,v in sorted(per_source.items())},
            'executed':executed,
            'adverse_mean_R':stats(all_slip)['mean_R'] if all_slip else 0.0,
            'realized_rr_below_2_share':degraded/max(1,executed)}

def causal_stratum_prior(records,test):
    train=[r for r in records if r['year']<test and is_resolved(r)]
    if not train:
        train=[r for r in records if r['year']<test]
    glob_tp=sum(1 for r in train if r['semantic_class']==0)
    gp=(glob_tp+2.0)/(len(train)+4.0) if train else 0.1
    cells=collections.defaultdict(lambda:[0,0])
    for r in train:
        c=cells[stratum_key(r)];c[1]+=1
        if r['semantic_class']==0:
            c[0]+=1
    def p_of(r):
        w,n=cells.get(stratum_key(r),[0,0])
        return (w+20.0*gp)/(n+20.0)
    return p_of,gp

def selective_risk_curve(records):
    out={}
    for test in TESTS:
        p_of,gp=causal_stratum_prior(records,test)
        rows=[r for r in records if r['year']==test]
        ranked=sorted(rows,key=lambda r:(-p_of(r),-r['planned_rr'],r['bar']))
        curve=[];certified=0
        for n in (25,50,100,150,200,250,275,400,600):
            sel=ranked[:n]
            if not sel:
                continue
            m=metrics_of(sel)
            row={'n':m['n'],'precision':m['precision'],'precision_lcb90':m['precision_lcb90'],
                 'tp_first_rate':m['tp_first_rate'],'mean_r':m['metrics'].get('mean_r'),
                 'pf_r':m['metrics'].get('pf_r'),'avg_rr':m['metrics'].get('average_rr'),
                 'lcb_r':m['metrics'].get('lcb_r')}
            curve.append(row)
            if row['precision_lcb90']>=.66:
                certified=max(certified,row['n'])
        out[test]={'curve':curve,'max_certified_n_lcb90_066':certified,
                   'global_train_p':gp,'k_contract':K,'k_cert_required':K_CERT}
    return out

def build_verdict(edge,strata,slippage):
    best_y=(strata['best']['y_implied'] if strata.get('best') else None)
    reasons=[]
    if best_y is None or best_y<0.20:
        primary='SUPPLY_OR_GEOMETRY_BOUNDED'
        reasons.append('no stratum with n>=%d reaches y>=0.20; the current universe cannot'
                       ' contain 70%% target-first actions regardless of model'%MIN_STRATUM_N)
    elif edge['min_cap_infeasible_share']>0.25:
        primary='CAPITAL_FEASIBILITY_DOMINANT'
        reasons.append('min_cap_infeasible_share=%.3f > 0.25'%edge['min_cap_infeasible_share'])
    elif edge['y_implied']<0.0 and slippage['adverse_mean_R']>0.15:
        primary='ENTRY_TIMING_DOMINANT'
        reasons.append('y_implied=%.3f < 0 and adverse entry slip mean=%.3fR > 0.15R'
                       %(edge['y_implied'],slippage['adverse_mean_R']))
    elif edge['expiry_share_of_executed']>0.35:
        primary='CENSORING_DOMINANT'
        reasons.append('expiry share of executed=%.3f > 0.35'%edge['expiry_share_of_executed'])
    else:
        primary='LEARNER_DOMINANT'
        reasons.append('supply/geometry/entry/censoring/feasibility inside tolerance;'
                       ' residual gap is learner side')
    return {'primary_binding_constraint':primary,'reasons':reasons,
            'measured':{'y_implied':edge['y_implied'],
                        'y_required_for_wr_70':edge['y_required_for_wr_70'],
                        'best_stratum_y':best_y,
                        'adverse_entry_slip_mean_R':slippage['adverse_mean_R'],
                        'expiry_share_of_executed':edge['expiry_share_of_executed'],
                        'min_cap_infeasible_share':edge['min_cap_infeasible_share']}}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('out')
    args=ap.parse_args()
    start=time.monotonic()
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    records,counts,outcome_stats=prepare(args.root)

    quadrants={}
    for test in TESTS:
        year=[r for r in records if r['year']==test]
        quadrants[test]={
            'A_oracle_admission_oracle_route':metrics_of(oracle_admission_oracle_route(year)[:K]),
            'B_oracle_admission_causal_route':metrics_of(oracle_admission_causal_route(year)[:K]),
            'universe':{'actions':len(year),'events':len({r['event'] for r in year}),
                        'executed':sum(1 for r in year if r['executed']),
                        'tp_first':sum(1 for r in year if r['semantic_class']==0),
                        'tp_first_rate':metrics_of(year)['tp_first_rate']},
        }
    edge=first_passage_edge(records)
    strata=stratum_stats(records)
    slippage=entry_slippage(records)
    curve=selective_risk_curve(records)
    verdict=build_verdict(edge,strata,slippage)

    manifest={
        'architecture':'V74_R18_ORACLE_BOUND_AUDIT','evaluator_only':True,
        'uses_future_information':True,'not_a_promotion_gate':True,
        'alpha_gate':False,'v74_gate':False,'research_pre_gate':False,
        'burned_authorized':False,'burned_status':'NOT_RUN',
        'validation_used':False,'fresh_used':False,'burned_used':False,
        'research_years':RESEARCH,'contract_k':K,'certified_k_required':K_CERT,
        'targets':{'wr':TARGET_WR,'mean_r':TARGET_MEAN_R,'pf_r':TARGET_PF,'avg_rr':TARGET_AVG_RR},
        'join_counts':counts,'outcome_stats':outcome_stats,
        'verdict':verdict,'runtime_seconds':round(time.monotonic()-start,3),
    }
    (out/'V74_R18_ORACLE_BOUND.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    (out/'oracle_quadrants.json').write_text(json.dumps(quadrants,indent=2,allow_nan=False)+'\n')
    (out/'stratified_oracle_bound.json').write_text(json.dumps(strata,indent=2,allow_nan=False)+'\n')
    (out/'first_passage_edge.json').write_text(json.dumps(edge,indent=2,allow_nan=False)+'\n')
    (out/'entry_geometry_slippage.json').write_text(json.dumps(slippage,indent=2,allow_nan=False)+'\n')
    (out/'selective_risk_curve.json').write_text(json.dumps(curve,indent=2,allow_nan=False)+'\n')
    print('[R18-ORACLE-BOUND]',json.dumps(verdict,allow_nan=False),flush=True)
    print('[R18-ORACLE-EDGE]',json.dumps(edge,allow_nan=False),flush=True)
    print(json.dumps(manifest,indent=2,allow_nan=False),flush=True)

if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        import sys
        if len(sys.argv)>2:
            out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
            fail={'architecture':'V74_R18_ORACLE_BOUND_AUDIT',
                  'research_status':'NOT_RUN_TELEMETRY_OR_ENGINEERING_FAIL',
                  'promotion_blocker':type(exc).__name__+': '+str(exc),
                  'alpha_gate':False,'v74_gate':False,'research_pre_gate':False,
                  'burned_authorized':False,'burned_status':'NOT_RUN',
                  'validation_used':False,'fresh_used':False,'burned_used':False}
            (out/'V74_R18_ORACLE_BOUND.json').write_text(json.dumps(fail,indent=2)+'\n')
        raise
