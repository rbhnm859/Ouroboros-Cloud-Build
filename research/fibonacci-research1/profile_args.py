#!/usr/bin/env python3
"""Print cTrader CLI parameter overrides for one research profile."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: profile_args.py <profile>")

    profile_name = sys.argv[1]
    profiles_path = Path(__file__).with_name("profiles.json")
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))

    if profile_name not in profiles:
        raise SystemExit(f"unknown profile: {profile_name}")

    for name, value in profiles[profile_name].items():
        print(f"--{name}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
