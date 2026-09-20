# PR #4 compatibility patch reasons

1. Keep namespace, Robot class, AccessRights.None and six-argument market-order overload; real API compilation confirms compatibility.
2. Interpret MinStopLossDistance/MinTakeProfitDistance using MinDistanceType; original compared pips or percentage to raw price distance and could reject valid orders.
3. Use explicit absolute ModifyPosition overload; retain TP, round stops to tick size, check broker minimum and throttle retries to reduce InvalidRequest failures.
4. Use account-wide position/pending-order entry gate, eliminating different-label bypass within this instance. No add-on/averaging entry paths added.
5. Validate finite ATR, distances and volume; warm up indicators; verify money risk after normalization and available margin before order submission.
6. Check post-fill/tick protection and latch entry shutdown with emergency close attempt if protection is absent.
7. Use completed-bar ATR/EMA/ADX; advance previous cumulative delta on every completed bar, even when guards block trading, to avoid stale threshold crossings. Duplicate bar callbacks cannot finalize the delta buffer twice.
8. Enforce EURUSD independently of the configurable prefix; qualify TimeFrame enum names.
9. Recover daily trade count, loss streak and cooldown from History; count unique entry position IDs rather than closure records; recover managed time exit from actual EntryTime.
10. Remove O(history) work from every tick; refresh at startup, bar, day rollover and managed close events.
11. Independent zero-disable daily money/percent limits, realized-plus-floating loss latch, remaining entry risk budget. Daily profit remains a realized entry guard.
12. Use UTC Server.Time directly; avoid a second local-time conversion.
13. Add isolated net6.0 project and pinned official cTrader.Automate 1.0.19. Correct copy target ordering and package-specific intermediate filename based on actual failed packaging attempt; subsequent build produced real .algo.
14. Add bounded four-timeframe tick sanity workflow and evidence-preserving JSON normalizer; no simulated results substituted for missing broker tests.

Original provenance files and all other bot directories are unchanged. Initial C# compilation found no missing API member in the original signatures; the substantive changes fix API semantics/runtime guards and modernize the obsolete protection overload. See build_result.md for actual compiler evidence, distinct from runtime acceptance.
