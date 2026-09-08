# Broker / Symbol Preflight — 2026-09-08

- Authentication: PASS (GitHub Secrets + temporary password file; no credential persisted)
- Broker: FxPro
- Environment / account type: False
- Currency: USD
- Leverage: 500

## Generic → broker symbol mapping

- `EURUSD` → `EURUSD`
- `GBPUSD` → `GBPUSD`
- `XAUUSD` → `XAUUSD`
- `BTCUSD` → `BITCOIN`
- `ETHUSD` → `ETHEREUM`
- `USDJPY` → `USDJPY`
- `AUDUSD` → `AUDUSD`

Raw account output is intentionally not stored. Raw symbol catalog is intentionally not committed.
This is a read-only preflight; no orders or positions are created.
