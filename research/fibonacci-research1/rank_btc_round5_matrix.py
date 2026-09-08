#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path


def nested(d, *keys, default=0.0):
    cur=d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur=cur[k]
    return cur


def num(v, default=0.0):
    try:
        x=float(v)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def metric_obj(v, key='all'):
    if isinstance(v, dict):
        return num(v.get(key,0))
    return num(v)


def parse_report(path: Path):
    d=json.loads(path.read_text(encoding='utf-8'))
    ts=d.get('tradeStatistics',{})
    total=metric_obj(ts.get('totalTrades',0))
    wins=metric_obj(ts.get('winningTrades',0))
    pf=metric_obj(ts.get('profitFactor',0))
    buy_trades=metric_obj(ts.get('totalTrades',0),'long')
    sell_trades=metric_obj(ts.get('totalTrades',0),'short')
    buy_pf=metric_obj(ts.get('profitFactor',0),'long')
    sell_pf=metric_obj(ts.get('profitFactor',0),'short')
    net_obj=ts.get('netProfit',{})
    buy_net=metric_obj(net_obj,'long') if isinstance(net_obj,dict) else 0.0
    sell_net=metric_obj(net_obj,'short') if isinstance(net_obj,dict) else 0.0
    return {
      'trades':int(total),'wins':int(wins),'win_rate':(100*wins/total if total else 0.0),
      'roi':num(nested(d,'main','roi')),'net':num(nested(d,'main','netProfit')),
      'pf':pf,'dd':num(nested(d,'equity','maxEquityDrawdownPercent')),
      'buy_trades':int(buy_trades),'sell_trades':int(sell_trades),
      'buy_pf':buy_pf,'sell_pf':sell_pf,'buy_net':buy_net,'sell_net':sell_net
    }


def score(m):
    s=1.6*m['roi'] + 1.4*min(m['pf'],5.0) - 0.8*m['dd'] + 0.12*min(m['trades'],30)
    if m['roi'] <= 0: s -= 12
    if m['pf'] < 1: s -= 8
    if m['trades'] < 3: s -= (3-m['trades'])*3
    return s


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--cells',required=True,type=Path)
    ap.add_argument('--reports-dir',required=True,type=Path)
    ap.add_argument('--ranking-output',required=True,type=Path)
    ap.add_argument('--selected-output',required=True,type=Path)
    a=ap.parse_args()
    cells=json.loads(a.cells.read_text(encoding='utf-8'))
    rows=[]
    for c in cells:
        p=a.reports_dir/f"dev-{c['id']}-BITCOIN.json"
        if not p.exists():
            rows.append({**c,'missing':True,'score':-1e9})
            continue
        m=parse_report(p)
        rows.append({**c,**m,'score':score(m)})
    periods=[]
    for c in cells:
        if c['period'] not in periods: periods.append(c['period'])
    selected=[]
    for period in periods:
        group=[r for r in rows if r['period']==period and not r.get('missing')]
        if not group: continue
        group.sort(key=lambda r:r['score'], reverse=True)
        best=group[0]
        qualifies=best['trades']>=2 and best['roi']>0 and best['pf']>1
        if qualifies or best['id']=='h1_recip':
            selected.append({k:best[k] for k in ('id','period','pattern','tier')})
    if not any(x['id']=='h1_recip' for x in selected):
        anchor=next(c for c in cells if c['id']=='h1_recip')
        selected.append(anchor)
    ranking={'rows':sorted(rows,key=lambda r:(r['period'],-r['score'])),'selected':selected}
    a.ranking_output.write_text(json.dumps(ranking,indent=2),encoding='utf-8')
    a.selected_output.write_text(json.dumps({'include':selected},separators=(',',':')),encoding='utf-8')
    print(json.dumps({'selected':selected},indent=2))

if __name__=='__main__': main()
