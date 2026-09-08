#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path


def get(d,*path,default=0.0):
    cur=d
    for k in path:
        if not isinstance(cur,dict): return default
        cur=cur.get(k)
        if cur is None: return default
    return cur


def parse(path:Path):
    d=json.loads(path.read_text(encoding='utf-8'))
    main=d.get('main',{})
    eq=d.get('equity',{})
    ts=d.get('tradeStatistics',{})
    return {
      'trades': int(get(ts,'totalTrades','all',default=0) or 0),
      'wins': int(get(ts,'winningTrades','all',default=0) or 0),
      'net': float(main.get('netProfit',0) or 0),
      'roi': float(main.get('roi',0) or 0),
      'dd': float(eq.get('maxEquityDrawdownPercent',0) or 0),
      'pf': float(get(ts,'profitFactor','all',default=0) or 0),
      'short_trades': int(get(ts,'totalTrades','short',default=0) or 0),
      'short_wins': int(get(ts,'winningTrades','short',default=0) or 0),
      'short_net': float(get(ts,'netProfit','short',default=0) or 0),
      'short_pf': float(get(ts,'profitFactor','short',default=0) or 0),
      'short_avg': float(get(ts,'averageTrade','short',default=0) or 0),
      'long_net': float(get(ts,'netProfit','long',default=0) or 0),
      'long_pf': float(get(ts,'profitFactor','long',default=0) or 0),
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--reports-dir',type=Path,required=True)
    ap.add_argument('--top',type=int,default=4)
    ap.add_argument('--selected-output',type=Path,required=True)
    ap.add_argument('--json-output',type=Path,required=True)
    a=ap.parse_args()
    grouped={}
    for p in sorted(a.reports_dir.glob('*-BITCOIN-DEV?.json')):
        stem=p.stem
        phase=stem.rsplit('-',1)[-1]
        profile=stem[:-(len('-BITCOIN-'+phase))]
        grouped.setdefault(profile,{})[phase]=parse(p)
    rows=[]
    for profile,folds in grouped.items():
        if 'DEV1' not in folds or 'DEV2' not in folds: continue
        f1,f2=folds['DEV1'],folds['DEV2']
        avg_roi=(f1['roi']+f2['roi'])/2
        worst_roi=min(f1['roi'],f2['roi'])
        max_dd=max(f1['dd'],f2['dd'])
        min_pf=min(f1['pf'],f2['pf'])
        short_net=f1['short_net']+f2['short_net']
        min_short_pf=min(f1['short_pf'],f2['short_pf'])
        trades=f1['trades']+f2['trades']
        short_trades=f1['short_trades']+f2['short_trades']
        score=2.0*avg_roi + 2.5*worst_roi - 1.4*max_dd + 1.8*min(min_pf,3.0) + 0.20*min(trades,30)
        score += 0.004*short_net + 1.5*min(min_short_pf,3.0) + 0.12*min(short_trades,20)
        if f1['net'] <= 0 or f2['net'] <= 0: score -= 10
        if short_net <= 0: score -= 8
        if max_dd > 6: score -= (max_dd-6)*2.5
        rows.append({'profile':profile,'score':score,'DEV1':f1,'DEV2':f2,'combined':{'trades':trades,'short_trades':short_trades,'avg_roi':avg_roi,'worst_roi':worst_roi,'max_dd':max_dd,'min_pf':min_pf,'short_net':short_net,'min_short_pf':min_short_pf}})
    rows.sort(key=lambda r:r['score'],reverse=True)
    selected=[r['profile'] for r in rows[:a.top]]
    if 'btc_r3_champion' not in selected:
        selected.append('btc_r3_champion')
    a.selected_output.write_text('\n'.join(selected)+'\n',encoding='utf-8')
    a.json_output.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    for i,r in enumerate(rows,1):
        c=r['combined']
        print(f"{i:02d} {r['profile']}: score={r['score']:.2f} trades={c['trades']} avgROI={c['avg_roi']:.2f}% worstROI={c['worst_roi']:.2f}% DD={c['max_dd']:.2f}% PFmin={c['min_pf']:.2f} shortNet={c['short_net']:.2f} shortPFmin={c['min_short_pf']:.2f}")

if __name__=='__main__':
    main()
