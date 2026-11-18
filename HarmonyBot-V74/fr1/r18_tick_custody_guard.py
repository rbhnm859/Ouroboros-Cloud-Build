#!/usr/bin/env python3
"""Fail-closed *schema* preflight for R18 historical ZIP custody.

A schema check cannot independently prove the tick chronology, execution fills,
or profitability.  No live trading or protected validation samples.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile, BadZipFile

_ALLOWED = b'V74_R17_TICK_V4'
_SCHEMA_RX = re.compile(rb'(?<!\S)schema=(V74_R17_TICK_V\d+)(?:\s|$)')


def file_sha256(path):
    with Path(path).open('rb') as fp:
        return hashlib.file_digest(fp, 'sha256').hexdigest()


def check_archive(path, expected_sha256=None):
    """Return structured observation; never approve strategy or infer outcomes."""
    path = Path(path)
    result = {'archive': path.name, 'state': 'BLOCKED', 'reason': 'UNREADABLE',
              'schema_reliable': False, 'trading_allowed': False,
              'new_strategy_backtest': False}
    if expected_sha256 is not None and file_sha256(path) != expected_sha256:
        return {**result,'reason': 'ARCHIVE_SHA256_MISMATCH'}
    try:
        with ZipFile(path) as z:
            custody = json.loads(z.read('R18_SEMANTIC_CUSTODY.json'))
            if custody.get('data_mode') != 'ticks':
                return {**result,'reason': 'NOT_REAL_TICK_MODE'}
            if any(custody.get(x) for x in ('burned_used','validation_used','fresh_used')):
                return {**result,'reason': 'PROTECTED_DATA_USED'}
            logs = [x for x in z.namelist() if x.endswith('-R15.log')]
            if len(logs) != 1:
                return {**result,'reason': 'MISSING_OR_DUPLICATE_SEALED_LOG'}
            v4_count = 0
            r18_count = 0
            with z.open(logs[0]) as lines:
                for line in lines:
                    if b'[V74-R17-FRAME]' in line:
                        ver = _SCHEMA_RX.search(line)
                        if ver is None:
                            return {**result,'reason': 'MISSING_FRAME_SCHEMA'}
                        if ver.group(1) != _ALLOWED:
                            return {**result,'reason': 'FORBIDDEN_TICK_FRAME',
                                    'observed_schema': ver.group(1).decode('ascii')}
                        v4_count += 1
                    if b'[V74-R18-OUTCOME]' in line and b'schema=V74_R18_OUTCOME_V1 ' in line:
                        r18_count += 1
            if custody.get('tick_time_semantics') != 'FORWARD':
                return {**result,'reason': 'MISSING_FORWARD_CUSTODY','v4_frames': v4_count}
            if v4_count == 0 or r18_count == 0:
                return {**result,'reason': 'MISSING_REQUIRED_FRAME_OR_OUTCOME',
                        'v4_frames': v4_count, 'r18_outcomes': r18_count}
            return {**result, 'state': 'PREFLIGHT_ONLY',
                    'reason': 'SCHEMA_ALLOWLIST_PASS_NEEDS_INDEPENDENT_TICK_ORDER_AND_FILL_VALIDATION',
                    'v4_frames': v4_count,'r18_outcomes': r18_count,
                    'schema_reliable': True}
    except (OSError, BadZipFile, KeyError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument('archives', nargs='+', type=Path)
    p.add_argument('--out',type=Path)
    args=p.parse_args()
    rows=[check_archive(f) for f in args.archives]
    text=json.dumps(rows,indent=2,ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(text+'\n',encoding='utf-8')
    print(text)
    # Data that does not pass source preflight must not be used for returns.
    return 0 if all(r['state']=='PREFLIGHT_ONLY' for r in rows) else 2


if __name__=='__main__':
    raise SystemExit(main())
