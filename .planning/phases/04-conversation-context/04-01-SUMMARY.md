---
phase: 04-conversation-context
plan: 01
subsystem: api
tags: [slack-api, perplexity, context, uid-resolution, conversation-history]

# Dependency graph
requires:
  - phase: 03-interaction-surfaces
    provides: services/perplexity.py query_perplexity function and Slack client patterns
provides:
  - services/context.py with resolve_uids, fetch_thread_history, fetch_channel_history, HISTORY_DEPTH, MSG_TRUNCATE_LENGTH
  - services/perplexity.py updated to accept optional structured messages list
  - Full test coverage for both modules (21 + 11 = 32 tests)
affects: [04-conversation-context plan 02, handler wiring for thread/channel context]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Module-level dict cache for UID resolution (same pattern as greeted_users in shared.py)
    - Structured {type, role, content} message dicts compatible with Perplexity InputMessage
    - Graceful API degradation: return [] on any exception rather than raising
    - Reload-based env var testing with importlib.reload for module-level constants

key-files:
  created:
    - services/context.py
    - tests/test_context.py
  modified:
    - services/perplexity.py
    - tests/test_perplexity_service.py

key-decisions:
  - "UID cache is module-level dict persisting for bot lifetime — sufficient for single-process Socket Mode; same pattern as greeted_users"
  - "fetch_thread_history uses limit=HISTORY_DEPTH+1 to account for current_ts exclusion without undercounting"
  - "fetch_channel_history reverses API response (newest-first) to produce chronological order for Perplexity context"
  - "query_perplexity messages=None/[] falls back to string input for full backward compatibility with all existing call sites"
  - "All history fetchers return [] on any exception — safe degradation preserves bot operation without context rather than failing"

patterns-established:
  - "Structured message dict: {type: 'message', role: 'user'|'assistant', content: str} — used by both context.py and perplexity.py"
  - "TDD RED-GREEN pattern for each task: failing tests committed first, then implementation"

requirements-completed: [CTXT-01, CTXT-02, CTXT-03, CTXT-04]

# Metrics
duration: 15min
completed: 2026-03-13
---

# Phase 4 Plan 01: Conversation Context Infrastructure Summary

**UID resolution with in-memory cache, thread/channel history fetchers with role tagging and truncation, and Perplexity structured multi-turn message support — all building blocks for context-aware responses.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-13T00:00:00Z
- **Completed:** 2026-03-13
- **Tasks:** 2 (both TDD with RED + GREEN commits)
- **Files modified:** 4

## Accomplishments

- Created `services/context.py` with full UID resolution (cached, fallback to real_name), thread history fetcher (excludes current message, truncates, role-tags bot vs user), and channel history fetcher (chronological, configurable depth)
- Updated `services/perplexity.py` to accept optional `messages` parameter for structured multi-turn Perplexity queries while keeping string-only calls fully backward compatible
- 32 new tests (21 for context.py, 11 updated for perplexity.py) — full test suite 79/79 passing

## Task Commits

Each task was committed atomically following TDD RED-GREEN pattern:

1. **Task 1 RED: Failing tests for context.py** - `adad16f` (test)
2. **Task 1 GREEN: services/context.py implementation** - `fcc43cc` (feat)
3. **Task 2 RED: Failing tests for structured perplexity messages** - `f7efa83` (test)
4. **Task 2 GREEN: services/perplexity.py update** - `f897c6e` (feat)

## Files Created/Modified

- `services/context.py` — UID resolver with cache, thread/channel history fetchers, config constants
- `tests/test_context.py` — 21 unit tests covering all context.py behaviors
- `services/perplexity.py` — Added optional messages parameter for structured multi-turn input
- `tests/test_perplexity_service.py` — Added 6 tests for structured message behavior

## Decisions Made

- UID cache is module-level dict persisting for bot lifetime — sufficient for single-process Socket Mode (same pattern as `greeted_users` in `shared.py`)
- `fetch_thread_history` requests `HISTORY_DEPTH + 1` messages to ensure HISTORY_DEPTH results after excluding current message
- Channel history reversed from newest-first API order to chronological for better Perplexity context
- `query_perplexity` with `messages=None` or `messages=[]` sends string input — full backward compatibility with all existing handler call sites
- All history functions return `[]` on any exception — safe degradation over hard failure

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None — all tests passed on first run after implementation.

## User Setup Required

None — no new environment variables required. `HISTORY_DEPTH` and `MSG_TRUNCATE_LENGTH` have defaults of 10 and 500 respectively.

## Next Phase Readiness

- All context building blocks are ready for handler wiring in plan 04-02
- `services/context.py` exports: `resolve_uids`, `fetch_thread_history`, `fetch_channel_history`, `HISTORY_DEPTH`, `MSG_TRUNCATE_LENGTH`
- `services/perplexity.py` `query_perplexity` signature: `(question: str, messages: list[dict] | None = None) -> dict`
- Existing call sites `query_perplexity(user_text)` in handlers/shared.py need no changes

---
*Phase: 04-conversation-context*
*Completed: 2026-03-13*
