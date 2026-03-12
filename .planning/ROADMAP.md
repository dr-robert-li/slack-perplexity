# Roadmap: Perplexity Slack Bot

## Overview

Two phases deliver a fully working bot. Phase 1 builds the complete core pipeline — project scaffolding, Perplexity service layer, and the DM handler with all reliability and response-quality requirements baked in. Phase 2 adds the remaining interaction surfaces (@mention, /ask slash command, App Home tab) that build directly on the Phase 1 foundation.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Core Pipeline** - Project setup, Perplexity service layer, DM handler with full reliability and response quality (completed 2026-03-12)
- [ ] **Phase 2: Full Trigger Coverage** - @mention, /ask slash command, and App Home tab

## Phase Details

### Phase 1: Core Pipeline
**Goal**: Users can DM the bot a question and receive a cited, threaded answer — with a loading indicator, graceful error handling, and zero infinite-loop risk
**Depends on**: Nothing (first phase)
**Requirements**: INTR-01, INTR-04, RESP-01, RESP-02, RESP-03, RESP-04, RELY-01, RELY-02, RELY-03, SURF-02
**Success Criteria** (what must be TRUE):
  1. User sends a DM to the bot and receives a threaded reply with a cited answer (not a top-level message)
  2. A "Searching..." indicator appears before the answer, then updates in-place with the full response and numbered citations with clickable URLs
  3. Bot uses the `pro-search` preset and all answers include source URLs extracted from Perplexity search results
  4. When Perplexity is unreachable, the bot replies with the friendly error message directing to @Robert Li
  5. Bot never replies to its own messages and all event handlers acknowledge within 3 seconds
**Plans:** 3/3 plans complete

Plans:
- [ ] 01-01-PLAN.md — Project scaffolding, Perplexity service layer, formatting utils, test infrastructure
- [ ] 01-02-PLAN.md — DM handler with full pipeline (loading, citations, errors, greeting)
- [ ] 01-03-PLAN.md — Live smoke test with real Slack credentials

### Phase 2: Full Trigger Coverage
**Goal**: Any Slack user can reach the bot through @mention in any channel, the /ask slash command, or the App Home tab — all using the same response pipeline built in Phase 1
**Depends on**: Phase 1
**Requirements**: INTR-02, INTR-03, SURF-01
**Success Criteria** (what must be TRUE):
  1. User @mentions the bot in any channel and receives a cited answer as a threaded reply in that channel
  2. User runs `/ask <question>` from any channel and receives a cited answer in a thread, whether or not the bot is invited to that channel
  3. App Home tab displays bot description and clear usage instructions for all three interaction methods
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Pipeline | 3/3 | Complete   | 2026-03-12 |
| 2. Full Trigger Coverage | 0/TBD | Not started | - |
