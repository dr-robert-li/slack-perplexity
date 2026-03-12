---
phase: 01-core-pipeline
plan: 03
subsystem: infra
tags: [slack, socket-mode, .env, .gitignore, smoke-test, credentials]

# Dependency graph
requires:
  - phase: 01-core-pipeline/01-02
    provides: DM handler with full pipeline, lazy listener registration, app.py with SocketModeHandler
provides:
  - .gitignore excluding .env, __pycache__, .pytest_cache, *.pyc, *.egg-info
  - .env placeholder file (not committed) ready for real credentials
  - Live smoke test confirmation (pending human-action checkpoint)
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - .env excluded from git via .gitignore; .env.example committed as credential template

key-files:
  created:
    - .gitignore
    - .env (not committed — gitignored)
  modified: []

key-decisions:
  - ".env is never committed — .gitignore entry ensures credentials are always local-only"
  - "Placeholder values in .env use obvious sentinel patterns (xoxb-your-token-here) to prevent accidental use of unfilled credentials"

patterns-established:
  - ".env excluded from git at project root; .env.example is the committed credential template"

requirements-completed: [RELY-03, SURF-02]

# Metrics
duration: 1min
completed: 2026-03-13
---

# Phase 1 Plan 03: Credentials and Live Smoke Test Summary

**.gitignore and .env placeholder created; live Slack smoke test awaiting real credentials from user**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-03-12T23:12:37Z
- **Completed:** 2026-03-13 (paused at checkpoint)
- **Tasks:** 1 of 2 complete (Task 2 is human-action checkpoint)
- **Files modified:** 2

## Accomplishments

- `.gitignore` created — excludes `.env`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `*.egg-info/`
- `.env` created with placeholder values (`xoxb-your-token-here`, `xapp-your-token-here`, `pplx-your-key-here`) — not committed, gitignored
- Bot is ready for live smoke test once real credentials are provided

## Task Commits

Each task was committed atomically:

1. **Task 1: Create .env file and add .gitignore** - `e0ff165` (chore)
2. **Task 2: Live smoke test** - pending human-action checkpoint

## Files Created/Modified

- `.gitignore` - Excludes .env, Python cache dirs, test cache, egg-info
- `.env` - Placeholder credential file (gitignored, not tracked)

## Decisions Made

- `.env` is never committed — `.gitignore` entry is the enforcement mechanism. `.env.example` remains the committed template.
- Placeholder values use explicit sentinel strings so the bot will fail fast if credentials are not replaced (Slack and Perplexity SDKs will raise auth errors).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

**Live smoke test requires manual Slack and Perplexity configuration.** Populate `.env` with:

- `SLACK_BOT_TOKEN` (xoxb-...) — Slack App > OAuth & Permissions > Bot User OAuth Token
- `SLACK_APP_TOKEN` (xapp-...) — Slack App > Basic Information > App-Level Tokens (needs `connections:write` scope)
- `PERPLEXITY_API_KEY` — Perplexity Dashboard > API Keys

Slack app dashboard configuration required:
- Enable Socket Mode: Slack App > Socket Mode > toggle ON
- Subscribe to `message.im` event: Slack App > Event Subscriptions > Subscribe to Bot Events
- Add scopes: `chat:write`, `im:history`, `im:read`, `im:write` (Slack App > OAuth & Permissions > Bot Token Scopes)

Then run `python app.py` and send a DM to the bot.

## Next Phase Readiness

- All code complete and tested (21 tests passing from Plans 01-02)
- Only credential provisioning and live verification remain
- No blockers beyond user providing real Slack/Perplexity credentials

---
*Phase: 01-core-pipeline*
*Completed: 2026-03-13*
