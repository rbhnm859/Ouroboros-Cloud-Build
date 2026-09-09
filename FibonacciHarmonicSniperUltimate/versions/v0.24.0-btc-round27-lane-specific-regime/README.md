# Round27 — Lane-Specific Regime

Round27 is built on the exact-parity Round26 architecture. It changes only two weak lanes:

- H1 Sell: optional H4 EMA regime confirmation.
- M30 Buy: optional H1 EMA regime confirmation.

H1 Buy and M30 Sell remain untouched. Risk allocation, SL/TP, MaxOpenPositions=1 and all anti-grid/martingale/DCA/hedging constraints remain frozen.

## Causal regime modes

Mode 0: off.
Mode 1 (soft): higher-timeframe price OR EMA slope aligns with the trade direction.
Mode 2 (strict): both price and EMA slope must align.

Only the last fully closed higher-timeframe bar is used (`Count-2`), so no future/current-bar lookahead is allowed.

## Pre-committed 3Y screen

Period: 2023-09-08 through 2026-09-08.

Profiles:
- control: H1Sell=0, M30Buy=0
- sell-soft: H1Sell=1, M30Buy=0
- m30buy-strict: H1Sell=0, M30Buy=2
- combined: H1Sell=1, M30Buy=2

A candidate is promotion-eligible only if the full 3Y Standard run has:
- trades >= 240
- ROI > 26.55%
- PF >= 1.30
- max equity DD <= 18.0%

Then the selected candidate is validated on three standalone one-year slices and Harsh costs. Recent-year Standard must retain:
- trades >= 90
- ROI >= 35%
- PF >= 1.80
- max equity DD <= 6%

No period is selected after seeing results. The entire chronological 3Y window and all annual slices are reported regardless of outcome.
