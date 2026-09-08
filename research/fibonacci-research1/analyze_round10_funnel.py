#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

RX=re.compile(r"\[R10 FUNNEL\]\s+([^=]+)=(\d+)")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--log',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    counts={}
    for line in a.log.read_text(encoding='utf-8',errors='ignore').splitlines():
        m=RX.search(line)
        if m: counts[m.group(1).strip()]=int(m.group(2))
    if not counts: raise SystemExit('No R10 FUNNEL counters found')
    near={k:v for k,v in counts.items() if any(x in k for x in ['score_miss_0_2','score_miss_2_4','age_miss_0_2','age_miss_2_4','entry_distance_miss_0_02','entry_distance_miss_02_04'])}
    rejects={k:v for k,v in counts.items() if ('reject' in k or 'miss' in k or 'duplicate' in k)}
    result={'counts':dict(sorted(counts.items(),key=lambda kv:(-kv[1],kv[0]))),'near_miss':dict(sorted(near.items(),key=lambda kv:(-kv[1],kv[0]))),'rejections':dict(sorted(rejects.items(),key=lambda kv:(-kv[1],kv[0])))}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    md=['# BTC Round10 Signal Rejection Funnel','','## Top counters','','| Counter | Count |','|---|---:|']
    for k,v in list(result['counts'].items())[:30]: md.append(f'| {k} | {v} |')
    md += ['','## Near-miss opportunities','','| Counter | Count |','|---|---:|']
    for k,v in result['near_miss'].items(): md.append(f'| {k} | {v} |')
    a.out.with_suffix('.md').write_text('\n'.join(md),encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
