#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit('usage: btc_round2_args.py <profile>')
profile = sys.argv[1]
path = Path(__file__).with_name('btc_round2_profiles.json')
profiles = json.loads(path.read_text(encoding='utf-8'))
if profile not in profiles:
    raise SystemExit(f'unknown BTC round2 profile: {profile}')
for name, value in profiles[profile].items():
    print(f'--{name}={value}')
