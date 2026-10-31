# HarmonyBot V72 HCAP — Terminal Negative Evidence

Source candidate: `harmonybot/v72-candidate-harmonic-counterfactual-action-policy`
Terminal source SHA: `a326e4e28ee5838cdb6fabd3c75cc192d46a6b83`
Formal workflow: HarmonyBot V72 One-Shot Harmonic Counterfactual Action Policy
Run: #197 / 36802880635

## Integrity

- Build: PASS
- V51 reference 2021/2022/2023: PASS
- Protected-core exact replay 2021/2022/2023: PASS
- Replay gate: PASS
- HCAP shadow 2021/2022/2023: completed successfully
- Validation used: false
- Fresh used: false

## Terminal HCAP result

The HCAP strategy gate failed. This is a strategy rejection, not a CI failure.

Temporal OOF selected total: 85 opportunities.

Observed OOF year summaries:

- 2021: mean R +0.2484355714, PF_R 1.3623018750, LCB -0.3266615392, WR 31.43%.
- 2022: mean R +0.1798444000, PF_R 1.2420982308, LCB -0.4816779131, WR 25.71%.
- 2023: mean R +1.1400474000, PF_R 2.7100711000, LCB -0.9991080924, WR 33.33%.

Gate semantics were preregistered as: each burned year N >= 60, Mean R > 0, PF_R > 1, one-sided 95% LCB > 0, with no threshold rescue.

Final decision:

`HCAP_CAUSAL_ALPHA_REJECT`
`candidate = null`
`V71_TERMINAL_REJECT_NO_V72`

Therefore HCAP is frozen as negative evidence. No threshold, LCB, family, or year-specific rescue is permitted.

## Forward rule

V73 is not an HCAP patch. It only addresses opportunity-universe supply and governed data coverage. Formal version numbers advance only after a preregistered evidence gate passes.
