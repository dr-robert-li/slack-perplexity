---
phase: 01-core-pipeline
plan: 02
subsystem: api
tags: [slack-bolt, lazy-listener, threading, perplexity, socket-mode, pytest]

# Dependency graph
requires:
  - phase: 01-core-pipeline/01-01
    provides: query_perplexity service, format_answer and split_message utils, Bolt App object
provides:
  - DM handler with full pipeline (ack -> loading indicator -> Perplexity -> formatted answer)
  - Lazy listener registration on Bolt App for "message" events
  - First-time user greeting (greeted_users set)
  - 60-second slow-response timer with in-place update
  - Graceful error handling with friendly "@Robert Li" message
  - Threaded replies via thread_ts=event["ts"]
  - Long response splitting (split_message) across multiple thread messages
affects: [01-03]

# Tech tracking
tech-stack:
  added:
    - threading.Timer (Python stdlib, 60s timeout for slow Perplexity responses)
  patterns:
    - Lazy listener: app.event("message")(ack=fn, lazy=[fn]) — ack in <3s, processing async
    - Module-level mutable set (greeted_users) for first-time detection across requests
    - chat_update replaces loading indicator in-place; overflow chunks use chat_postMessage
    - Guard-clause pattern in handle_dm: bot_id / subtype / channel_type checked before any Slack API call

key-files:
  created:
    - handlers/__init__.py
    - handlers/dm_handler.py
    - tests/test_dm_handler.py
  modified:
    - app.py

key-decisions:
  - "Lazy listener syntax is app.event('message')(ack=fn, lazy=[fn]) not app.event('message', lazy=[fn])(fn)"
  - "greeted_users is module-level set — simple in-process state sufficient for single-process Socket Mode bot"
  - "60s timer fires update_slow_message but is cancelled immediately after query_perplexity returns"

patterns-established:
  - "Lazy listener: ack function + lazy list passed as kwargs to app.event(type)() call"
  - "Loading indicator: chat_postMessage 'Searching...', capture ts, chat_update in-place with result"
  - "Error handler: cancel timer + chat_update loading_ts with ERROR_MSG containing '@Robert Li'"

requirements-completed: [INTR-01, INTR-04, RESP-01, RESP-02, RELY-01, RELY-02, RELY-03]

# Metrics
duration: 3min
completed: 2026-03-12
---

# Phase 1 Plan 02: DM Handler Summary

**Full Slack DM pipeline: lazy listener acks in <3s, posts Searching... loading indicator, calls Perplexity pro-search, updates message in-place with cited answer, splits responses >3800 chars, handles errors with friendly @Robert Li message — 21 tests green**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-12T23:08:01Z
- **Completed:** 2026-03-12T23:10:35Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- DM handler (`handle_dm`) implements complete pipeline: guard checks, threaded loading message, 60s timer, Perplexity call, timer cancel, greeting detection, split_message chunking, chat_update first chunk, overflow chunks via chat_postMessage
- Lazy listener registered via `app.event("message")(ack=ack_dm_message, lazy=[handle_dm])` — acks within Slack's 3s limit, processing runs asynchronously
- Bot loop prevention: guard on `event.get("bot_id")` stops processing before any API call
- Full test suite: 21 tests passing (11 existing from Plan 01 + 10 new DM handler tests)

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests** - `4055486` (test)
2. **Task 1 GREEN: DM handler implementation** - `5c06786` (feat)
3. **Task 2: Register handler in app.py + fix lazy syntax** - `810d53b` (feat)

## Files Created/Modified

- `handlers/__init__.py` - Empty package init
- `handlers/dm_handler.py` - Full DM handler: constants, greeted_users set, handle_dm, update_slow_message, register_dm_handler
- `tests/test_dm_handler.py` - 10 tests covering all behavior: guards, loading message, threading, error handling, greeting, long response splitting
- `app.py` - Added import and `register_dm_handler(app)` call after App() initialization

## Decisions Made

- Lazy listener registration syntax required `app.event("message")(ack=fn, lazy=[fn])` — Bolt's `_to_listener_functions` expects a kwargs dict with `ack` and `lazy` keys, not positional arguments. Using `app.event("message", lazy=[fn])(fn)` raises `TypeError`.
- Used module-level `greeted_users = set()` for first-time greeting detection — single-process Socket Mode bot makes this sufficient without persistence.
- 60-second timer is started before the Perplexity call and cancelled immediately after — ensures "still working on it..." fires only for truly slow responses, never for fast ones.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Incorrect lazy listener registration syntax**
- **Found during:** Task 2 (register handler in app.py, full suite run)
- **Issue:** `app.event("message", lazy=[handle_dm])(ack_fn)` raises `TypeError: App.event() got an unexpected keyword argument 'lazy'` because `App.event()` does not accept a `lazy` kwarg — the lazy list must be passed to the inner `__call__` returned by `app.event(type)`
- **Fix:** Changed `register_dm_handler` to call `app.event("message")(ack=ack_dm_message, lazy=[handle_dm])` — passes both ack and lazy as kwargs to the inner callable
- **Files modified:** `handlers/dm_handler.py`
- **Verification:** `test_app_initializes` and all 10 DM handler tests pass; 21/21 green
- **Committed in:** 810d53b (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 Rule 1 bug)
**Impact on plan:** Auto-fix necessary for correct Bolt lazy listener registration. No scope creep — implementation intent unchanged.

## Issues Encountered

None beyond the auto-fixed deviation above.

## User Setup Required

None — no external service configuration required at this stage. Real credentials needed in `.env` (see `.env.example`) only when running the bot live.

## Next Phase Readiness

- Complete DM pipeline is working and tested: question -> cited answer, loading indicator, error handling, threading
- Plan 03 (deployment/smoke test) can proceed; all handlers registered on `app`
- No blockers for Plan 03

## Self-Check: PASSED

- `handlers/__init__.py` confirmed present
- `handlers/dm_handler.py` confirmed present
- `tests/test_dm_handler.py` confirmed present
- `app.py` confirmed contains `register_dm_handler`
- Commits 4055486, 5c06786, 810d53b confirmed in git log
- 21/21 tests confirmed passing (pytest tests/ -v)

---
*Phase: 01-core-pipeline*
*Completed: 2026-03-12*
