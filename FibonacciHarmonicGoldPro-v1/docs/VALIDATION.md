# Validation protocol

## Stage 1 - Compile and API validation
1. Build Release with the current `cTrader.Automate` 1.x package.
2. Require 0 compile errors.
3. Verify an `.algo` artifact is produced.
4. Start on an FXPro XAUUSD demo account.
5. Confirm the broker's actual `PipSize`, `TickSize`, `VolumeInUnitsMin/Max/Step`, `MinStopLossDistance`, `MinTakeProfitDistance`, commission and leverage tier.

## Stage 2 - Behavioral tests
- No trade outside configured UTC session.
- No duplicate position for one harmonic D point.
- No entry while any XAUUSD position already exists when `Respect All Symbol Positions=true`.
- Opposite H1/H4 harmonic signal blocks entry.
- Every market entry is submitted with both SL and final TP.
- TP1 partial exit -> break-even modification.
- TP2 partial exit -> structure trailing enabled.
- Daily/weekly loss gates block new entries.
- Max equity drawdown creates persistent hard halt until restart/manual review.
- Insufficient margin, abnormal spread or excessive transaction cost blocks entry.

## Stage 3 - Backtests
Use tick data and realistic broker costs:
- 1 month diagnostic
- 1 year primary IS/OOS split
- 3 years robustness

Do not optimise directly on the full 3-year sample.

Suggested commercial-candidate gates:
- Profit factor > 1.5 OOS; stretch goal > 2.0
- Max drawdown <= 20%; preferred <= 12-15%
- Positive expectancy after spread + commission
- Stable performance across rolling windows
- No single month or pattern family responsible for most total profit
- Enough trades to make statistics meaningful

## Stage 4 - Robustness
- Walk-forward validation.
- Parameter perturbation around selected values.
- Higher spread and slippage stress.
- Monte Carlo trade-order reshuffling.
- Separate results by harmonic pattern family and direction.
