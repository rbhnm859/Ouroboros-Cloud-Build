#!/usr/bin/env python3
"""R19 research-only bounds from pinned R18 artifacts; NO trading or OOF access.

The interval DP deliberately relaxes the unique-event constraint, so it
computes an optimistic upper bound, not an exact joint optimum.
"""
from __future__ import annotations
import argparse
from bisect import bisect_right
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'r18'))
from feasibility_certificate import EXPECTED_SHA256, audit_year, parse_line, IntegrityError, SOURCE_HEAD, SOURCE_RUN


def max_nonoverlap_relaxed(actions):
    """Maximum count of nonoverlapping half-open [decision, exit) intervals.

    Same-event actions are NOT excluded. Coupled event+interval optimization
    can only reduce this upper bound, so it cannot produce a false FAIL.
    """
    intervals = sorted(((a['exit'], a['decision']) for a in actions), key=lambda x: (x[0], x[1]))
    ends = [end for end, _ in intervals]
    dp = [0] * (len(intervals) + 1)
    for i, (end, start) in enumerate(intervals, 1):
        if end < start:
            raise IntegrityError('negative action interval')
        predecessor_count = bisect_right(ends, start, 0, i - 1)
        dp[i] = max(dp[i - 1], dp[predecessor_count] + 1)
    return dp[-1]


def collect_eligible_actions(path):
    with zipfile.ZipFile(path) as z:
        logs = [n for n in z.namelist() if n.endswith('-R15.log')]
        if len(logs) != 1:
            raise IntegrityError('missing/ambiguous R18 canonical log')
        eligible = []
        best = {}
        with z.open(logs[0]) as stream:
            for raw in stream:
                if b'[V74-R18-OUTCOME]' not in raw:
                    continue
                r = parse_line(raw.decode('utf-8', 'strict'))
                if not r['executed'] or not r['min_cap'] or r['net_target_rr'] + 1e-10 < 2.0:
                    continue
                eligible.append(r)
                if r['event'] not in best or r['net_r'] > best[r['event']]['net_r']:
                    best[r['event']] = r
        return eligible, best


def audit_pinned_year(path, year, expected_digest):
    # Existing R18 certificate independently validates ZIP SHA256, custody,
    # duplicate actions, execution semantics, timestamp and risk geometry.
    legacy = audit_year(path, year, expected_digest)
    actions, best = collect_eligible_actions(path)
    positive_actions = [r for r in actions if r['net_r'] > 0]
    n_events = len(best)
    n_winners = sum(r['net_r'] > 0 for r in best.values())
    if n_events != legacy['shadow_eligible_events'] or n_winners != legacy['shadow_positive_events_event_oracle']:
        raise IntegrityError('R19/legacy event oracle parity mismatch')
    if len(actions) != legacy['shadow_eligible_actions']:
        raise IntegrityError('R19/legacy eligible-action count mismatch')
    relaxed_n = max_nonoverlap_relaxed(actions)
    relaxed_wins = max_nonoverlap_relaxed(positive_actions)
    upper_n = min(n_events, relaxed_n)
    upper_wins = min(n_winners, relaxed_wins)
    return {
        'year': year, 'artifact_sha256': expected_digest,
        'source_run': SOURCE_RUN, 'source_head': SOURCE_HEAD,
        'eligible_actions': len(actions),
        'unique_eligible_events': n_events,
        'unique_oracle_positive_events': n_winners,
        'relaxed_nonoverlap_action_count': relaxed_n,
        'relaxed_nonoverlap_positive_action_count': relaxed_wins,
        'independent_nonoverlap_count_upper_bound': upper_n,
        'independent_nonoverlap_positive_upper_bound': upper_wins,
        'required_n': 250, 'required_winners': 175,
        'necessary_count_conditions_pass': upper_n >= 250 and upper_wins >= 175,
        'strict_gate': False, 'commercial_gate': False,
        'relaxation': 'interval DP may select multiple actions from one event; min with unique-event counts is an optimistic bound, not exact joint optimum',
        'limits': ['R18 existing actions ONLY', 'shadow execution not broker verified',
                   'minimum capital is proxy', 'hindsight oracle is not a causal policy'],
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact-dir', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args(argv)
    years = []
    for y, digest in sorted(EXPECTED_SHA256.items()):
        path = args.artifact_dir / f'v74-r18-semantic-Y{y}.zip'
        if not path.is_file():
            raise IntegrityError(f'missing pinned artifact Y{y}')
        years.append(audit_pinned_year(path, y, digest))
    result = {
        'schema': 'V74_R19_R18_PINNED_BOUND_V1',
        'research_only': True, 'alpha_gate': False, 'v74_gate': False,
        'burned_used': False, 'promotion_authorized': False,
        'all_years_pass_necessary_counts': all(y['necessary_count_conditions_pass'] for y in years),
        'years': years,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(args.out), 'years': [
        (r['year'], r['unique_eligible_events'], r['unique_oracle_positive_events']) for r in years
    ], 'research_only': True}))


if __name__ == '__main__':
    main()
