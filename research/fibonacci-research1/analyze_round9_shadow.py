#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, statistics
from pathlib import Path

RX = re.compile(r"\[R9 SHADOW\]\s+id=(?P<id>\d+)\s+dir=(?P<dir>Buy|Sell)\s+pattern=(?P<pattern>\S+)\s+riskPips=(?P<risk>[0-9.]+)\s+max6R=(?P<m6>-?[0-9.]+)\s+max12R=(?P<m12>-?[0-9.]+)\s+max24R=(?P<m24>-?[0-9.]+)\s+max48R=(?P<m48>-?[0-9.]+)\s+minPostR=(?P<min>-?[0-9.]+)\s+hit20Min=(?P<h20>-?[0-9.]+)\s+hit22Min=(?P<h22>-?[0-9.]+)\s+hit25Min=(?P<h25>-?[0-9.]+)\s+horizonH=(?P<horizon>\d+)")


def parse(path: Path):
    rows=[]
    for line in path.read_text(encoding='utf-8',errors='ignore').splitlines():
        m=RX.search(line)
        if not m: continue
        d=m.groupdict()
        rows.append({
            'id':int(d['id']),'direction':d['dir'],'pattern':d['pattern'],'risk_pips':float(d['risk']),
            'max6_r':float(d['m6']),'max12_r':float(d['m12']),'max24_r':float(d['m24']),'max48_r':float(d['m48']),
            'min_post_r':float(d['min']),'hit20_min':float(d['h20']),'hit22_min':float(d['h22']),'hit25_min':float(d['h25']),
            'horizon_h':int(d['horizon'])})
    return rows


def summarize(rows):
    if not rows: return {'shadows':0}
    out={'shadows':len(rows),'median_max48_r':round(statistics.median(r['max48_r'] for r in rows),4),'median_min_post_r':round(statistics.median(r['min_post_r'] for r in rows),4),'horizons':{}}
    for h,key in [(6,'max6_r'),(12,'max12_r'),(24,'max24_r'),(48,'max48_r')]:
        z={}
        for t in [2.0,2.2,2.5]:
            n=sum(1 for r in rows if r[key]>=t)
            z[str(t)]={'reached':n,'pct':round(100*n/len(rows),1)}
        out['horizons'][str(h)]=z
    for t,key in [(2.0,'hit20_min'),(2.2,'hit22_min'),(2.5,'hit25_min')]:
        hits=[r[key] for r in rows if r[key]>=0]
        out[f'hit_{t}_count']=len(hits)
        out[f'hit_{t}_pct']=round(100*len(hits)/len(rows),1)
        out[f'hit_{t}_median_min']=round(statistics.median(hits),1) if hits else None
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--log',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    rows=parse(a.log)
    if not rows: raise SystemExit('No completed R9 SHADOW rows found')
    summary={'all':summarize(rows),'buy':summarize([r for r in rows if r['direction']=='Buy']),'sell':summarize([r for r in rows if r['direction']=='Sell'])}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    md=['# BTC Round9 TP Shadow Continuation','']
    for side in ['all','buy','sell']:
        s=summary[side]; md += [f'## {side.upper()}',f"Completed shadows: {s.get('shadows',0)}"]
        if s.get('shadows',0):
            md += [f"Median max 48h: {s['median_max48_r']}R | Median post-TP minimum: {s['median_min_post_r']}R",'','| Horizon | >=2.0R | >=2.2R | >=2.5R |','|---:|---:|---:|---:|']
            for h in ['6','12','24','48']:
                z=s['horizons'][h]; md.append(f"| {h}h | {z['2.0']['reached']} ({z['2.0']['pct']}%) | {z['2.2']['reached']} ({z['2.2']['pct']}%) | {z['2.5']['reached']} ({z['2.5']['pct']}%) |")
            md.append('')
    a.out.with_suffix('.md').write_text('\n'.join(md),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
