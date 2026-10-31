#!/usr/bin/env python3
"""Audit a completed research artifact without refitting or selecting a model."""
import copy,json,pathlib,sys
YEARS=('Y2018','Y2019','Y2020')

def audit(manifest):
    m=copy.deepcopy(manifest)
    m.update({'alpha_gate':False,'alpha_status':'NOT_RUN','v74_gate':False,
              'execution_semantics_ready':False,'burned_authorized':False,'burned_status':'NOT_RUN',
              'burned_non_regression':'NOT_EVALUATED__CHAMPION_UNCHANGED'})
    folds=m.get('folds')
    if folds is None:
        m['audit_status']='ENGINEERING_FAILURE__NO_ALPHA_INFERENCE';return m
    if set(folds)!=set(YEARS):raise ValueError('incomplete outer forward research folds')
    precision=[];deltas=[];regime=[];conditional=[];nonreg=True
    for y in YEARS:
        f=folds[y];a=f['x']['precision_at_275'];b=f['summary']['precision_at_275']
        if not all(isinstance(z['n'],int) and z['n']>=0 and 0<=z['precision']<=1 and abs(z['fdr']+z['precision']-1)<1e-9 for z in (a,b)):
            raise ValueError('research metric identity mismatch')
        precision.append(a['precision'] if a['n']==275 else 0.)
        deltas.append(f['information_delta_bits'])
        regime.append(f['x']['information']['regime_log_score_gain_bits'])
        conditional.append(f['x']['information']['conditional_winner_log_score_gain_bits'])
        nonreg &= a['precision']>=b['precision']
    worst=min(precision);approx=max(abs(d) for d in deltas)<=.01
    margin=worst>=.75 and min(deltas)>.01 and min(regime)>0 and min(conditional)>0 and nonreg
    if not nonreg:case='REJECTED__OBSERVED_REGRESSION_VS_MATCHED_SUMMARY'
    elif worst<.45 and approx:case='A_ENCODER_LEARNER_FOUND_NO_SUFFICIENT_NEW_INFORMATION'
    elif margin:case='C_INFORMATION_MARGIN_ONLY__CALIBRATED_LCB_RUNTIME_PARITY_PENDING'
    else:case='B_RESEARCH_PRECISION_OR_REGIME_INFORMATION_MARGIN_FAIL'
    m.update({'audit_status':'COMPLETED_RESEARCH_ONLY','research_information_pass':margin,
              'research_pre_gate':False,'promotion_blocker':case,'worst_precision_at_275':worst,
              'matched_summary_non_regression':bool(nonreg),'experiment_rejected':not margin,
              'information_claim':'CROSS_FITTED_LOG_SCORE_PROXY__NOT_A_UNIVERSAL_INFORMATION_CEILING',
              'next_scope':'RESEARCH_YEARS_ONLY__NO_BURNED_THRESHOLD_REPAIR'})
    return m
def verify_archived_result(source,pin_path):
    import hashlib,zipfile
    pin_path=pathlib.Path(pin_path);pin=json.loads(pin_path.read_text());root=pin_path.parents[2]
    archive=pin_path.parent/pin['artifact_archive']
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=pin['artifact_archive_sha256']:
        raise ValueError('research result archive checksum mismatch')
    with zipfile.ZipFile(archive) as z:
        data=z.read(pin['manifest_member'])
    if pathlib.Path(source).read_bytes()!=data:raise ValueError('research manifest differs from original CI artifact')
    for file,digest in pin['evaluator_hashes'].items():
        if hashlib.sha256((root/file).read_bytes()).hexdigest()!=digest:raise ValueError('model/evaluator changed; cached verdict invalid')
    return pin

if __name__=='__main__':
    source=pathlib.Path(sys.argv[1]);target=pathlib.Path(sys.argv[2]);target.parent.mkdir(parents=True,exist_ok=True)
    if len(sys.argv)>3:verify_archived_result(source,sys.argv[3])
    target.write_text(json.dumps(audit(json.loads(source.read_text())),indent=2,allow_nan=False)+'\n')
