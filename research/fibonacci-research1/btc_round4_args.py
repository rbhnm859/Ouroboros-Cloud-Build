#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

PROFILE_FILE = Path(__file__).with_name('btc_round4_mtf_profiles.json')

# Profile JSON keeps the human-friendly MTF acronym; cTrader CLI binds to the C# property name.
KEY_MAP = {
    'MTFMode': 'MtfMode',
}

BASE_ARGS = {
    'EnabledPatterns': 'Reciprocal ABCD',
    'MinPatternScore': '84',
    'RatioTolerancePercent': '6',
    'PivotLeft': '2',
    'PivotRight': '2',
    'MaxPatternAgeBars': '16',
    'MaxEntryDistanceAtr': '1.80',
    'ConfirmationMoveAtr': '0.05',
    'CooldownBars': '2',
    'StopAnchorMode': 'LegacyD',
    'TargetRiskRewardPolicy': 'LegacyFallback',
    'FallbackRiskReward': '1.80',
    'MinimumRiskReward': '1.50',
    'MaxOpenPositions': '1',
}

def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit('usage: btc_round4_args.py PROFILE')
    name = sys.argv[1]
    profiles = json.loads(PROFILE_FILE.read_text(encoding='utf-8'))
    if name not in profiles:
        raise SystemExit(f'unknown profile: {name}')
    profile = profiles[name]
    print(f"__PERIOD__={profile['execution_period']}")
    args = dict(BASE_ARGS)
    args.update(profile.get('parameters', {}))
    for key, value in args.items():
        cli_key = KEY_MAP.get(key, key)
        if isinstance(value, bool):
            value = str(value).lower()
        print(f'--{cli_key}={value}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
