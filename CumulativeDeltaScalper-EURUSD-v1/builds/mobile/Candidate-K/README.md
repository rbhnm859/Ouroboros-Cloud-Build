# Candidate K Mobile Build

- Product: CumulativeDeltaScalper EURUSD M1 Candidate K
- Historical K validation head: ca6d78774eb7f772d32e19e537a9584a5cfc5400
- Historical K workflow run: 34405972113
- Target: cTrader Mobile / Cloud importable .algo
- Framework: net6.0
- Access rights: None
- Symbol: EURUSD
- Timeframe default: M1 only in this Mobile archive
- Starting-capital profile: USD 30
- Strategy exclusions: no grid, martingale, DCA, recovery, loss averaging, or hedge stacking
- SHA256: 294bd228ff9c4bcdfa228720bd899287229aac80424580ec731aaf575e40a2c6

Candidate K parameters are embedded as defaults in the archived source and the original K preset is shipped beside the .algo.
The historical K backtest used cTrader console M1 data mode and did not explicitly model the later Q2 realistic spread/commission test, so its historical ROI should not be treated as a live-performance guarantee.
