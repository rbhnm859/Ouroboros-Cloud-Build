#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path


def metric(d, path, default=0.0):
    cur=d
    for k in path:
        if not isinstance(cur, dict): return default
        cur=cur.get(k)
    return default if cur is None else cur


def parse(path: Path, symbol: str, phase: str):
    d=json.loads(path.read_text(encoding='utf-8'))
    main=d.get('main',{})
    ts=d.get('tradeStatistics',{})
    eq=d.get('equity',{})
    trades=int(metric(ts,['totalTrades','all'],0) or 0)
    wins=int(metric(ts,['winningTrades','all'],0) or 0)
    net=float(main.get('netProfit',0) or 0)
    roi=float(main.get('roi',0) or 0)
    dd=float(eq.get('maxEquityDrawdownPercent',0) or 0)
    pf=float(metric(ts,['profitFactor','all'],0) or 0)
    win_rate=100*wins/trades if trades else 0.0
    stem=path.stem
    suffix=f'-{symbol}-{phase}'
    if not stem.endswith(suffix):
        raise ValueError(f'unexpected filename: {path.name}')
    profile=stem[:-len(suffix)]
    score=2.5*roi - 1.2*dd + 0.35*min(trades,25) + min(pf,3.0)
    if trades < 5: score -= (5-trades)*2.5
    if net <= 0: score -= 8.0
    if dd > 8.0: score -= (dd-8.0)*3.0
    return dict(profile=profile,trades=trades,wins=wins,win_rate=win_rate,net_profit=net,roi=roi,max_dd=dd,pf=pf,score=score)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--reports-dir',type=Path,required=True)
    ap.add_argument('--symbol',required=True)
    ap.add_argument('--phase',required=True)
    ap.add_argument('--top',type=int,default=3)
    ap.add_argument('--selected-output',type=Path,required=True)
    ap.add_argument('--json-output',type=Path,required=True)
    a=ap.parse_args()
    rows=[]
    for p in sorted(a.reports_dir.glob(f'*-{a.symbol}-{a.phase}.json')):
        rows.append(parse(p,a.symbol,a.phase))
    rows.sort(key=lambda r:r['score'],reverse=True)
    a.selected_output.write_text('\n'.join(r['profile'] for r in rows[:a.top])+'\n',encoding='utf-8')
    a.json_output.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(f'Ranking {a.symbol} {a.phase}')
    for i,r in enumerate(rows,1):
        print(f"{i:02d} {r['profile']}: trades={r['trades']} roi={r['roi']:.2f}% dd={r['max_dd']:.2f}% pf={r['pf']:.2f} score={r['score']:.2f}")

if __name__=='__main__':
    main()
