#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit('usage: btc_round3_args.py <profile>')
profile=sys.argv[1]
profiles=json.loads(Path(__file__).with_name('btc_round3_profiles.json').read_text(encoding='utf-8'))
if profile not in profiles:
    raise SystemExit(f'unknown BTC round3 profile: {profile}')
for name,value in profiles[profile].items():
    print(f'--{name}={value}')
