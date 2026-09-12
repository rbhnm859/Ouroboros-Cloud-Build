# HarmonyBotPro v27 Commercial RC

Architecture goals:
- cTrader native risk sizing (VolumeForFixedRisk / AmountRisked / PipsForFixedRisk)
- projected daily / weekly / max-DD pre-trade risk budget
- small-account stop compression bounded by actual 0.01-lot risk budget
- small-account grid guard retained
- min-volume partial TP safety and fresh-position lifecycle
- broker-native margin estimation
- grid basket projected risk via native AmountRisked
- commercial diagnostics counters

This branch is a release-candidate engineering branch. It is not declared profitable or final until IS/OOS and higher-fidelity backtests pass.
