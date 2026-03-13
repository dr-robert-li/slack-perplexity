---
phase: 04-conversation-context
plan: 02
subsystem: handlers
tags: [slack-handlers, context-wiring, uid-resolution, thread-history, channel-history, tdd]

# Dependency graph
requires:
  - phase: 04-conversation-context plan 01
    provides: services/context.py and updated services/perplexity.py
provides:
  - handlers/shared.py updated with get_bot_user_id() cache and messages= support
  - handlers/message_handler.py wired to fetch thread/channel history
  - handlers/mention_handler.py wired to fetch thread/channel history
  - Full test coverage for all context wiring (15 new tests, 94 total)
affects: [end-to-end context-aware responses for all interaction surfaces]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Module-level _bot_user_id cache with lazy init via get_bot_user_id() — same pattern as greeted_users
    - thread_ts presence check to branch between fetch_thread_history vs fetch_channel_history
    - resolve_uids called in _handle_question before query_perplexity — central UID resolution point
    - messages= forwarded from handlers through _handle_question to query_perplexity

key-files:
  created:
    - tests/test_mention_handler.py
  modified:
    - handlers/shared.py
    - handlers/message_handler.py
    - handlers/mention_handler.py
    - .env.example
    - tests/test_shared.py
    - tests/test_message_handler.py
    - tests/test_dm_handler.py
    - tests/test_slash_handler.py

key-decisions:
  - "get_bot_user_id() cached in handlers/shared.py not app.py — avoids circular import risk while still caching for bot lifetime"
  - "UID resolution happens in _handle_question (central) not in each handler — single responsibility, no duplication"
  - "slash_handler.py unchanged — /ask is intentionally standalone with no conversation context per user decision"

patterns-established:
  - "All handlers follow same context pattern: get_bot_user_id -> branch on thread_ts -> fetch_thread_history or fetch_channel_history -> pass messages= to _handle_question"
  - "Test pattern: patch at import site (handlers.message_handler.fetch_channel_history not services.context.fetch_channel_history)"

requirements-completed: [CTXT-01, CTXT-02, CTXT-03, CTXT-04]

# Metrics
duration: 15min
completed: 2026-03-13
---

# Phase 4 Plan 02: Handler Context Wiring Summary

**Context infrastructure connected end-to-end — all handler surfaces now assemble thread/channel history, resolve UIDs, and pass structured conversation context to Perplexity before answering.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-13
- **Completed:** 2026-03-13
- **Tasks:** 2 (both TDD with RED + GREEN commits)
- **Files modified:** 8 (4 handlers/tests, 4 test files)
- **Files created:** 1 (tests/test_mention_handler.py)

## Accomplishments

- Updated `handlers/shared.py`: added `get_bot_user_id()` with module-level cache; extended `_handle_question` signature with `messages=None` kwarg; UID resolution via `resolve_uids()` before every Perplexity call
- Updated `handlers/message_handler.py`: `handle_dm` and `handle_mpim` now fetch `fetch_thread_history` when `thread_ts` is present, `fetch_channel_history` otherwise; pass `messages=` to `_handle_question`
- Updated `handlers/mention_handler.py`: same context fetching pattern as message_handler
- `handlers/slash_handler.py` intentionally unchanged — `/ask` is standalone per user decision
- Added `.env.example` entries for `HISTORY_DEPTH=10` and `MSG_TRUNCATE_LENGTH=500`
- 15 new tests (6 mention handler, 4 DM/mpim context, 4 shared context, 1 slash no-context assertion) — full suite 94/94 passing

## Task Commits

Each task was committed atomically following TDD RED-GREEN pattern:

1. **Task 1 RED: Failing tests for handler context wiring** - `0766a7d` (test)
2. **Task 1 GREEN: Wire context into all handlers** - `7e180e6` (feat)
3. **Task 2: Add mention handler tests** - `5af6186` (feat)

## Files Created/Modified

- `handlers/shared.py` — Added `_bot_user_id` cache, `get_bot_user_id()`, updated `_handle_question` with `messages=` and UID resolution
- `handlers/message_handler.py` — Imports context functions; `handle_dm`/`handle_mpim` fetch history, pass `messages=`
- `handlers/mention_handler.py` — Imports context functions; `handle_mention` fetches history, passes `messages=`
- `.env.example` — Added `HISTORY_DEPTH` and `MSG_TRUNCATE_LENGTH` entries
- `tests/test_mention_handler.py` — 6 tests for mention handler guards and context fetching
- `tests/test_shared.py` — Added `TestHandleQuestionWithContext` (4 tests)
- `tests/test_message_handler.py` — Added `TestHandleDmContextFetching` and `TestHandleMpimContextFetching` (5 tests)
- `tests/test_dm_handler.py` — Updated `TestDMHandlerPipeline` with context mock patches
- `tests/test_slash_handler.py` — Added `test_run_ask_does_not_call_context_functions`

## Decisions Made

- `get_bot_user_id()` cached in `handlers/shared.py` — avoids circular import if placed in `app.py`; same module-level cache pattern as `greeted_users`
- UID resolution centralized in `_handle_question` — single point prevents duplication across all callers
- `/ask` slash command left completely unchanged — standalone behavior by design

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None — all tests passed on first run after implementation.

## User Setup Required

Add to `.env` if non-default values are needed:
- `HISTORY_DEPTH=10` — number of prior messages to include as context
- `MSG_TRUNCATE_LENGTH=500` — max characters per history message before truncation

Both have sensible defaults and are optional.

## Next Phase Readiness

Phase 4 complete. The bot now provides full contextual conversation:
- Thread follow-ups include prior thread history as Perplexity context
- Channel @mentions include recent channel history as context
- DMs include prior DM history as context
- `<@UID>` tags resolved to display names in all questions
- `/ask` remains standalone (no context)

## Self-Check: PASSED

- handlers/shared.py: FOUND
- handlers/message_handler.py: FOUND
- handlers/mention_handler.py: FOUND
- tests/test_mention_handler.py: FOUND
- Commit 0766a7d (test RED): FOUND
- Commit 7e180e6 (feat GREEN): FOUND
- Commit 5af6186 (mention tests): FOUND
- Test suite: 94/94 passed

---
*Phase: 04-conversation-context*
*Completed: 2026-03-13*
