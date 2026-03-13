# Requirements: Perplexity Slack Bot

**Defined:** 2026-03-13
**Core Value:** Any Slack user can ask a question and get a high-quality, source-cited answer powered by Perplexity's real-time web search — without leaving Slack.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Core Interaction

- [x] **INTR-01**: User can DM the bot a question and receive a Perplexity-powered answer
- [x] **INTR-02**: User can @mention the bot in any channel and receive an answer in a thread
- [x] **INTR-03**: User can use `/ask <question>` slash command from any channel to get an answer
- [x] **INTR-04**: All bot responses are posted as threaded replies (not top-level messages)

### Response Quality

- [x] **RESP-01**: Bot posts a "Searching..." loading indicator before the answer arrives
- [x] **RESP-02**: Bot updates the loading message with the full answer once Perplexity responds
- [x] **RESP-03**: Answers include numbered source citations with clickable URLs extracted from Perplexity search results
- [x] **RESP-04**: Bot uses Perplexity `pro-search` preset for optimized model selection and web search

### Reliability

- [x] **RELY-01**: Bot displays friendly error message when backend/Perplexity is unreachable: "Uh oh, it seems my brain is offline — talk to @Robert Li about trying to kick start it"
- [x] **RELY-02**: Bot ignores its own messages to prevent self-response loops
- [x] **RELY-03**: Handlers ack() within 3 seconds before making Perplexity API calls

### App Surface

- [x] **SURF-01**: App Home tab displays bot description and usage instructions
- [x] **SURF-02**: Bot runs via Socket Mode (no public URL required)

## v1.1 Requirements

Requirements for milestone v1.1. Each maps to roadmap phases.

### Interaction Surfaces

- [x] **SURF-03**: User runs `/ask <question>` from any channel and receives a cited answer as a visible threaded reply
- [x] **SURF-04**: App Home tab displays bot description, usage instructions for all interaction methods, and current status
- [x] **SURF-05**: Bot responds to messages in group DMs (multi-person DMs) using the same pipeline

### Conversation Context

- [ ] **CTXT-01**: Bot reads up to N previous messages in a thread before querying Perplexity, enabling follow-up questions
- [ ] **CTXT-02**: `<@UID>` mention tags in messages are resolved to display names via Slack API before sending to Perplexity
- [ ] **CTXT-03**: Bot reads up to N recent channel messages as context when a question is asked outside a thread
- [ ] **CTXT-04**: Thread/channel history depth is configurable per-workspace with a default of 10 messages

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced UX

- **UX-01**: Rotating loading status messages during search
- **UX-02**: Per-query cost/usage tracking and logging

### Administration

- **ADMIN-01**: Usage analytics dashboard
- **ADMIN-02**: Per-user or per-channel rate limiting

## Out of Scope

| Feature | Reason |
|---------|--------|
| Per-user model selection | pro-search preset handles this; unnecessary complexity |
| HTTP deployment mode | Socket Mode sufficient; no public URL needed |
| Admin dashboard | Not needed yet, small user base |
| OAuth distribution to other workspaces | Single workspace install only |
| File attachment processing | Requires vision model or document extraction; defer |
| Persistent memory across sessions | Context is per-thread/channel only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INTR-01 | Phase 1 | Complete |
| INTR-02 | Phase 1 | Complete |
| INTR-03 | Phase 3 | Complete |
| INTR-04 | Phase 1 | Complete |
| RESP-01 | Phase 1 | Complete |
| RESP-02 | Phase 1 | Complete |
| RESP-03 | Phase 1 | Complete |
| RESP-04 | Phase 1 | Complete |
| RELY-01 | Phase 1 | Complete |
| RELY-02 | Phase 1 | Complete |
| RELY-03 | Phase 1 | Complete |
| SURF-01 | Phase 3 | Complete |
| SURF-02 | Phase 1 | Complete |
| SURF-03 | Phase 3 | Complete |
| SURF-04 | Phase 3 | Complete |
| SURF-05 | Phase 3 | Complete |
| CTXT-01 | Phase 4 | Pending |
| CTXT-02 | Phase 4 | Pending |
| CTXT-03 | Phase 4 | Pending |
| CTXT-04 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 13 total
- v1.1 requirements: 7 total
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 after v1.1 roadmap creation — all 20 requirements mapped*
