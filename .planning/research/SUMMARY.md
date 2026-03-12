# Project Research Summary

**Project:** slack-computer
**Domain:** Python Slack bot with real-time web search via Perplexity Agent API (Socket Mode)
**Researched:** 2026-03-13
**Confidence:** HIGH

## Executive Summary

This project is a single-workspace Slack bot that routes questions to Perplexity's `pro-search` Agent API and returns cited, web-grounded answers in threaded replies. The research consensus is clear: use Slack Bolt for Python with Socket Mode. This combination eliminates the need for a public HTTPS endpoint, handles the 3-second acknowledgment deadline automatically through Bolt's event listener framework, and runs on localhost with zero infrastructure. The Perplexity `perplexityai` SDK (not a generic OpenAI-compatible client) is the correct integration point because it exposes `preset="pro-search"`, the `output_text` convenience property, and the typed `search_results` output items that power citation display.

The recommended architecture is a thin, modular Python project: a `services/perplexity.py` layer isolates all SDK calls and returns plain Python data to handlers; four event handlers (DM, `@mention`, `/ask` slash command, App Home) each live in their own file under `handlers/`; a `utils/formatting.py` module handles Slack mrkdwn conversion. This separation makes each handler testable without a live API connection and keeps the SDK upgrade surface confined to a single file.

The highest-risk surface is the interaction between Slack's strict timing model and Perplexity's variable latency. Three pitfalls — missing the 3-second `ack()` deadline, blocking the event loop with a synchronous Perplexity call, and the bot responding to its own messages — must all be addressed in the first implementation phase or they compound into a broken, looping bot that is difficult to debug. All three have clear, low-effort fixes documented in PITFALLS.md and must be treated as non-negotiable implementation requirements, not polish tasks.

---

## Key Findings

### Recommended Stack

The stack is lean and purpose-fit. All versions were verified against PyPI on 2026-03-13. No alternatives are recommended — the choices are well-justified against documented tradeoffs.

**Core technologies:**
- **Python 3.11+**: Runtime — 3.11 LTS gives asyncio improvements and better error messages; required by `perplexityai` SDK (3.8+ minimum)
- **slack_bolt 1.27.0**: Slack app framework — official SDK; `SocketModeHandler` is built-in; handles ack deadline boilerplate; no alternative offers this
- **slack_sdk 3.41.0**: Slack Web API client — auto-installed as a bolt dependency; needed directly for `chat_postMessage` (to capture `ts` for threading) and `views_publish`
- **perplexityai 0.30.1**: Perplexity Agent API client — official SDK; exposes `preset="pro-search"`, `output_text`, and `search_results` typed output; auto-reads `PERPLEXITY_API_KEY` from env
- **python-dotenv 1.2.2**: Secret management — loads `.env` at startup; is a no-op when env vars are already set (compatible with CI/CD)

**Critical version notes:** Do not pin `slack_sdk` independently — it is a declared dependency of `slack_bolt` and the compatible version installs automatically. Do not use the `slack` PyPI package (name-squatted, not from Slack) or `slackclient` (deprecated 2021).

### Expected Features

All 8 MVP features are classified P1 and are LOW-MEDIUM complexity. The full v1 can ship without any deferred features.

**Must have (table stakes):**
- DM response — baseline interaction surface; users expect it on every bot
- `@mention` response in channels — primary team discovery surface
- `/ask` slash command — canonical Slack invocation pattern; works without inviting bot to channel
- Threaded replies — non-negotiable; top-level bot replies flood channels
- "Searching..." loading indicator — Perplexity takes 3–30s; users abandon without feedback
- Source citations with clickable URLs — core differentiator; ungrounded answers feel fabricated
- Graceful error message — professional failure mode with owner contact
- App Home tab (static) — onboarding surface; reduces support questions

**Should have (v1.x after validation):**
- Rotating "Searching..." status messages — low effort UX improvement
- Usage cost logging to stdout — useful before any dashboard

**Defer (v2+):**
- Conversation history / multi-turn context — adds statefulness, DB requirement, degrades Perplexity's fresh-search strength
- Per-user model/preset selection — exposes API complexity, modal UI required
- Admin usage dashboard — requires persistent storage and a separate UI surface
- Multi-workspace deployment (HTTP mode + OAuth) — only if moving from internal tool to SaaS

### Architecture Approach

The architecture is a single Python process communicating outbound over WebSocket (to Slack via Socket Mode) and HTTPS (to Perplexity). There is no inbound port, no database, and no queue. The Bolt framework dispatches incoming events to decorated handler functions, which call a service layer, format the result, and reply in-thread via the Slack Web API. The recommended build order is: env/config first, then the Perplexity service layer (standalone testable), then the Bolt skeleton (token verification), then handlers in dependency order (DM first as simplest pipeline validation, then mention, slash command, App Home last as independent surface).

**Major components:**
1. **SocketModeHandler** — maintains persistent WebSocket to Slack; receives all event payloads; requires `SLACK_APP_TOKEN` (xapp-) with `connections:write` scope
2. **Event Listeners** (`handlers/`) — four files: `mention.py`, `direct_message.py`, `slash_command.py`, `app_home.py`; each registers via Bolt decorators; never calls Perplexity SDK directly
3. **Perplexity Service Layer** (`services/perplexity.py`) — sole call site for `perplexityai` SDK; returns `(answer: str, citations: list[dict])`; raises `PerplexityError` on failure
4. **Formatting Utils** (`utils/formatting.py`) — converts answer + citations to Slack mrkdwn with `<URL|Title>` link syntax
5. **App Home Handler** (`handlers/app_home.py`) — publishes static Block Kit view on `app_home_opened`; no Perplexity dependency

### Critical Pitfalls

Six pitfalls were identified; all six must be prevented in Phase 1. The top five are:

1. **Missing the 3-second `ack()` deadline** — call `ack()` as the absolute first line of every slash command handler, before any I/O; Bolt handles event/mention ack automatically but slash commands require explicit call
2. **Bot responds to its own messages (infinite loop)** — check `event.get("bot_id") or event.get("subtype")` at the top of every `message` event handler and return early; failure causes an infinite Perplexity-calling loop
3. **Blocking the event loop with synchronous Perplexity calls** — run the Perplexity call in a background thread (`threading.Thread`) so Bolt can continue receiving events; `pro-search` with `fetch_url` tool can take 30+ seconds
4. **Incorrect thread targeting** — use `event.get("thread_ts") or event["ts"]` not just `event["ts"]`; for slash commands, post a placeholder first and reply to its `ts`
5. **Perplexity `output` type mismatch** — use `response.output_text` for the answer; iterate `response.output` filtering by `item.type == "search_results"` for citations; never use `response.output[0].text`

---

## Implications for Roadmap

Based on combined research, the build follows a strict dependency order that mirrors the architecture's dependency graph. All core features can ship in a single focused phase; there is no architectural reason to split Phase 1 further.

### Phase 1: Foundation and Core Pipeline

**Rationale:** The env/config layer, Perplexity service, and Bolt skeleton are prerequisites for everything else. Validates all three credentials are working before any handler code is written. The DM handler is the simplest full-pipeline test (no mention-stripping, no ack complexity).
**Delivers:** Working bot that responds to DMs with cited answers, threaded replies, loading indicator, and error handling
**Addresses:** DM response, threaded replies, "Searching..." indicator, source citations, graceful error message (5 of 8 P1 features)
**Avoids:** All 6 critical pitfalls must be baked in at this phase — ack deadline, bot loop filter, threading for Perplexity calls, correct thread_ts logic, output type parsing, secret management

### Phase 2: Full Trigger Coverage

**Rationale:** `@mention` and `/ask` handlers build directly on the DM handler pattern; only the trigger surface differs. App Home is independent and can be done in the same phase. Completes the full v1 feature set.
**Delivers:** `@mention` in channels, `/ask` slash command, App Home tab with usage instructions (remaining 3 of 8 P1 features)
**Uses:** Same Perplexity service layer and formatting utils from Phase 1; adds mention-stripping for `@mention` handler; adds `ack()` + placeholder pattern for slash command handler
**Avoids:** Slash command `respond()` pitfall (use `say()` + `chat_postMessage` instead); wrong thread targeting in mention handler

### Phase 3: Polish and Hardening

**Rationale:** Once the bot is in real use, low-effort UX improvements and operational hygiene become visible. Rotating status messages and cost logging are P2 items that add value without architectural change.
**Delivers:** Rotating "Searching..." status messages (`assistant.threads.setStatus()`), per-query cost logging to stdout, verification of the "Looks Done But Isn't" checklist from PITFALLS.md
**Uses:** `assistant.threads.setStatus` API (documented in FEATURES.md sources)

### Phase Ordering Rationale

- Perplexity service layer must precede all handlers — handlers have no value without it, and it can be tested standalone before any Slack credentials are configured
- DM handler before mention handler — DM is structurally simpler (no mention-stripping); validates full pipeline cheaply before adding complexity
- Slash command after DM/mention — the `ack()` + threading pattern is an additional complexity layer; easier to introduce once the basic pipeline is proven
- App Home in Phase 2 (not Phase 1) — it is fully independent of Perplexity; deferring keeps Phase 1 focused on the core pipeline
- Phase 3 is purely additive — no architectural changes, no new dependencies, safe to ship after v1 validation

### Research Flags

Phases with well-documented patterns (skip research-phase for these):
- **Phase 1 and Phase 2:** All patterns are fully documented in the local reference docs (`slack-bolt-docs.md`, `pplx-docs.md`) and in STACK.md/ARCHITECTURE.md. No external research needed — implementation can proceed directly from these files.
- **Phase 3:** `assistant.threads.setStatus` is documented in official Slack API reference. Rotating status message patterns are well-established.

No phases require `/gsd:research-phase` — confidence is HIGH across all implementation surfaces.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against PyPI 2026-03-13; all API patterns verified against local official docs |
| Features | HIGH (core), MEDIUM (differentiators) | Table stakes and anti-features confirmed against official docs and competitor analysis; differentiator claims based on 2026 market landscape |
| Architecture | HIGH | Component structure and all three key patterns (ack-first, thread pinning, service isolation) verified against official Slack Bolt docs and Perplexity Agent API docs |
| Pitfalls | HIGH | All 6 critical pitfalls sourced from official documentation of Slack's timing model and Perplexity response schema; not inferred |

**Overall confidence:** HIGH

### Gaps to Address

- **Perplexity `pro-search` response time under real load:** Research documents 3–30s latency but exact P95 latency is unknown. The threading pattern handles this architecturally, but if response times routinely exceed 30s, a timeout threshold needs to be defined. Recommend logging `response.usage.total_tokens` and wall-clock time per query from day one.
- **`assistant.threads.setStatus` rotating message UX:** Documented in FEATURES.md as available in the API, but not tested. Defer to Phase 3 when the baseline loading indicator is confirmed working.
- **Perplexity API rate limits at workspace scale:** Research confirms per-key quotas exist but does not specify exact limits for the `pro-search` preset. Monitor via the Perplexity console; add in-memory per-user rate limiting only if costs spike.

---

## Sources

### Primary (HIGH confidence)
- `slack-bolt-docs.md` (local, from docs.slack.dev) — SocketModeHandler pattern, token types, event subscriptions, message listener API, slash command ack requirements, App Home `views_publish`
- `pplx-docs.md` (local, from docs.perplexity.ai) — Agent API endpoint, `perplexityai` SDK, `pro-search` preset, `output_text` convenience property, `search_results` output structure, error types, tools reference
- PyPI (live query 2026-03-13) — `slack_bolt==1.27.0`, `perplexityai==0.30.1`, `slack_sdk==3.41.0`, `python-dotenv==1.2.2`
- `.planning/PROJECT.md` — confirmed constraints: Socket Mode, Python, Perplexity Python SDK, `pro-search` preset, no conversation history

### Secondary (MEDIUM confidence)
- [Slack: Best practices for AI-enabled apps](https://docs.slack.dev/ai/ai-apps-best-practices/) — loading indicator patterns, App Home design
- [Slack: assistant.threads.setStatus](https://docs.slack.dev/reference/methods/assistant.threads.setStatus/) — rotating status message API
- [eesel AI: Slack AI loading states UX](https://www.eesel.ai/blog/slack-ai-loading-states-ux) — UX patterns for AI bots in Slack

### Tertiary (context only)
- [TechCrunch: Slackbot is an AI agent now (Jan 2026)](https://techcrunch.com/2026/01/13/slackbot-is-an-ai-agent-now/) — competitive landscape
- [Wonderchat: Best AI chatbots for Slack in 2026](https://wonderchat.io/blog/best-ai-chatbots-for-slack) — market landscape context

---
*Research completed: 2026-03-13*
*Ready for roadmap: yes*
