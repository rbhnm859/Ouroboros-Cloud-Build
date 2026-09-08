#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

def val(d, key, side='all', default=0.0):
    v=d.get(key, default)
    if isinstance(v, dict):
        v=v.get(side, default)
    try:
        return float(v)
    except Exception:
        return float(default)

def parse_report(path: Path):
    data=json.loads(path.read_text(encoding='utf-8'))
    main=data.get('main',{})
    eq=data.get('equity',{})
    ts=data.get('tradeStatistics',{})
    name=path.stem
    parts=name.rsplit('-BITCOIN-',1)
    profile=parts[0]
    phase=parts[1] if len(parts)>1 else 'UNKNOWN'
    row={
        'profile':profile,
        'phase':phase,
        'period':main.get('period',''),
        'roi':float(main.get('roi',0) or 0),
        'net':val(ts,'netProfit'),
        'trades':int(val(ts,'totalTrades')),
        'wins':int(val(ts,'winningTrades')),
        'pf':val(ts,'profitFactor'),
        'dd':float(eq.get('maxEquityDrawdownPercent',0) or 0),
        'avg_trade':val(ts,'averageTrade'),
        'long_trades':int(val(ts,'totalTrades','long')),
        'long_wins':int(val(ts,'winningTrades','long')),
        'long_net':val(ts,'netProfit','long'),
        'long_pf':val(ts,'profitFactor','long'),
        'long_avg':val(ts,'averageTrade','long'),
        'short_trades':int(val(ts,'totalTrades','short')),
        'short_wins':int(val(ts,'winningTrades','short')),
        'short_net':val(ts,'netProfit','short'),
        'short_pf':val(ts,'profitFactor','short'),
        'short_avg':val(ts,'averageTrade','short'),
    }
    row['winrate']=100.0*row['wins']/row['trades'] if row['trades'] else 0.0
    row['long_winrate']=100.0*row['long_wins']/row['long_trades'] if row['long_trades'] else 0.0
    row['short_winrate']=100.0*row['short_wins']/row['short_trades'] if row['short_trades'] else 0.0
    row['return_dd']=row['roi']/row['dd'] if row['dd']>0 else 0.0
    return row

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--reports-dir',type=Path,required=True)
    ap.add_argument('--out-json',type=Path,required=True)
    ap.add_argument('--out-csv',type=Path,required=True)
    ap.add_argument('--out-md',type=Path,required=True)
    a=ap.parse_args()
    rows=[]
    for p in sorted(a.reports_dir.glob('*-BITCOIN-*.json')):
        rows.append(parse_report(p))
    a.out_json.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    fields=list(rows[0].keys()) if rows else []
    with a.out_csv.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    phases=['FULL6','FULL6HARSH','FULL3','OOS','OOSHARSH']
    md=['# BTC Round4 MTF cross-test summary','']
    for phase in phases:
        group=[r for r in rows if r['phase']==phase]
        if not group: continue
        md += [f'## {phase}','', '| Profile | TF | Trades | ROI | PF | DD | Return/DD | Buy T/W/PF/Net | Sell T/W/PF/Net |',
               '|---|---:|---:|---:|---:|---:|---:|---|---|']
        group.sort(key=lambda r:(r['roi'],r['pf'],-r['dd']),reverse=True)
        for r in group:
            md.append(f"| {r['profile']} | {r['period']} | {r['trades']} | {r['roi']:.2f}% | {r['pf']:.2f} | {r['dd']:.2f}% | {r['return_dd']:.2f} | {r['long_trades']}/{r['long_winrate']:.1f}%/{r['long_pf']:.2f}/{r['long_net']:+.2f} | {r['short_trades']}/{r['short_winrate']:.1f}%/{r['short_pf']:.2f}/{r['short_net']:+.2f} |")
        md.append('')
    a.out_md.write_text('\n'.join(md),encoding='utf-8')
    print(a.out_md.read_text(encoding='utf-8'))

if __name__=='__main__':
    main()
