"""Secret-free GitHub scheduler probe; never imports or runs trading/agent code."""
import argparse
import json
from pathlib import Path
import time


def verify(rows):
    expected = {'r17', 'r18', 'third-pending', 'independent'}
    if {r['name'] for r in rows} != expected or len(rows) != len(expected):
        raise ValueError('missing/duplicate probe receipt: a pending job may have been canceled')
    shared = sorted((r for r in rows if r['lock'] == 'shared'), key=lambda r: r['start_ns'])
    if {r['name'] for r in shared} != expected - {'independent'}:
        raise ValueError('wrong probe lock membership')
    for row in rows:
        if row['end_ns'] <= row['start_ns']:
            raise ValueError('invalid probe interval')
    if next(r for r in rows if r['name'] == 'independent')['lock'] != 'independent':
        raise ValueError('unrelated probe must use a different group')
    for previous, current in zip(shared, shared[1:]):
        if previous['end_ns'] > current['start_ns']:
            raise ValueError('shared-group work overlapped')
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--name')
    p.add_argument('--lock', choices=['shared', 'independent'])
    p.add_argument('--verify', type=Path)
    args = p.parse_args()
    if args.verify:
        rows = [json.loads(f.read_text()) for f in args.verify.glob('*.json')]
        verify(rows)
        print('PASS: 3 shared-group probes completed without overlap/cancellation; independent probe completed')
        print('Scope: synthetic job-level GitHub scheduling only; no broker or Engineer runtime validation')
    else:
        if args.name not in {'r17', 'r18', 'third-pending', 'independent'} or not args.lock:
            p.error('known probe name and lock required')
        start = time.time_ns()
        time.sleep(3)
        row = {'name': args.name, 'lock': args.lock, 'start_ns': start, 'end_ns': time.time_ns()}
        Path('probe-receipts').mkdir(exist_ok=True)
        Path('probe-receipts', args.name + '.json').write_text(json.dumps(row) + '\n')
        print(json.dumps(row))


if __name__ == '__main__':
    main()
