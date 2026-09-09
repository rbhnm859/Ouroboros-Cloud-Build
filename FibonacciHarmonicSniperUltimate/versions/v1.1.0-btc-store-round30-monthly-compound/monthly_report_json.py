#!/usr/bin/env python3
import calendar, json, math, statistics, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: monthly_report_json.py <report.json> <out.json>')
src,out=sys.argv[1:]
r=json.loads(Path(src).read_text())
main=r['main']; start=float(main['startingCapital'])
start_ms=int(main['testingPeriod']['startDate']); end_ms=int(main['testingPeriod']['endDate'])
start_dt=datetime.fromtimestamp(start_ms/1000,tz=timezone.utc); end_dt=datetime.fromtimestamp(end_ms/1000,tz=timezone.utc)
items=sorted(r['history']['items'], key=lambda x:(x['closeTime'],x.get('id',0)))
monthly=defaultdict(float)
for x in items:
    dt=datetime.fromtimestamp(int(x['closeTime'])/1000,tz=timezone.utc)
    monthly[dt.strftime('%Y-%m')]+=float(x['net'])

balance=start; table=[]; all_returns=[]; full_returns=[]
for month in sorted(monthly):
    y,m=map(int,month.split('-')); pnl=monthly[month]; month_start=balance
    ret=pnl/month_start if month_start else 0.0
    balance+=pnl
    first=datetime(y,m,1,tzinfo=timezone.utc)
    last_day=calendar.monthrange(y,m)[1]
    after=datetime(y+1,1,1,tzinfo=timezone.utc) if m==12 else datetime(y,m+1,1,tzinfo=timezone.utc)
    is_full=(start_dt<=first and end_dt>=after)
    all_returns.append(ret)
    if is_full: full_returns.append(ret)
    table.append({'month':month,'full_calendar_month':is_full,'start_balance':round(month_start,2),'net_profit':round(pnl,2),'return_pct':round(ret*100,4),'end_balance':round(balance,2)})

def geom(vals):
    if not vals:return None
    p=math.prod(1+x for x in vals)
    return -1.0 if p<=0 else p**(1/len(vals))-1

def stats(vals):
    if not vals:return {'count':0}
    return {
      'count':len(vals),
      'geometric_pct':round(geom(vals)*100,4),
      'median_pct':round(statistics.median(vals)*100,4),
      'worst_pct':round(min(vals)*100,4),
      'best_pct':round(max(vals)*100,4),
      'positive_pct':round(100*sum(x>0 for x in vals)/len(vals),2),
      'std_pct':round((statistics.pstdev(vals) if len(vals)>1 else 0)*100,4),
    }

days=max(1.0,(end_dt-start_dt).total_seconds()/86400)
total_factor=balance/start if start>0 else 1.0
duration_months=days/30.4375
duration_geo=(total_factor**(1/duration_months)-1) if total_factor>0 else -1.0
streak=cur=0
for x in full_returns:
    cur=cur+1 if x<0 else 0; streak=max(streak,cur)
report={
 'starting_capital':start,
 'ending_balance_from_history':round(balance,2),
 'report_ending_balance':float(main['endingBalance']),
 'trades':len(items),
 'roi_pct':float(main['roi']),
 'testing_start_utc':start_dt.isoformat(),
 'testing_end_utc':end_dt.isoformat(),
 'duration_days':round(days,4),
 'duration_normalized_geometric_monthly_pct':round(duration_geo*100,4),
 'all_calendar_buckets':stats(all_returns),
 'full_calendar_months_only':stats(full_returns),
 'longest_full_losing_month_streak':streak,
 'monthly':table
}
Path(out).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='monthly'},indent=2))
