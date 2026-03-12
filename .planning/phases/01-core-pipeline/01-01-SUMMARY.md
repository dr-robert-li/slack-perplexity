---
phase: 01-core-pipeline
plan: 01
subsystem: api
tags: [perplexity, slack-bolt, socket-mode, pytest, python-dotenv]

# Dependency graph
requires: []
provides:
  - Perplexity service layer (query_perplexity) calling pro-search preset with citation extraction
  - Citation formatter producing Slack mrkdwn <url|title> footnotes with 5-source cap
  - Message splitter handling responses over 3800 chars
  - Slack Bolt App with SocketModeHandler entry point
  - Pytest infrastructure with shared fixtures for mock Perplexity response and mock Slack client
affects: [01-02, 01-03]

# Tech tracking
tech-stack:
  added:
    - slack_bolt (Slack Bolt SDK for Python)
    - perplexityai (Perplexity Python SDK)
    - python-dotenv (environment variable loading)
    - pytest + pytest-mock (test framework)
  patterns:
    - Module-level SDK client with placeholder api_key fallback for test-safe imports
    - TDD with RED-GREEN cycle per task
    - Mock at SDK client level (patch module-level client object)
    - Mock WebClient.auth_test to prevent real Slack API calls in tests

key-files:
  created:
    - requirements.txt
    - .env.example
    - pytest.ini
    - services/__init__.py
    - services/perplexity.py
    - utils/__init__.py
    - utils/formatting.py
    - app.py
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_perplexity_service.py
    - tests/test_formatting.py
    - tests/test_app.py
  modified: []

key-decisions:
  - "pplx_client initialized with api_key fallback to 'placeholder' so module imports work in tests without real env var"
  - "Bolt App test patches WebClient.auth_test to prevent real Slack API validation call on App() init"
  - "format_answer uses Slack mrkdwn <url|title> syntax (NOT markdown [title](url))"

patterns-established:
  - "Module-level SDK clients use os.environ.get('KEY', 'placeholder') for test-safe initialization"
  - "Perplexity response parsing: iterate response.output for type==search_results items"
  - "Citation format: [N] <url|title> appended after \\n--- divider"

requirements-completed: [RESP-03, RESP-04, SURF-02]

# Metrics
duration: 3min
completed: 2026-03-12
---

# Phase 1 Plan 01: Core Pipeline Scaffold Summary

**Perplexity pro-search service layer, Slack mrkdwn citation formatter, and Bolt Socket Mode app shell — 11 tests passing**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-12T23:03:11Z
- **Completed:** 2026-03-12T23:05:39Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments

- Perplexity service (`query_perplexity`) calls `pro-search` preset and extracts up to 5 citations as `{title, url}` dicts
- Citation formatter (`format_answer`) produces Slack mrkdwn footnotes with `<url|title>` syntax and `---` divider; falls back to "No web sources" disclaimer when empty
- Message splitter (`split_message`) chunks responses into 3800-char slices for Slack's limit
- App entry point (`app.py`) initializes `slack_bolt.App` with `SocketModeHandler` ready for Plan 02 handlers
- Full pytest infrastructure: `conftest.py` fixtures, 11 tests all green

## Task Commits

Each task was committed atomically:

1. **Task 1: Perplexity service layer** - `b299aaa` (feat)
2. **Task 2: Formatter, splitter, app entry** - `bd7c2b0` (feat)

## Files Created/Modified

- `requirements.txt` - All project deps (slack_bolt, perplexityai, python-dotenv, pytest, pytest-mock)
- `.env.example` - Three required env vars documented with placeholder values
- `pytest.ini` - testpaths=tests, python_files=test_*.py
- `services/perplexity.py` - `query_perplexity()` wrapping Perplexity SDK with pro-search preset
- `utils/formatting.py` - `format_answer()` with mrkdwn citations, `split_message()` chunker
- `app.py` - Bolt App + SocketModeHandler, handler registration deferred to Plan 02
- `tests/conftest.py` - `mock_perplexity_response` and `mock_slack_client` shared fixtures
- `tests/test_perplexity_service.py` - 5 tests for Perplexity service (pro-search call, citations, max-5, no-results, error propagation)
- `tests/test_formatting.py` - 5 tests for formatter and splitter
- `tests/test_app.py` - 1 test for app init with mocked auth.test

## Decisions Made

- Used `os.environ.get("PERPLEXITY_API_KEY", "placeholder")` for module-level `Perplexity()` init so tests can import the module without setting a real API key; the client is patched before any real call is made.
- Patched `slack_sdk.web.client.WebClient.auth_test` in the app test to prevent Slack Bolt from making a live `auth.test` API call during `App()` initialization in CI/local environments.
- `format_answer` uses Slack mrkdwn `<url|title>` link syntax — not standard markdown `[title](url)` — as required by the Slack rendering engine.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Module-level Perplexity() client crashes import without API key**
- **Found during:** Task 1 (GREEN phase — running tests)
- **Issue:** `pplx_client = Perplexity()` at module level raises `PerplexityError` when `PERPLEXITY_API_KEY` env var is absent; tests cannot import the module
- **Fix:** Changed to `Perplexity(api_key=os.environ.get("PERPLEXITY_API_KEY", "placeholder"))` — placeholder prevents crash; tests patch the client object before any real API call
- **Files modified:** `services/perplexity.py`
- **Verification:** All 5 perplexity service tests pass with patched client
- **Committed in:** b299aaa (Task 1 commit)

**2. [Rule 1 - Bug] Slack Bolt App() makes live auth.test call during initialization**
- **Found during:** Task 2 (GREEN phase — running test_app.py)
- **Issue:** `App(token="xoxb-fake-token")` triggers `auth.test` API call to Slack servers, returning `invalid_auth` and failing with `BoltError`
- **Fix:** Patched `slack_sdk.web.client.WebClient.auth_test` to return a mock success response; app initializes without network call
- **Files modified:** `tests/test_app.py`
- **Verification:** test_app_initializes passes, App instance confirmed
- **Committed in:** bd7c2b0 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both fixes necessary for tests to run in environments without real API credentials. No scope creep — implementation unchanged, only test isolation improved.

## Issues Encountered

None beyond the auto-fixed deviations above.

## User Setup Required

None — no external service configuration required at this stage. Real credentials needed in `.env` (see `.env.example`) only when running the bot live.

## Next Phase Readiness

- All Plan 02 dependencies satisfied: `query_perplexity`, `format_answer`, `split_message`, and `app` are importable and tested
- Plan 02 (DM handler) can register event listeners on `app` and call the service/formatting layers
- No blockers for Plan 02

## Self-Check: PASSED

- All 13 created files confirmed present on disk
- Commits b299aaa and bd7c2b0 confirmed in git log
- 11 tests confirmed passing (pytest tests/ -v)

---
*Phase: 01-core-pipeline*
*Completed: 2026-03-12*
