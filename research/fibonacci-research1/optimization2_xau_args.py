#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
if len(sys.argv)!=2: raise SystemExit('usage: optimization2_xau_args.py <profile>')
profiles=json.loads(Path(__file__).with_name('optimization2_xau_profiles.json').read_text(encoding='utf-8'))
profile=sys.argv[1]
if profile not in profiles: raise SystemExit(f'unknown profile: {profile}')
for k,v in profiles[profile].items(): print(f'--{k}={v}')
