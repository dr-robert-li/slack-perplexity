# Perplexity Slack Bot

## What This Is

A Slack bot that lets any workspace user ask questions and get AI-powered, web-searched answers via the Perplexity Agent API. Users can interact through DMs, @mentions in channels, a slash command, or the App Home tab — and the bot replies in threads with cited sources to keep conversations clean.

## Core Value

Any Slack user can ask a question and get a high-quality, source-cited answer powered by Perplexity's real-time web search — without leaving Slack.

## Current Milestone: v1.1 Extended Interactions

**Goal:** Add remaining interaction surfaces (slash command, App Home, group DMs) and conversation context (thread history, @mention resolution, channel context) so the bot understands follow-up questions and works everywhere in Slack.

**Target features:**
- `/ask` slash command with threaded replies
- App Home tab with usage instructions
- Group DM support
- Thread history context for follow-ups (configurable depth, default 10)
- @mention resolution to display names
- Channel context window for non-threaded questions

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Bot responds to DMs with Perplexity-powered answers — v1.0 Phase 1
- ✓ Bot responds to @mentions in channels — v1.0 Phase 1
- ✓ Threaded replies, loading indicator, cited answers — v1.0 Phase 1
- ✓ pro-search preset, error handling, Socket Mode — v1.0 Phase 1

### Active

<!-- Current scope. Building toward these. -->

- [ ] `/ask` slash command with visible threaded reply from any channel
- [ ] App Home tab with bot description and usage instructions
- [ ] Group DM support using existing pipeline
- [ ] Thread history context (up to N messages) for follow-up questions
- [ ] @mention resolution — `<@UID>` → display names via Slack API
- [ ] Channel context window for questions outside threads
- [ ] Configurable history depth per-workspace (default 10)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- User authentication or access control — any workspace member can use it
- HTTP deployment mode — Socket Mode is sufficient
- Admin dashboard or analytics — not needed yet
- Custom model selection per user — pro-search preset handles this
- File attachment processing — requires vision model or document extraction, defer
- Persistent memory across sessions — context is per-thread/channel only

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
| Standalone questions (no conversation memory) | Reduces complexity, each question gets fresh web search | ⚠️ Revisit — v1.1 adds thread/channel context |

---
*Last updated: 2026-03-13 after milestone v1.1 started*
