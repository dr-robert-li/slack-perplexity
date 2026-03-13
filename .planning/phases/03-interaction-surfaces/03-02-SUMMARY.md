---
phase: 03-interaction-surfaces
plan: "02"
subsystem: api
tags: [slack, bolt, slash-command, app-home, block-kit, tdd]

requires:
  - phase: 03-interaction-surfaces/03-01
    provides: handlers/shared.py with _handle_question, group DM support via MPIM handler

provides:
  - /ask slash command handler (ack/lazy pattern, ephemeral guard for empty input)
  - App Home tab handler (Block Kit home view, 4 usage methods, error handling)
  - Both handlers wired into app.py with no-op removal

affects:
  - Phase 04 (channel context) — slash command posts top-level; context window design must account for thread_ts=None anchor pattern

tech-stack:
  added: []
  patterns:
    - "ack/lazy pattern: ack function calls ack() unconditionally; lazy list handles business logic"
    - "Block Kit home view: type=home, blocks list with header/section/divider structure"
    - "Patch path convention: patch handlers.slash_handler._handle_question not handlers.shared._handle_question"

key-files:
  created:
    - handlers/slash_handler.py
    - handlers/home_handler.py
    - tests/test_slash_handler.py
    - tests/test_home_handler.py
  modified:
    - app.py

key-decisions:
  - "ack unconditional: ack_ask always calls ack(); empty text is handled in run_ask (lazy), not ack"
  - "thread_ts=None for slash command: _handle_question posts top-level loading message; overflow chunks thread off loading_ts"
  - "ROBERT_LI_UID constant in home_handler.py with TODO comment for real UID replacement"

patterns-established:
  - "Patch at import site: mock handlers.slash_handler._handle_question (not handlers.shared) since the name is bound in slash_handler's namespace"
  - "Block Kit text extraction for tests: flatten all block text values into one string for content assertions"

requirements-completed:
  - SURF-03
  - SURF-04

duration: 2min
completed: 2026-03-13
---

# Phase 3 Plan 02: Slash Command and App Home Handler Summary

**/ask slash command with ephemeral guard + App Home Block Kit view covering all 4 interaction methods, wired into app.py via ack/lazy pattern**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-13T01:37:09Z
- **Completed:** 2026-03-13T01:39:13Z
- **Tasks:** 2 of 3 (Task 3 is a live verification checkpoint awaiting human)
- **Files modified:** 5

## Accomplishments
- Implemented `/ask` slash command using Bolt's ack/lazy pattern: unconditional ack, lazy handler with empty-text ephemeral guard, and full pipeline via `_handle_question(thread_ts=None)`
- Implemented App Home tab handler publishing a Block Kit `home` view with header, description, 4 usage methods (DM, @mention, /ask, group DM), and contact block; errors caught and logged
- Removed the no-op `app_home_opened` handler from app.py and registered both new handlers — full test suite passes with 50 tests, zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1 RED — Failing tests** - `ace886e` (test)
2. **Task 1 GREEN — Handler implementations** - `bdcb7de` (feat)
3. **Task 2 — Wire into app.py** - `cb12809` (feat)

_Note: TDD task has two commits (test → feat)_

## Files Created/Modified
- `handlers/slash_handler.py` - /ask ack/lazy handlers and register_slash_handler
- `handlers/home_handler.py` - App Home Block Kit view handler and register_home_handler
- `app.py` - Removed no-op handler; added slash and home handler registration
- `tests/test_slash_handler.py` - 12 tests: ack, empty text, pipeline args, text stripping
- `tests/test_home_handler.py` - 8 tests: views_publish, view type/blocks, content coverage, error handling

## Decisions Made
- Ack is unconditional (per plan spec): empty text check happens in the lazy `run_ask` function, keeping ack fast
- `ROBERT_LI_UID` left as a named constant with a TODO comment rather than hardcoded, making the UID easy to update

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test patch path for _handle_question**
- **Found during:** Task 1 GREEN (running tests after implementing handlers)
- **Issue:** Tests patched `handlers.shared._handle_question` but `slash_handler.py` imports the function directly, binding it in its own namespace; the patch had no effect
- **Fix:** Changed all patch paths to `handlers.slash_handler._handle_question`
- **Files modified:** tests/test_slash_handler.py
- **Verification:** 20 handler tests pass after fix
- **Committed in:** bdcb7de (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in test patch path)
**Impact on plan:** Fix was necessary for test correctness. No scope creep.

## Issues Encountered
None beyond the patch path fix above.

## User Setup Required

**External services require manual Slack API dashboard configuration before live verification (Task 3):**

1. **Create /ask slash command:** api.slack.com/apps → your app → Slash Commands → Create New Command
   - Command: `/ask`
   - Description: `Ask a question and get a cited answer`
   - Usage hint: `<your question>`
   - No URL needed (Socket Mode)

2. **Enable Home Tab:** App Home → Show Tabs → enable "Home Tab"

3. **Add OAuth scopes if missing:** OAuth & Permissions → add `commands` and `mpim:history`

4. **Reinstall app to workspace** after any scope changes

5. **Set real UID:** Update `ROBERT_LI_UID` constant in `handlers/home_handler.py` with the actual Slack user ID

## Next Phase Readiness
- All three interaction surfaces coded: DM (Phase 1), @mention (Phase 1), group DM (03-01), /ask (this plan), App Home (this plan)
- Live verification checkpoint (Task 3) required before Phase 3 is complete
- After Task 3 passes: Phase 4 (channel context) can begin

---
*Phase: 03-interaction-surfaces*
*Completed: 2026-03-13*
