# ChatGPT × Codex Cloud handoff — integration v2

State: configuration staged on a **separate integration branch**. This does not modify the source V74 branch, enable ChatGPT automatic mode switching, or create a Codex Cloud task.

## Realistic native-plus route
1. ChatGPT interprets intent and uses already-authorized tools. The private `harmonybot-master` v0.2.0 plugin adds Intent Router, Codex Handoff and Runtime Evidence while preserving previous source-locked modules.
2. In Codex Cloud (web/desktop), connect GitHub repository `rbhnm859/Ouroboros-Cloud-Build`; create and publish a reusable environment after checking actual .NET/cTrader toolchain. Mobile can start tasks after publication.
3. For an actual cloud task, submit a complete scoped request through supported Codex UI. General ChatGPT chat currently has no verified native direct consumer-Codex task launcher.
4. For new cBot work, allocate a separate project branch before writing. Do not edit V74 under its new requirements.
5. Work in isolated branch -> PR -> matching CI receipts -> independent validation. No auto merge or production trading.

## Test and acceptance
Pure Python advisory classifier: `python integrations/codex_router/test_route.py` (no dependencies, no network). Not a C# compile or market backtest.
Acceptance: CONFIGURED -> TOOL_AUTH_VERIFIED -> CODEX_STARTED (task ID) -> CI_PASS -> CTRADER_RUNTIME_VERIFIED -> OOF_GATE_PASS -> FINAL_ACCEPTED. Missing evidence means NOT VERIFIED or BLOCKED.

## Budget and security
No newly paid API, Railway deployment, auto-trading, secrets, forced pushes or branch deletions. OpenAI Agents API is a separately metered product, not ChatGPT Plus Codex Cloud credits. Do not mistake an advisory intent route for an authorization boundary.

## Set-up reference
https://help.openai.com/en/articles/20001545-using-codex-cloud
