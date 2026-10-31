Evidence checked 2026-10-08 UTC

R14 #233 is the empirical failure baseline. The sequence representation hypothesis
is narrower than an assertion that winners are identifiable: temporal summaries
may discard ordering useful for selecting reversal versus continuation. For a
deterministic summary S=g(H), the data-processing inequality gives I(S;Y)<=I(H;Y)
under the corresponding Markov relationship. Strict improvement does not follow;
this experiment must test it on identical event/action opportunities.

Dempster, Schmidt and Webb, MiniRocket (KDD 2021), provide evidence that temporal
kernel transforms with linear heads can be efficient on time-series benchmarks:
https://arxiv.org/abs/2012.08791
The paper does not establish trading alpha or forward-year invariance. The fixed
small kernel bank here is a ROCKET-like diagnostic, not the published MiniRocket
algorithm and not a promised accuracy improvement.

Sagawa, Koh, Hashimoto and Liang (ICLR 2020) show why worst-group training loss
alone does not guarantee group generalization, and motivate regularization:
https://arxiv.org/abs/1911.08731
Our ridge regularization and bounded year reweighting address that failure mode;
only untouched forward research folds can substantiate improvement for XAUUSD.

cTrader documents that bar-close events arrive when the next tick opens a bar:
https://help.ctrader.com/ctrader-algo/documentation/cbots/cbot-bar-events/
The current runtime uses OnBar plus Count-2 on separately loaded M1 Bars; this is
the equivalent completed-bar selection. New telemetry additionally rejects any
index beyond LastClosedIndex and records nominal minute close timestamps. Actual
next-tick observation time can be later, especially across market closures. Exact
live fill/decision latency remains a runtime parity veto; nominal close timestamps
must not be misrepresented as proof of broker execution time.

Falsification: if all outer research years do not reach P@275>=75% with positive
matched information gain, do not evaluate burned OOF. A poor result rejects this
representation/learner combination, not harmonic event supply or the physical
oracle. Negative log-score gains are allowed and are not clipped into success.
The minimum information delta is a preregistered experimental margin, not a
lowered formal Alpha gate. No paper's benchmark figures are imported as expected
performance for this project.
