#!/usr/bin/env python3
"""Read-only source-locked R18 action attrition and event-coverage audit.

R18 action outcomes only. Never used to train or promote a trading model.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'r18'))
from feasibility_certificate import EXPECTED_SHA256, SOURCE_HEAD, SOURCE_RUN, IntegrityError, audit_year, parse_line


def audit_attrition(path,year,digest):
    legacy=audit_year(path,year,digest)
    seen_actions=set()
    event_all=set()
    event_executed=set()
    event_positive=set()
    event_cap=set()
    event_eligible=set()
    event_positive_eligible=set()
    counts=Counter()
    with zipfile.ZipFile(path) as z:
        logs=[n for n in z.namelist() if n.endswith('-R15.log')]
        if len(logs)!=1:raise IntegrityError('missing or multiple canonical R18 logs')
        with z.open(logs[0]) as f:
            for raw in f:
                if b'[V74-R18-OUTCOME]' not in raw:continue
                r=parse_line(raw.decode('utf-8','strict'))
                if r['action'] in seen_actions:raise IntegrityError('duplicate action')
                seen_actions.add(r['action'])
                counts['action_total']+=1
                counts['cause_'+r['cause']]+=1
                event_all.add(r['event'])
                if not r['executed']:
                    counts['action_nofill']+=1
                    continue
                counts['action_executed']+=1
                event_executed.add(r['event'])
                if r['net_r']>0:event_positive.add(r['event'])
                if not r['min_cap']:
                    counts['action_cap_proxy_infeasible']+=1
                    continue
                event_cap.add(r['event'])
                if r['net_target_rr']+1e-10<2.0:
                    counts['action_net_target_rr_below_2']+=1
                    continue
                counts['action_eligible']+=1
                event_eligible.add(r['event'])
                if r['net_r']>0:event_positive_eligible.add(r['event'])
    if counts['action_eligible']!=legacy['shadow_eligible_actions']:
        raise IntegrityError('eligible action count drift')
    if len(event_eligible)!=legacy['shadow_eligible_events'] or len(event_positive_eligible)!=legacy['shadow_positive_events_event_oracle']:
        raise IntegrityError('event oracle count drift')
    return {'year':year,'artifact_sha256':digest,'source_head':SOURCE_HEAD,'source_run':SOURCE_RUN,
        'raw_independent_events':len(event_all),
        'any_executed_events':len(event_executed),
        'any_executed_positive_events_oracle':len(event_positive),
        'any_cap_proxy_feasible_events':len(event_cap),
        'eligible_independent_events':len(event_eligible),
        'eligible_positive_events_oracle':len(event_positive_eligible),
        'action_counts':dict(sorted(counts.items())),
        'necessary_winners_at_n250':175,
        'unrestricted_r18_executed_winner_count_condition':len(event_positive)>=175,
        'research_only':True}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact-dir',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(argv)
    years=[]
    for y,digest in sorted(EXPECTED_SHA256.items()):
        src=a.artifact_dir/f'v74-r18-semantic-Y{y}.zip'
        if not src.is_file():raise IntegrityError('pinned zip missing '+str(y))
        years.append(audit_attrition(src,y,digest))
    result={'schema':'V74_R19_R18_ATTRITION_V1','research_only':True,
        'alpha_gate':False,'v74_gate':False,'burned_used':False,
        'promotion_authorized':False,'years':years}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'years':[(y['year'],y['raw_independent_events'],y['any_executed_positive_events_oracle'],y['eligible_positive_events_oracle']) for y in years],'research_only':True}))

if __name__=='__main__':main()
