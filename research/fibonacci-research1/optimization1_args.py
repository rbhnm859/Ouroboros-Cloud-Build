#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: optimization1_args.py <symbol> <profile>')
symbol, profile = sys.argv[1], sys.argv[2]
path = Path(__file__).with_name('optimization1_profiles.json')
profiles = json.loads(path.read_text(encoding='utf-8'))
try:
    params = profiles[symbol][profile]
except KeyError:
    raise SystemExit(f'unknown optimization profile: {symbol}/{profile}')
for name, value in params.items():
    print(f'--{name}={value}')
