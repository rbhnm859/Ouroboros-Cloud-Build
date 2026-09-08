# Backtests

Target window: 2026-06-08 through 2026-09-08 UTC.

Protocol: prefer cTrader server Tick data; use 2026-06-08 through 2026-08-08 as IS and 2026-08-09 through 2026-09-08 as OOS. Freeze parameters before OOS. M5 and M15 are primary; M1 is evaluated only after cost-adjusted M5/M15 results justify it. Baseline session is 08:00-16:00 UTC. Reports must state symbol mapping, spread, commission, slippage/data mode and whether broker metadata was verified.

Never label synthetic or open-price simulation as broker Tick validation.
