# Optimization

Order of work: code/logic baseline -> filter ablation -> session expansion -> A/B signal grading -> multi-symbol opportunity pool -> M5/M15 diversification -> M1 last.

Selection is multi-objective: OOS net profit, PF, drawdown, Avg R/Avg Win-Loss, Return/DD, trade count and cost robustness. Do not select by ROI alone. Prefer parameter plateaus and middle values; reject candidates that collapse under ±5%/±10% perturbation or spread/commission/slippage stress.

Risk test set: 0.25%, 0.50%, 0.75%, 1.00%. TP set: 1.3R, 1.5R, 1.8R, 2.0R, 2.2R, 2.5R. BE set: 0.8R, 1.0R, 1.2R. Trailing modes: ATR, Swing, Chandelier; trigger range 1.3R-1.8R.
