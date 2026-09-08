#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

def parse(p:Path):
    d=json.loads(p.read_text(encoding='utf-8')); main=d.get('main',{}); ts=d.get('tradeStatistics',{}); eq=d.get('equity',{})
    trades=int(ts.get('totalTrades',{}).get('all',0) or 0); wins=int(ts.get('winningTrades',{}).get('all',0) or 0)
    roi=float(main.get('roi',0) or 0); net=float(main.get('netProfit',0) or 0); dd=float(eq.get('maxEquityDrawdownPercent',0) or 0); pf=float(ts.get('profitFactor',{}).get('all',0) or 0)
    m=p.stem.rsplit('-XAUUSD-',1)[0]; tf=p.stem.rsplit('-XAUUSD-',1)[1].replace('-FULL','')
    score=2.5*roi-1.5*dd+0.08*min(trades,80)+min(pf,3)
    if net<=0: score-=10
    if trades<12: score-=(12-trades)*0.8
    if dd>10: score-=(dd-10)*4
    return {'profile':m,'timeframe':tf,'trades':trades,'wins':wins,'win_rate':100*wins/trades if trades else 0,'net_profit':net,'roi':roi,'max_dd':dd,'pf':pf,'score':score}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--reports-dir',type=Path,required=True); ap.add_argument('--top',type=int,default=4); ap.add_argument('--selected-output',type=Path,required=True); ap.add_argument('--json-output',type=Path,required=True); a=ap.parse_args()
    rows=[parse(p) for p in a.reports_dir.glob('*-XAUUSD-*-FULL.json')]
    rows.sort(key=lambda r:r['score'],reverse=True)
    a.json_output.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    a.selected_output.write_text('\n'.join(f"{r['profile']}|{r['timeframe']}" for r in rows[:a.top])+'\n',encoding='utf-8')
    for i,r in enumerate(rows,1): print(f"{i:02d} {r['profile']} {r['timeframe']}: trades={r['trades']} roi={r['roi']:.2f}% dd={r['max_dd']:.2f}% pf={r['pf']:.2f} score={r['score']:.2f}")
if __name__=='__main__': main()
