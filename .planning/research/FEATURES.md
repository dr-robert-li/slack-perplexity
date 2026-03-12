# Feature Research

**Domain:** Slack AI assistant bot — real-time web search, Q&A answers with cited sources
**Researched:** 2026-03-13
**Confidence:** HIGH (core features), MEDIUM (differentiators), HIGH (anti-features)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Respond to DMs | Every Slack bot responds to direct messages — it's the baseline interaction surface | LOW | Bolt `@app.event("message")` with DM channel check |
| Respond to @mentions in channels | Users expect to summon the bot by name in any channel, same as tagging a human | LOW | Bolt `@app.event("app_mention")` |
| `/ask` slash command | Slash commands are the canonical Slack interaction pattern — users expect a named command | LOW | Bolt `@app.command("/ask")` — slash command name must match manifest |
| Threaded replies (not top-level) | Posting top-level responses to @mentions floods channels; threading is the Slack norm | LOW | `thread_ts` must be passed in `say()` call; always reply in-thread |
| "Thinking" / loading indicator | AI responses take 3–10+ seconds; users abandon or retry without feedback | LOW | `assistant.threads.setStatus()` API supports rotating status messages; or post ephemeral "Searching..." message immediately |
| Graceful error message | Backend failures without user-facing messaging feel broken; users don't know if the bot received their request | LOW | Human-friendly text, route to owner contact for follow-up |
| App Home tab with usage instructions | Users land here first when they click the bot — no content = abandoned, confused users | LOW | Publish static Block Kit view on `app_home_opened` event; list trigger methods and example queries |
| Source citations with URLs | Users of search-grounded AI expect to verify answers; unmarked answers feel fabricated | MEDIUM | Perplexity `pro-search` preset returns `search_results` output items with title, URL, snippet — format as numbered list |

### Differentiators (Competitive Advantage)

Features that set this bot apart from generic Q&A bots. Not required, but they deliver the core value promise.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Real-time web search grounding | Most Slack bots answer from static knowledge cutoffs; this bot fetches live web content for every answer — making it useful for current events, recent releases, breaking news | LOW | Perplexity `pro-search` preset handles web search + model selection automatically; no extra work |
| Numbered source citations with clickable URLs | Competing bots (e.g., generic ChatGPT integrations) give answers without traceable sources; cited sources build trust and allow follow-up research without leaving Slack | MEDIUM | `search_results` array in Perplexity response has `id`, `title`, `url` fields; format as `[1] Title — URL` after answer text |
| `pro-search` preset quality | Perplexity's `pro-search` uses optimized model selection (currently routes to top-tier models like GPT-5.1 per docs), multi-query decomposition, and URL fetch for deep answers — higher quality than basic LLM completions | LOW | Pass `preset="pro-search"` — no model juggling required |
| Zero infrastructure friction | Socket Mode eliminates the need for a public HTTPS endpoint, SSL cert, or cloud hosting — runs on localhost, deployable anywhere with network access to Slack's WebSocket relay | LOW | Already decided in PROJECT.md; surfaced here because it matters for adoption and internal tooling contexts |
| Single-question freshness model | Each question gets a fresh web search — answers never stale out the way memory-augmented bots do when their stored context ages | LOW | Intentional design choice: no `previous_response_id` passed, no conversation state |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good on the surface but create maintenance burden, complexity, or user confusion disproportionate to their value for this bot's purpose.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Multi-turn conversation history | Users want context-aware follow-up questions ("What about React?" after asking about JavaScript) | Each question is a fresh web search — injecting prior messages into the `input` field increases token cost, requires storing per-user/thread state in memory or a DB, and stale context can degrade answer quality for unrelated follow-ups. Perplexity's strength is fresh search, not memory replay. | Encourage complete standalone questions. If follow-up context is needed, users can quote the prior answer in their next message. |
| Per-user model selection | Power users ask for GPT-4 vs Claude vs Gemini toggles | Exposes API complexity, requires UI (modals or slash args), increases error surface. The `pro-search` preset already routes to the best available model per query type. | Fixed to `pro-search` preset — document what models it selects and why in App Home |
| Admin analytics dashboard | Teams want to see query volume, top questions, active users | Requires persistent storage (DB or log aggregation), a separate UI surface, authentication. Scope doubles before v1 ships. | Log to stdout/stderr for now; revisit when there is proven demand |
| Rate limiting per user | Prevent abuse, manage API costs | Requires per-user state tracking, a clock mechanism, and graceful messaging around limits. At internal Slack workspace scale, the Perplexity API cost per query (~$0.04) is negligible. | Monitor API usage via Perplexity console; if costs spike, add simple per-request cost logging first |
| Streaming response with live message updates | Progressive text delivery feels faster, matches Perplexity.ai web UX | Slack's `chat.update` method can be called to edit messages progressively, but this requires posting a placeholder, polling or streaming from Perplexity, and updating the message in a loop — substantially more complex. Perplexity's `pro-search` preset is not real-time streaming in its current agent form. | Post "Searching..." placeholder → replace with full answer when response arrives (two-message pattern) |
| HTTP mode / public webhook deployment | Some users want to host on cloud servers rather than localhost | Socket Mode already works; switching to HTTP requires a public TLS endpoint, webhook verification middleware, and deployment infra. No user-facing benefit. | Keep Socket Mode; add HTTP mode only if the bot needs to be deployed as a shared multi-workspace SaaS |

---

## Feature Dependencies

```
[App responds to DMs]
    └──requires──> [Slack bot token with `im:history` scope]

[App responds to @mentions]
    └──requires──> [Slack bot token with `app_mentions:read` scope]
                       └──requires──> [Bot invited to channel]

[Threaded replies]
    └──requires──> [Any trigger that provides thread_ts or message ts]

[Source citations with URLs]
    └──requires──> [Perplexity pro-search preset response with search_results output items]
                       └──requires──> [pro-search preset or explicit web_search tool]

[Loading indicator ("Searching...")]
    └──enhances──> [Any trigger: DM, @mention, /ask]

[App Home tab]
    └──requires──> [app_home_opened event listener]
    └──enhances──> [/ask slash command] (cross-references command in UI)

[Graceful error message]
    └──enhances──> [All triggers] (wraps every Perplexity call in try/except)
```

### Dependency Notes

- **Threaded replies require ts/thread_ts:** For @mentions, use `event["ts"]` as the `thread_ts`. For DMs, use the message `ts`. For slash commands, post a placeholder message first, then reply in that thread.
- **Source citations require pro-search:** The `search_results` output array is only reliably present when web search tools are active. The `pro-search` preset enables this automatically.
- **Loading indicator enhances all triggers:** Can be implemented as a single wrapper function around the Perplexity API call — decoupled from trigger type.
- **App Home tab is independent:** No runtime dependencies; published once on `app_home_opened` and can be purely static for v1.

---

## MVP Definition

### Launch With (v1)

Minimum viable product that delivers the core value: "ask a question in Slack, get a source-cited answer."

- [ ] DM response — users can ask questions in private without being in a channel
- [ ] @mention response in channels — primary discovery surface for team use
- [ ] `/ask` slash command — explicit invocation, works in any channel without needing to invite the bot
- [ ] Threaded replies — keeps channels clean, non-negotiable for channel mentions
- [ ] "Searching..." loading indicator — prevents user abandonment during 3–10s API latency
- [ ] Source citations with clickable URLs — core differentiator, validates answers are grounded
- [ ] Graceful error message on backend failure — professional failure mode, routes to owner
- [ ] App Home tab with usage instructions — onboarding surface, reduces support questions

All 8 items are in project scope (PROJECT.md Active requirements). All are LOW-MEDIUM complexity.

### Add After Validation (v1.x)

Features to add once the core bot is in daily use and real usage patterns emerge.

- [ ] `/ask` ephemeral responses option — when user wants a private answer in a public channel; add when users request it
- [ ] Rotating "Searching..." status messages — `assistant.threads.setStatus()` supports up to 10 rotating messages for better UX; low effort enhancement after baseline works
- [ ] Usage cost logging to stdout — single-line log per query showing `total_cost` from Perplexity usage object; useful before any admin dashboard

### Future Consideration (v2+)

Features to defer until product-market fit is established and there is real user demand.

- [ ] Conversation threading / follow-up context — adds statefulness; only worth building if users consistently complain about standalone-question limitation
- [ ] Per-user `/ask` preferences (verbosity, language) — only worth building if diverse user base with varying needs emerges
- [ ] Multi-workspace deployment (HTTP mode + OAuth) — only if this moves from internal tool to shared product
- [ ] Admin usage dashboard — only if API costs become significant enough to warrant monitoring beyond Perplexity console

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| DM response | HIGH | LOW | P1 |
| @mention response | HIGH | LOW | P1 |
| `/ask` slash command | HIGH | LOW | P1 |
| Threaded replies | HIGH | LOW | P1 |
| "Searching..." loading indicator | HIGH | LOW | P1 |
| Source citations with URLs | HIGH | MEDIUM | P1 |
| Graceful error message | HIGH | LOW | P1 |
| App Home tab (static) | MEDIUM | LOW | P1 |
| Rotating status messages | LOW | LOW | P2 |
| Usage cost logging | LOW | LOW | P2 |
| Conversation history / follow-up | MEDIUM | HIGH | P3 |
| Admin usage dashboard | LOW | HIGH | P3 |
| Per-user model selection | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

Competitors surveyed: Slack's native AI (Slackbot), eesel AI, and generic ChatGPT-in-Slack integrations.

| Feature | Native Slackbot (2026) | eesel AI | This Bot |
|---------|------------------------|----------|----------|
| Real-time web search | Yes (Slack AI tier) | No (internal sources only) | Yes — Perplexity pro-search |
| Source citations | Partial (no numbered refs) | No | Yes — numbered URLs from search_results |
| Setup complexity | Zero (built-in) | High (SaaS onboarding) | Low (Socket Mode, .env config) |
| Answers from public web | Yes | No (company data only) | Yes |
| Requires paid Slack plan | Yes (Business+/Enterprise+) | Yes ($299+/mo) | No — works on any Slack plan |
| Conversation memory | Yes | Yes | No (intentional — fresh search) |
| Internal doc search | Yes | Yes | No (out of scope) |
| Slash command trigger | No | No | Yes |
| App Home tab | Yes | Yes | Yes |

**Assessment:** Native Slackbot has more features but requires paid Slack tiers. This bot's differentiator is fresh web search with cited sources on any Slack plan, with minimal setup.

---

## Sources

- [Slack: Best practices for AI-enabled apps](https://docs.slack.dev/ai/ai-apps-best-practices/) — official Slack developer documentation
- [Slack: assistant.threads.setStatus method](https://docs.slack.dev/reference/methods/assistant.threads.setStatus/) — loading status API reference
- [Slack: App design guidelines](https://docs.slack.dev/surfaces/app-design/) — Home tab and surface design
- [TechCrunch: Slackbot is an AI agent now (Jan 2026)](https://techcrunch.com/2026/01/13/slackbot-is-an-ai-agent-now/) — competitive landscape context
- [eesel AI: Deep dive into Slack AI 2025](https://www.eesel.ai/blog/slack-ai) — competitor feature comparison
- [eesel AI: Slack AI loading states UX](https://www.eesel.ai/blog/slack-ai-loading-states-ux) — loading indicator UX patterns
- [eesel AI: Slack AI integration with Perplexity](https://www.eesel.ai/blog/slack-ai-integration-with-perplexity) — adjacent product pattern
- [Wonderchat: Best AI chatbots for Slack in 2026](https://wonderchat.io/blog/best-ai-chatbots-for-slack) — market landscape
- [Salesforce: Slackbot general availability announcement](https://investor.salesforce.com/news/news-details/2026/Salesforce-Announces-the-General-Availability-of-Slackbot--Your-Personal-Agent-for-Work/default.aspx) — competitive context
- Perplexity Agent API docs (`pplx-docs.md`) — pro-search preset, search_results output structure, SDK usage

---
*Feature research for: Slack AI assistant bot with Perplexity Agent API*
*Researched: 2026-03-13*
