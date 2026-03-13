---
phase: 03-interaction-surfaces
plan: 01
subsystem: api
tags: [slack, bolt, python, handlers, threading, perplexity]

# Dependency graph
requires:
  - phase: 01-core-pipeline
    provides: query_perplexity, format_answer, split_message, greeted_users pattern
provides:
  - handlers/shared.py with _handle_question(thread_ts: str | None) — used by all interaction surfaces
  - handlers/message_handler.py — DM (im) + group DM (mpim) lazy listeners
  - handlers/mention_handler.py — @mention event handler
  - Multi-handler architecture for Plans 02 and 03
affects:
  - 03-02 (slash commands need thread_ts=None path in _handle_question)
  - 03-03 (app home needs thread_ts=None path in _handle_question)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Shared pipeline pattern: all interaction surfaces call _handle_question from handlers/shared.py"
    - "thread_ts=None anchor pattern: when no thread context, use loading message ts as overflow anchor"
    - "Lazy listener guard pattern: each lazy fn guards on channel_type so only one fires per event"

key-files:
  created:
    - handlers/shared.py
    - handlers/message_handler.py
    - handlers/mention_handler.py
    - tests/test_shared.py
    - tests/test_message_handler.py
  modified:
    - app.py
    - tests/test_dm_handler.py
  deleted:
    - handlers/dm_handler.py

key-decisions:
  - "thread_ts=None posts top-level loading message; overflow chunks thread off loading_ts (not original thread_ts)"
  - "mpim handler guards require @mention match before calling _handle_question (no broadcast responses)"
  - "MENTION_RE [A-Z0-9]+ regex is correct — Slack user IDs never contain underscores"

patterns-established:
  - "anchor_ts pattern: anchor_ts = thread_ts if thread_ts is not None else loading_ts"
  - "Register handlers via register_*_handlers(app) factory functions in each handler module"

requirements-completed:
  - SURF-05

# Metrics
duration: 3min
completed: 2026-03-13
---

# Phase 3 Plan 01: Handler Refactor Summary

**Shared pipeline extracted to handlers/shared.py with thread_ts=None support, DM/mention split into dedicated modules, group DM (mpim) handler added — all 30 tests pass**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-13T01:31:12Z
- **Completed:** 2026-03-13T01:34:45Z
- **Tasks:** 2
- **Files modified:** 7 (5 created, 1 modified, 1 deleted from handlers)

## Accomplishments

- Extracted `handlers/shared.py` with `_handle_question` refactored to accept `thread_ts: str | None`, enabling slash command and App Home surfaces in Plans 02 and 03
- Split monolithic `dm_handler.py` into `message_handler.py` (DM + group DM) and `mention_handler.py` (@mentions), each importing from `shared.py`
- Added group DM (mpim) handler with @mention guard so the bot only responds when directly addressed
- 9 new tests covering the thread_ts=None path and mpim guard/happy-path; all 21 original DM tests pass with updated import paths

## Task Commits

1. **Task 1: Extract shared.py, split message/mention handlers (TDD)** - `3d1fc7c` (feat)
2. **Task 2: Update app.py registration, delete dm_handler, fix test imports** - `825e70d` (feat)

## Files Created/Modified

- `handlers/shared.py` - Shared pipeline: _handle_question, MENTION_RE, ERROR_MSG, GREETING, greeted_users, update_slow_message
- `handlers/message_handler.py` - DM (im) and group DM (mpim) lazy listeners + register_message_handlers
- `handlers/mention_handler.py` - @mention (app_mention) handler + register_mention_handler
- `tests/test_shared.py` - Tests for _handle_question with thread_ts=None and thread_ts='...'
- `tests/test_message_handler.py` - Tests for mpim guards and happy path
- `app.py` - Updated to use register_message_handlers + register_mention_handler
- `tests/test_dm_handler.py` - Import paths updated from dm_handler to message_handler/shared
- `handlers/dm_handler.py` - DELETED (code split across three new modules)

## Decisions Made

- `thread_ts=None` uses loading message ts as overflow anchor (`anchor_ts = thread_ts if thread_ts is not None else loading_ts`). This means slash command responses create one top-level message and any overflow chunks thread under it — clean UX without needing a pre-existing thread.
- mpim handler requires @mention match before acting. Group DMs can have many participants; the bot should only respond when directly addressed, not to every message.
- MENTION_RE `[A-Z0-9]+` kept unchanged — Slack user IDs are uppercase alphanumeric, no underscores. Test fixture updated to use realistic ID format (`UBOTABC123`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test fixture used unrealistic Slack user ID format with underscore**
- **Found during:** Task 1 (TDD GREEN phase)
- **Issue:** Test used `<@U_BOT123>` but MENTION_RE pattern `[A-Z0-9]+` correctly rejects underscores (real Slack IDs never have them). Test would have permanently failed.
- **Fix:** Updated test fixtures to use `<@UBOTABC123>` and `<@UBOTABC>` (realistic formats)
- **Files modified:** tests/test_message_handler.py
- **Verification:** All 9 new tests pass
- **Committed in:** 3d1fc7c (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - test fixture bug)
**Impact on plan:** Minor test fixture correction, no functional scope change.

## Issues Encountered

None - implementation matched plan exactly. The only issue was a test fixture using an invalid Slack mention format, caught during the TDD GREEN phase.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `handlers/shared.py` is ready: `_handle_question` accepts `thread_ts=None` for Plans 02 and 03
- `register_message_handlers` and `register_mention_handler` registered in `app.py`
- Plans 02 (slash commands) and 03 (App Home) can import directly from `handlers/shared.py`
- No blockers

---
*Phase: 03-interaction-surfaces*
*Completed: 2026-03-13*
