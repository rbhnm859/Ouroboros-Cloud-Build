#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
from pathlib import Path

RX = re.compile(
    r"\[R8 EXCURSION\]\s+id=(?P<id>\d+)\s+dir=(?P<dir>Buy|Sell)\s+pattern=(?P<pattern>\S+)\s+"
    r"riskPips=(?P<risk>-?[0-9.]+)\s+targetR=(?P<target>-?[0-9.]+)\s+mfeR=(?P<mfe>-?[0-9.]+)\s+"
    r"maeR=(?P<mae>-?[0-9.]+)\s+finalR=(?P<final>-?[0-9.]+)\s+net=(?P<net>-?[0-9.]+)\s+"
    r"durationMin=(?P<dur>-?[0-9.]+)\s+reason=(?P<reason>\S+)"
)
THRESHOLDS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.8, 2.0, 2.2]


def parse(path: Path):
    rows = []
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        m = RX.search(line)
        if not m:
            continue
        d = m.groupdict()
        rows.append({
            'id': int(d['id']), 'direction': d['dir'], 'pattern': d['pattern'],
            'risk_pips': float(d['risk']), 'target_r': float(d['target']),
            'mfe_r': float(d['mfe']), 'mae_r': float(d['mae']),
            'final_r': float(d['final']), 'net': float(d['net']),
            'duration_min': float(d['dur']), 'reason': d['reason'],
        })
    return rows


def q(values, p):
    if not values:
        return None
    v = sorted(values)
    if len(v) == 1:
        return v[0]
    x = (len(v) - 1) * p
    lo = int(math.floor(x)); hi = int(math.ceil(x))
    if lo == hi:
        return v[lo]
    return v[lo] * (hi - x) + v[hi] * (x - lo)


def summarize(rows):
    wins = [r for r in rows if r['net'] > 0]
    losses = [r for r in rows if r['net'] < 0]
    out = {
        'trades': len(rows), 'wins': len(wins), 'losses': len(losses),
        'net': round(sum(r['net'] for r in rows), 2),
        'avg_final_r': round(statistics.mean([r['final_r'] for r in rows]), 4) if rows else None,
        'median_mfe_r': round(statistics.median([r['mfe_r'] for r in rows]), 4) if rows else None,
        'median_mae_r': round(statistics.median([r['mae_r'] for r in rows]), 4) if rows else None,
        'median_duration_min': round(statistics.median([r['duration_min'] for r in rows]), 1) if rows else None,
        'winner_mfe_q25': round(q([r['mfe_r'] for r in wins], .25), 4) if wins else None,
        'winner_mfe_median': round(q([r['mfe_r'] for r in wins], .5), 4) if wins else None,
        'winner_mae_median': round(q([r['mae_r'] for r in wins], .5), 4) if wins else None,
        'loser_mfe_median': round(q([r['mfe_r'] for r in losses], .5), 4) if losses else None,
        'loser_mae_median': round(q([r['mae_r'] for r in losses], .5), 4) if losses else None,
        'thresholds': {},
    }
    for t in THRESHOLDS:
        reached = [r for r in rows if r['mfe_r'] >= t]
        losing_after = [r for r in losses if r['mfe_r'] >= t]
        out['thresholds'][str(t)] = {
            'reached': len(reached),
            'reached_pct': round(100 * len(reached) / len(rows), 1) if rows else 0,
            'losers_reached_then_lost': len(losing_after),
            'losers_reached_then_lost_pct_of_losses': round(100 * len(losing_after) / len(losses), 1) if losses else 0,
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', type=Path, required=True)
    ap.add_argument('--out-prefix', type=Path, required=True)
    args = ap.parse_args()
    rows = parse(args.log)
    if not rows:
        raise SystemExit(f'No R8 excursion rows found in {args.log}')
    args.out_prefix.parent.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_prefix.with_suffix('.csv')
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    summary = {
        'all': summarize(rows),
        'buy': summarize([r for r in rows if r['direction'] == 'Buy']),
        'sell': summarize([r for r in rows if r['direction'] == 'Sell']),
    }
    json_path = args.out_prefix.with_suffix('.json')
    json_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    md = ['# BTC Round8 Excursion Summary', '']
    for key in ['all','buy','sell']:
        s = summary[key]
        md += [f'## {key.upper()}', f"Trades {s['trades']} | Wins {s['wins']} | Losses {s['losses']} | Net {s['net']}",
               f"Median MFE {s['median_mfe_r']}R | Median MAE {s['median_mae_r']}R | Median duration {s['median_duration_min']} min", '']
        md += ['| MFE threshold | Reached | Losing trades that reached it then lost |', '|---:|---:|---:|']
        for t in THRESHOLDS:
            z=s['thresholds'][str(t)]
            md.append(f"| {t:.2f}R | {z['reached']} ({z['reached_pct']}%) | {z['losers_reached_then_lost']} ({z['losers_reached_then_lost_pct_of_losses']}% of losses) |")
        md.append('')
    args.out_prefix.with_suffix('.md').write_text('\n'.join(md), encoding='utf-8')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
