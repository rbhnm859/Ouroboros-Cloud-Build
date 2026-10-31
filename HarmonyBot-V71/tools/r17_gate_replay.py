#!/usr/bin/env python3
"""Gate-only replay for V74-R17 using immutable annual artifacts from a pinned run.

This wrapper changes custody resolution only. It does not alter the R17 learner,
features, thresholds, research years, or any burned/Validation/Fresh policy.
"""
import hashlib
import math
from pathlib import Path

import evaluate_v74_r17 as base
from v74_model_lib import RX, FEATURE_NAMES
from v74_r15_contract import validate_sidecar, ContractError

def audit_raw_outcomes_r17(root, windows):
    count=0
    seen_windows=set()
    root=Path(root)
    for p in root.rglob('*-R15.log'):
        matches=[w for w in windows if w in str(p)]
        if len(matches)!=1:
            continue
        w=matches[0]
        validate_sidecar(p,require_hash=False)

        pins=list(p.parent.parent.glob(f'R17_EVIDENCE_SHA256-{w}.txt'))
        matched=[]
        for pin in pins:
            fields=pin.read_text().split()
            if len(fields)==2 and Path(fields[1]).name==p.name:
                matched.append((pin,fields[0]))
        if len(matched)!=1:
            raise ContractError(f'R17 missing/duplicate sidecar SHA256 custody {w}')

        digest=hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''):
                digest.update(block)
        if digest.hexdigest()!=matched[0][1]:
            raise ContractError(f'R17 sidecar SHA256 custody mismatch {w}')

        seen_windows.add(w)
        with p.open(errors='strict') as f:
            for line in f:
                if '[V72-HCOG-OUTCOME]' not in line:
                    continue
                match=RX.search(line)
                if match is None:
                    raise ContractError('malformed raw outcome would be silently skipped')
                raw=match.group(17)
                if raw in (None,'NONE'):
                    raise ContractError('missing causal event-static vector')
                try:
                    vec=[float(x) for x in raw.split(',')]
                except ValueError as e:
                    raise ContractError('corrupt causal event-static vector') from e
                if len(vec)!=len(FEATURE_NAMES) or not all(math.isfinite(x) for x in vec):
                    raise ContractError('invalid causal event-static vector')
                if not math.isfinite(float(match.group(7))):
                    raise ContractError('nonfinite outcome label')
                count+=1

    missing=[w for w in windows if w not in seen_windows]
    if missing:
        raise ContractError('R17 missing research window sidecar custody '+','.join(missing))
    if not count:
        raise ContractError('no terminal outcome records')
    return count

base.audit_raw_outcomes=audit_raw_outcomes_r17

if __name__=='__main__':
    base.main()
