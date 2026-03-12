# Requirements: Perplexity Slack Bot

**Defined:** 2026-03-13
**Core Value:** Any Slack user can ask a question and get a high-quality, source-cited answer powered by Perplexity's real-time web search — without leaving Slack.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Core Interaction

- [ ] **INTR-01**: User can DM the bot a question and receive a Perplexity-powered answer
- [ ] **INTR-02**: User can @mention the bot in any channel and receive an answer in a thread
- [ ] **INTR-03**: User can use `/ask <question>` slash command from any channel to get an answer
- [ ] **INTR-04**: All bot responses are posted as threaded replies (not top-level messages)

### Response Quality

- [ ] **RESP-01**: Bot posts a "Searching..." loading indicator before the answer arrives
- [ ] **RESP-02**: Bot updates the loading message with the full answer once Perplexity responds
- [ ] **RESP-03**: Answers include numbered source citations with clickable URLs extracted from Perplexity search results
- [ ] **RESP-04**: Bot uses Perplexity `pro-search` preset for optimized model selection and web search

### Reliability

- [ ] **RELY-01**: Bot displays friendly error message when backend/Perplexity is unreachable: "Uh oh, it seems my brain is offline — talk to @Robert Li about trying to kick start it"
- [ ] **RELY-02**: Bot ignores its own messages to prevent self-response loops
- [ ] **RELY-03**: Handlers ack() within 3 seconds before making Perplexity API calls

### App Surface

- [ ] **SURF-01**: App Home tab displays bot description and usage instructions
- [ ] **SURF-02**: Bot runs via Socket Mode (no public URL required)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced UX

- **UX-01**: Rotating loading status messages during search
- **UX-02**: Per-query cost/usage tracking and logging
- **UX-03**: Conversation memory for multi-turn follow-up questions

### Administration

- **ADMIN-01**: Usage analytics dashboard
- **ADMIN-02**: Per-user or per-channel rate limiting

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-turn conversation memory | Adds statefulness, storage, token cost; undermines Perplexity's fresh-search strength |
| Per-user model selection | pro-search preset handles this; unnecessary complexity |
| HTTP deployment mode | Socket Mode sufficient; no public URL needed |
| Admin dashboard | Not needed for v1, small user base |
| OAuth distribution to other workspaces | Single workspace install only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INTR-01 | — | Pending |
| INTR-02 | — | Pending |
| INTR-03 | — | Pending |
| INTR-04 | — | Pending |
| RESP-01 | — | Pending |
| RESP-02 | — | Pending |
| RESP-03 | — | Pending |
| RESP-04 | — | Pending |
| RELY-01 | — | Pending |
| RELY-02 | — | Pending |
| RELY-03 | — | Pending |
| SURF-01 | — | Pending |
| SURF-02 | — | Pending |

**Coverage:**
- v1 requirements: 13 total
- Mapped to phases: 0
- Unmapped: 13 ⚠️

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 after initial definition*
