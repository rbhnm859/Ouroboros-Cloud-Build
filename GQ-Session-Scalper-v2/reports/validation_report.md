# GQ-Session-Scalper-v2 Validation Report

## Data and protocol

**SIMULATION DATA** — deterministic synthetic OHLC bars; not actual broker data.

- Period: 2026-06-08 to 2026-09-08
- IS: 2026-06-08 to 2026-08-08
- OOS: 2026-08-09 to 2026-09-08
- OOS parameters were frozen before the OOS run.
- Symbols: EURUSD, GBPUSD, XAUUSD, BTCUSD, ETHUSD; primary timeframe M15, trend timeframe H1.
- Costs: symbol-specific simulated spread, commission and 0.2 pip slippage.

## Selected candidate

```json
{
  "name": "c001",
  "ema": 13,
  "momentum": 14,
  "atr": 10,
  "sl_mult": 1.25,
  "tp_r": 1.3,
  "pullback_atr": 0.5,
  "cooldown_min": 30,
  "risk_pct": 0.5
}
```

## Metrics

| Metric | IS | OOS | Overall |
|---|---:|---:|---:|
| trades | 113 | 66 | 179 |
| win_rate_pct | 41.59 | 43.94 | 42.46 |
| net_profit | -572.83 | -218.99 | -784.06 |
| roi_pct | -5.73 | -2.19 | -7.84 |
| pf | 0.833 | 0.888 | 0.853 |
| average_win_loss_ratio | 1.17 | 1.133 | 1.157 |
| average_r | -0.1025 | -0.0639 | -0.0882 |
| max_drawdown_pct | 9.08 | 4.84 | 9.41 |
| max_loss_streak | 8 | 4 | 8 |
| average_holding_minutes | 106.19 | 123.86 | 112.71 |
| total_cost | 425.08 | 294.64 | 709.81 |

### Long/Short

- `long_trades`: IS `55`, OOS `28`, Overall `83`
- `long_net`: IS `-722.26`, OOS `-180.43`, Overall `-890.66`
- `long_pf`: IS `0.609`, OOS `0.796`, Overall `0.67`
- `short_trades`: IS `58`, OOS `38`, Overall `96`
- `short_net`: IS `149.43`, OOS `-38.56`, Overall `106.59`
- `short_pf`: IS `1.094`, OOS `0.964`, Overall `1.04`

## Gate decision

**PROFITABILITY VALIDATION FAILED**

SIMULATION DATA ONLY; broker export and broker-specific costs are required for promotion.

The package deliberately does not emit `PROFITABLE CANDIDATE` because the required broker-specific validation has not been supplied.
