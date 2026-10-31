# HarmonyBot V34 — Fresh Validation Reservation

This reservation is committed **before** the first V34 validation execution.

## Frozen source

- Engineering-clean baseline commit: `bf277db05ce303a3e1184b6be8b28868cbe9e69a`
- Source: `HarmonyBot-V34/src/HarmonyBotV34.cs`
- Expected Git blob SHA: `f404767c70bdf5032b8d5c1fc2be9e81b9a97947`
- Strategy, Harmonic ratios, Fibonacci levels, Grid weights, entry logic, risk parameters and lifecycle rules are frozen for this validation.

## Fresh Validation reservation

- ID: `V34-VAL-FRESH-2020H1`
- Start: **2020-01-02**
- Evaluation start: **2020-01-09T00:00:00Z**
- End: **2020-06-30**
- Symbol: **XAUUSD**
- Broker/account guard: **FxPro demo, USD, 1:500**
- Track A: **Normal Capital — USD 10,000**
- Track B: **Micro Capital — USD 100**

Repository code/workflow search and repository issue/PR search found no HarmonyBot references to this H1-2020 interval. This is therefore classified **AUDITABLY_UNEXPOSED_RESERVED_BEFORE_EXECUTION**, not as an absolute claim about unknown off-repository activity.

2020-H2 is explicitly excluded: repository workflows now show it was used by prior HarmonyBot research.

## Pre-registered Stage-1 gate

Each track is evaluated independently. No pooled PF, Net or DD.

- at least 10 completed baskets; otherwise `INSUFFICIENT_SAMPLE`
- PF > 1.0
- Net > 0
- Expectancy > 0
- Max Equity DD <= 10%
- Engineering Clean = true
- broker profile present
- V34 summary present
- basket activity present
- all execution/risk safety invariants remain zero

This is PASS/FAIL evidence only. Results may not be used to retune thresholds, Fibonacci levels, Harmonic ratios, Grid weights, pattern blacklists or risk parameters against this interval.

## Protected Final Holdout

`2023-01-02 .. 2023-08-31` remains reserved and **must not** be used by this validation workflow.
