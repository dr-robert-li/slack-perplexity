# Roadmap: Perplexity Slack Bot

## Milestones

- ✅ **v1.0 Core Bot** - Phases 1-2 (Phase 1 complete; Phase 2 superseded by v1.1 scope)
- 🚧 **v1.1 Extended Interactions** - Phases 3-4 (in progress)

## Phases

<details>
<summary>✅ v1.0 Core Bot (Phases 1-2)</summary>

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
- [x] 01-01-PLAN.md — Project scaffolding, Perplexity service layer, formatting utils, test infrastructure
- [x] 01-02-PLAN.md — DM handler with full pipeline (loading, citations, errors, greeting)
- [x] 01-03-PLAN.md — Live smoke test with real Slack credentials

### Phase 2: Full Trigger Coverage (superseded)
**Goal**: @mention handler and App Home — absorbed into v1.1 scope (Phases 3-4)
**Status**: Superseded — @mention shipped as part of Phase 1 codebase; /ask and App Home moved to Phase 3
**Requirements**: INTR-02, INTR-03, SURF-01 (remapped to Phase 3)
**Plans**: Superseded before execution

</details>

---

### 🚧 v1.1 Extended Interactions (In Progress)

**Milestone Goal:** Add all remaining interaction surfaces (slash command, App Home, group DMs) and conversation context (thread history, mention resolution, channel context) so the bot understands follow-up questions and works everywhere in Slack.

#### Phase 3: Interaction Surfaces
**Goal**: Any Slack user can reach the bot through the `/ask` slash command, group DMs, or the App Home tab — all using the same response pipeline already built
**Depends on**: Phase 1
**Requirements**: SURF-03, SURF-04, SURF-05
**Success Criteria** (what must be TRUE):
  1. User runs `/ask <question>` from any channel and receives a cited answer posted as a visible thread reply in that channel
  2. User in a group DM sends a message and the bot responds with a cited, threaded answer using the same pipeline as 1:1 DMs
  3. App Home tab shows bot description, usage instructions for all interaction methods (DM, @mention, /ask, group DM), and current status
**Plans:** 2/2 plans complete

Plans:
- [x] 03-01-PLAN.md — Refactor handler module: extract shared.py, split handlers, add group DM support, fix thread_ts=None
- [x] 03-02-PLAN.md — /ask slash command, App Home tab, wire into app.py, live verification

#### Phase 4: Conversation Context
**Goal**: The bot understands follow-up questions by reading prior thread or channel messages before querying Perplexity, and displays human-readable names instead of raw Slack UIDs
**Depends on**: Phase 3
**Requirements**: CTXT-01, CTXT-02, CTXT-03, CTXT-04
**Success Criteria** (what must be TRUE):
  1. User sends a follow-up question in a thread (e.g., "What about in Python?") and the bot answers in context of the prior conversation without the user repeating themselves
  2. When a message contains `<@UID>` mention tags, the bot sends Perplexity the resolved display name (e.g., "Robert Li") instead of the raw UID
  3. User asks a question in a channel (not in a thread) and the bot includes recent channel messages as context, enabling answers that reference the current conversation
  4. History depth defaults to 10 messages and can be adjusted per-workspace without code changes
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 3 → 4

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Core Pipeline | v1.0 | 3/3 | Complete | 2026-03-12 |
| 2. Full Trigger Coverage | v1.0 | 0/0 | Superseded | - |
| 3. Interaction Surfaces | v1.1 | 2/2 | Complete | 2026-03-13 |
| 4. Conversation Context | v1.1 | 0/TBD | Not started | - |
