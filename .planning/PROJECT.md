# Perplexity Slack Bot

## What This Is

A Slack bot that lets any workspace user ask questions and get AI-powered, web-searched answers via the Perplexity Agent API. Users can interact through DMs, @mentions in channels, a slash command, or the App Home tab — and the bot replies in threads with cited sources to keep conversations clean.

## Core Value

Any Slack user can ask a question and get a high-quality, source-cited answer powered by Perplexity's real-time web search — without leaving Slack.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Bot responds to direct messages with Perplexity-powered answers
- [ ] Bot responds to @mentions in any channel it's invited to
- [ ] Bot responds to `/ask` slash command from any channel
- [ ] App Home tab displays bot info and usage instructions
- [ ] All responses are posted as threaded replies (not top-level messages)
- [ ] Bot posts a "Searching..." indicator before the answer arrives
- [ ] Answers include numbered source citations with clickable URLs
- [ ] Uses Perplexity `pro-search` preset for optimized search + model selection
- [ ] Friendly error message when backend is offline: "Uh oh, it seems my brain is offline — talk to @Robert Li about trying to kick start it"
- [ ] Runs via Socket Mode (no public URL required)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Conversation history / multi-turn chat — keep it simple, each question is standalone
- User authentication or access control — any workspace member can use it
- HTTP deployment mode — Socket Mode is sufficient for now
- Admin dashboard or analytics — not needed for v1
- Custom model selection per user — pro-search preset handles this

## Context

- Built with Slack Bolt for Python using Socket Mode (no public URL needed)
- Perplexity Agent API endpoint: `POST https://api.perplexity.ai/v1/agent` with `pro-search` preset
- Perplexity SDK: `perplexityai` Python package
- Reference docs provided locally: `slack-bolt-docs.md` and `pplx-docs.md`
- Perplexity returns `search_results` output items with URLs, titles, and snippets alongside the model's text response
- Socket Mode requires `SLACK_APP_TOKEN` (xapp) and `SLACK_BOT_TOKEN` (xoxb)
- Perplexity requires `PERPLEXITY_API_KEY` environment variable

## Constraints

- **Tech stack**: Python + Slack Bolt + Perplexity Python SDK
- **Connection**: Socket Mode only (localhost-friendly, no public endpoint)
- **API dependency**: Requires active Perplexity API key with credits
- **Error handling**: Must gracefully handle backend disconnection with user-friendly message directing to @Robert Li

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Socket Mode over HTTP | Simplest setup, runs locally without public URL | — Pending |
| pro-search preset | Optimized defaults, auto model selection, includes web search + URL fetch | — Pending |
| Threaded replies | Keeps channels clean when bot is mentioned | — Pending |
| Standalone questions (no conversation memory) | Reduces complexity, each question gets fresh web search | — Pending |

---
*Last updated: 2026-03-13 after initialization*
