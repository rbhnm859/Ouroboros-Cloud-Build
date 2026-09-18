# HARMONYBOT FINAL COMMERCIAL FREEZE — ONE-PASS EXECUTION COMMAND

Repository: rbhnm859/Ouroboros-Cloud-Build
Evidence Run: 35338325244
Evidence result: STRATEGY_ARCHITECTURE_LIMITATION

Execute ONE architecture-level redesign. Do not create V29.6/V29.7/V29.8. Do not tune one version after another.

The failure is not an execution bug. Engineering errors are zero. The bottleneck is regime-dependent strategy edge and payoff conversion.

Freeze all engineering/risk/broker infrastructure. Change only the strategy edge layer.

Mandatory architecture:
1. Restore BUY and SELL. No global direction bias.
2. Harmonic pattern remains the only primary entry setup.
3. Resolve H4/H1/M15 conflicts causally using only completed bars.
4. Never take a harmonic signal opposite a fully aligned H4+H1 regime.
5. Require closed-bar price confirmation for every Development entry, not only SmallAccount mode.
6. Disable the Grid for the commercial freeze candidate. Previous Development executed zero Grid child baskets; do not allow Grid parent management to alter payoff.
7. Disable partial TP and early BE/trailing during Development. Measure the structural >=2R payoff cleanly.
8. Do not use hour lookup tables, date rules, future data, realized PnL, MFE/MAE from future bars, or post-hoc filters.
9. Pre-register P1/P2/P3 before running and do not change them after seeing results.

Run P1/P2/P3 across DEV-A/DEV-B/DEV-C in one job family. Select only if all three windows have PF>1, expectancy>0, net>0, aggregate positive, DD<=10%, execution errors=0 and >=50 baskets/year.

If none passes, stop with STRATEGY_ARCHITECTURE_LIMITATION. Do not invent another profile.

If Development passes, freeze winner and run exactly once:
Validation -> real $100 FxPro XAUUSD 1:500 ticks -> OOS -> quality sensitivity 0.80/0.90/0.95/1.05/1.10/1.20 -> spread/commission/slippage/combined cost stress -> Monte Carlo -> Final Holdout once.

Commercial target:
PF>=2.5, WR>=65%, realized RR>=2, annual ROI>=100%, profitable months>=10/12, actual executable trades>=200/year, DD<=10%.

PASS requires all mandatory gates and all targets.
NEAR_TARGET is allowed only if every mandatory gate including Final Holdout passes and at least PF>=1.5, realized RR>=1.5, annual ROI>=30%, actual executable frequency>=75/year and DD<=10%.
Otherwise HOLD.

Never guarantee profit. Output exact gaps.

Only if PASS or NEAR_TARGET:
- produce final compiled .algo
- record source SHA and algo SHA256
- create commercial freeze report
- keep PR unmerged until evidence is reviewed.

At the end report:
branch, commit SHA, PR, workflow Run ID, selected profile, all Development rows, Validation, $100, OOS, robustness, Final Holdout, final freeze status, and target-gap table.
