#!/usr/bin/env python3
import csv, json, math, statistics, sys
from collections import defaultdict
from datetime import datetime

if len(sys.argv) != 3:
    raise SystemExit('usage: monthly_compound_report.py <trades.csv> <out.json>')

src, out = sys.argv[1:]
rows = list(csv.DictReader(open(src, newline='', encoding='utf-8-sig')))

def first(row, names):
    for n in names:
        if n in row and row[n] not in ('', None): return row[n]
    return None

def parse_dt(v):
    if not v: return None
    v=v.strip().replace('Z','+00:00')
    for f in (None,'%Y-%m-%d %H:%M:%S','%Y-%m-%dT%H:%M:%S'):
        try: return datetime.fromisoformat(v) if f is None else datetime.strptime(v,f)
        except ValueError: pass
    return None

monthly=defaultdict(float)
for r in rows:
    dt=parse_dt(first(r,['Closing Time','Close Time','CloseTime','closingTime','exit_time','ExitTime']))
    pnl=first(r,['Net Profit','NetProfit','netProfit','net_profit','Profit','profit'])
    if dt is None or pnl is None: continue
    try: monthly[dt.strftime('%Y-%m')] += float(str(pnl).replace(',',''))
    except ValueError: pass

initial = 10000.0
balance=initial
returns=[]
table=[]
for month in sorted(monthly):
    start=balance
    pnl=monthly[month]
    r=pnl/start if start else 0.0
    balance += pnl
    returns.append(r)
    table.append({'month':month,'start_balance':round(start,2),'net_profit':round(pnl,2),'return_pct':round(r*100,4),'end_balance':round(balance,2)})

if returns:
    product=math.prod(1+r for r in returns)
    geo=product**(1/len(returns))-1 if product>0 else -1.0
    positive=sum(r>0 for r in returns)/len(returns)
    median=statistics.median(returns)
    std=statistics.pstdev(returns) if len(returns)>1 else 0.0
    worst=min(returns)
    streak=cur=0
    for r in returns:
        cur=cur+1 if r<0 else 0
        streak=max(streak,cur)
else:
    geo=positive=median=std=worst=0.0; streak=0

report={
 'initial_balance':initial,
 'ending_balance':round(balance,2),
 'months':len(returns),
 'geometric_monthly_return_pct':round(geo*100,4),
 'median_monthly_return_pct':round(median*100,4),
 'worst_month_pct':round(worst*100,4),
 'positive_month_pct':round(positive*100,2),
 'monthly_return_std_pct':round(std*100,4),
 'longest_losing_month_streak':streak,
 'monthly':table
}
open(out,'w',encoding='utf-8').write(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='monthly'},indent=2))
