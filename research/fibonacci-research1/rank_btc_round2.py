#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path

CHAMPION = 'btc_champion'

def get(d, *path, default=0.0):
    cur=d
    for k in path:
        if not isinstance(cur, dict): return default
        cur=cur.get(k)
    return default if cur is None else cur

def parse(path: Path):
    d=json.loads(path.read_text(encoding='utf-8'))
    main=d.get('main',{})
    ts=d.get('tradeStatistics',{})
    eq=d.get('equity',{})
    trades=int(get(ts,'totalTrades','all',default=0) or 0)
    wins=int(get(ts,'winningTrades','all',default=0) or 0)
    pf=float(get(ts,'profitFactor','all',default=0) or 0)
    return {
        'trades':trades,
        'wins':wins,
        'win_rate':100.0*wins/trades if trades else 0.0,
        'net':float(main.get('netProfit',0) or 0),
        'roi':float(main.get('roi',0) or 0),
        'dd':float(eq.get('maxEquityDrawdownPercent',0) or 0),
        'pf':pf,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--reports-dir',type=Path,required=True)
    ap.add_argument('--top',type=int,default=4)
    ap.add_argument('--selected-output',type=Path,required=True)
    ap.add_argument('--json-output',type=Path,required=True)
    a=ap.parse_args()
    profiles=json.loads(Path(__file__).with_name('btc_round2_profiles.json').read_text(encoding='utf-8'))
    rows=[]
    for profile in profiles:
        paths=[a.reports_dir/f'{profile}-BITCOIN-DEV1.json', a.reports_dir/f'{profile}-BITCOIN-DEV2.json']
        if not all(p.exists() for p in paths):
            continue
        folds=[parse(p) for p in paths]
        trades=sum(x['trades'] for x in folds)
        wins=sum(x['wins'] for x in folds)
        roi_sum=sum(x['roi'] for x in folds)
        worst_roi=min(x['roi'] for x in folds)
        max_dd=max(x['dd'] for x in folds)
        avg_pf=sum(x['pf'] for x in folds)/len(folds)
        score=2.0*roi_sum + 1.5*worst_roi - 1.1*max_dd + 0.25*min(trades,30) + 1.5*min(avg_pf,3.0)
        if trades < 8: score -= (8-trades)*2.0
        if any(x['trades'] < 2 for x in folds): score -= 4.0
        if worst_roi < -2.0: score -= 3.0*abs(worst_roi+2.0)
        if max_dd > 8.0: score -= 4.0*(max_dd-8.0)
        if avg_pf < 1.0: score -= 8.0*(1.0-avg_pf)
        rows.append({
            'profile':profile,'score':score,'trades':trades,'wins':wins,
            'win_rate':100.0*wins/trades if trades else 0.0,'roi_sum':roi_sum,
            'worst_fold_roi':worst_roi,'max_fold_dd':max_dd,'avg_pf':avg_pf,'folds':folds
        })
    rows.sort(key=lambda r:r['score'],reverse=True)
    selected=[r['profile'] for r in rows[:a.top]]
    if CHAMPION not in selected and any(r['profile']==CHAMPION for r in rows):
        selected.append(CHAMPION)
    a.selected_output.write_text('\n'.join(selected)+'\n',encoding='utf-8')
    a.json_output.write_text(json.dumps({'selected':selected,'ranking':rows},indent=2),encoding='utf-8')
    for i,r in enumerate(rows,1):
        print(f"{i:02d} {r['profile']}: devTrades={r['trades']} roiSum={r['roi_sum']:.2f}% worstROI={r['worst_fold_roi']:.2f}% maxDD={r['max_fold_dd']:.2f}% avgPF={r['avg_pf']:.2f} score={r['score']:.2f}")
    print('SELECTED:', ', '.join(selected))

if __name__=='__main__':
    main()
