---
phase: 03-interaction-surfaces
verified: 2026-03-13T02:10:00Z
status: human_needed
score: 3/3 must-haves verified
human_verification:
  - test: "Run /ask What is Python? in any Slack channel"
    expected: "A visible, threaded reply with a cited Perplexity answer appears in that channel (not ephemeral)"
    why_human: "Slash command end-to-end Slack API routing cannot be verified programmatically; requires live bot and Slack API dashboard config (command registered, commands scope, app reinstalled)"
  - test: "Create a group DM with the bot and another user, then send @mention the bot with a question"
    expected: "Bot replies in-thread with a cited Perplexity answer; a message in the same group DM without @mention gets no response"
    why_human: "mpim:history scope and live group DM event delivery cannot be verified without a connected Slack workspace"
  - test: "Open the bot's Home tab in Slack sidebar"
    expected: "Header shows bot name, description section present, all 4 usage methods listed (DM, @mention, /ask, group DM), contact block visible"
    why_human: "Block Kit view rendering and App Home tab activation (dashboard toggle) require live Slack workspace to confirm"
---

# Phase 3: Interaction Surfaces Verification Report

**Phase Goal:** Any Slack user can reach the bot through the `/ask` slash command, group DMs, or the App Home tab — all using the same response pipeline already built
**Verified:** 2026-03-13T02:10:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

All automated checks pass. Three live-smoke items remain for human confirmation (Slack API routing, real group DM events, App Home tab rendering). The code fully implements all three surfaces; human testing is needed to confirm Slack API dashboard configuration and real event delivery are working as expected.

The SUMMARY reports that all 6 live verification scenarios were already completed during plan execution (Task 3 was a blocking human checkpoint). This verification confirms the code artifacts match those claims. If the human checkpoint result is trusted, the phase goal is fully achieved.

### Observable Truths

| #  | Truth                                                                                          | Status     | Evidence                                                                                          |
|----|-----------------------------------------------------------------------------------------------|------------|---------------------------------------------------------------------------------------------------|
| 1  | User runs `/ask <question>` and receives a cited answer as a visible threaded reply            | ? HUMAN    | `slash_handler.py` wired; `run_ask` calls `_handle_question(thread_ts=None)`; 12 tests pass; requires live Slack verification |
| 2  | Empty `/ask` returns ephemeral help text only visible to the invoking user                    | VERIFIED   | `run_ask` guard: empty text calls `respond(text="Usage: /ask ...", response_type="ephemeral")` — 3 parametrized test cases pass |
| 3  | Group DM @mention triggers the shared answer pipeline; non-mention messages are ignored       | VERIFIED   | `handle_mpim` in `message_handler.py` guards bot_id/subtype/channel_type/MENTION_RE; 5 unit tests (4 guards + happy path) pass |
| 4  | App Home tab shows bot description and all 4 usage methods                                    | ? HUMAN    | `home_handler.py` publishes Block Kit view with header/description/divider/usage/contact; 8 tests pass; requires live tab verification |

**Score:** 3/3 must-haves verified (automated); 2 items flagged for human smoke test confirmation

### Required Artifacts

| Artifact                        | Expected                                            | Status      | Details                                                                                      |
|---------------------------------|-----------------------------------------------------|-------------|----------------------------------------------------------------------------------------------|
| `handlers/shared.py`            | `_handle_question`, `MENTION_RE`, `ERROR_MSG`, `GREETING`, `greeted_users` | VERIFIED | All symbols present; `thread_ts: str \| None` signature confirmed (line 39); anchor_ts logic confirmed (line 58) |
| `handlers/message_handler.py`   | DM (im) + group DM (mpim) lazy listeners            | VERIFIED    | `handle_dm`, `handle_mpim`, `register_message_handlers` all present and substantive          |
| `handlers/mention_handler.py`   | @mention event handler                              | VERIFIED    | `handle_mention`, `register_mention_handler` present; delegates to `_handle_question`         |
| `handlers/slash_handler.py`     | `/ask` slash command ack/lazy handler               | VERIFIED    | `ack_ask`, `run_ask`, `register_slash_handler` present; ephemeral guard implemented           |
| `handlers/home_handler.py`      | App Home Block Kit view handler                     | VERIFIED    | 6-block view (header, description, divider, usage, divider, contact); error caught + logged   |
| `handlers/dm_handler.py`        | Must NOT exist (deleted)                            | VERIFIED    | File confirmed deleted                                                                         |
| `tests/test_shared.py`          | Tests for `_handle_question` with/without `thread_ts` | VERIFIED  | 4 tests: loading threaded/top-level, overflow chunks use thread_ts vs loading_ts              |
| `tests/test_message_handler.py` | Tests for mpim guards and happy path                | VERIFIED    | 5 tests: 4 guard cases + 1 happy path                                                         |
| `tests/test_slash_handler.py`   | Tests for `/ask` command                            | VERIFIED    | 12 tests: ack always called, empty ephemeral, pipeline args, text stripping                   |
| `tests/test_home_handler.py`    | Tests for App Home view                             | VERIFIED    | 8 tests: views_publish called, view type/blocks, DM/@mention//ask/group DM content, error catch/log |

### Key Link Verification

| From                         | To                         | Via                                          | Status   | Details                                                    |
|------------------------------|----------------------------|----------------------------------------------|----------|------------------------------------------------------------|
| `handlers/message_handler.py` | `handlers/shared.py`       | `from handlers.shared import _handle_question, MENTION_RE, greeted_users` | WIRED | Line 2 confirmed |
| `handlers/mention_handler.py` | `handlers/shared.py`       | `from handlers.shared import _handle_question, MENTION_RE` | WIRED | Line 2 confirmed |
| `handlers/slash_handler.py`  | `handlers/shared.py`       | `from handlers.shared import _handle_question` | WIRED | Line 2 confirmed |
| `handlers/slash_handler.py`  | shared pipeline            | `_handle_question(..., thread_ts=None, ...)` | WIRED    | Line 30 in `run_ask`; `thread_ts=None` explicit             |
| `handlers/home_handler.py`   | Slack views API            | `client.views_publish(user_id=..., view={...})` | WIRED | Line 58 confirmed; `type: home` confirmed                  |
| `app.py`                     | `handlers/message_handler.py` | `register_message_handlers(app)`          | WIRED    | Lines 16, 21 in app.py                                     |
| `app.py`                     | `handlers/mention_handler.py` | `register_mention_handler(app)`           | WIRED    | Lines 17, 22 in app.py                                     |
| `app.py`                     | `handlers/slash_handler.py`   | `register_slash_handler(app)`             | WIRED    | Lines 18, 23 in app.py                                     |
| `app.py`                     | `handlers/home_handler.py`    | `register_home_handler(app)`              | WIRED    | Lines 19, 24 in app.py                                     |

All 9 key links wired. The no-op `app_home_opened` handler was removed before `register_home_handler` is called — no duplicate registration risk.

### Requirements Coverage

| Requirement | Source Plan  | Description                                                                              | Status        | Evidence                                                                 |
|-------------|--------------|------------------------------------------------------------------------------------------|---------------|--------------------------------------------------------------------------|
| SURF-03     | 03-02-PLAN   | User runs `/ask <question>` and receives cited answer as visible threaded reply           | SATISFIED     | `slash_handler.py` calls `_handle_question(thread_ts=None)`; 12 tests pass; human live-verify documented in SUMMARY |
| SURF-04     | 03-02-PLAN   | App Home tab displays bot description, usage instructions for all interaction methods, and current status | SATISFIED | `home_handler.py` publishes Block Kit view with all 4 methods; 8 tests pass |
| SURF-05     | 03-01-PLAN   | Bot responds to messages in group DMs using the same pipeline                            | SATISFIED     | `handle_mpim` in `message_handler.py`; mpim guard tests pass             |
| SURF-01     | **ORPHANED** | App Home tab displays bot description and usage instructions                             | SATISFIED     | Covered by `home_handler.py` (same implementation as SURF-04); not declared in any plan's `requirements` field — orphaned in REQUIREMENTS.md but fully implemented |

**Orphaned requirement note:** SURF-01 is listed as `Phase 3 / Complete` in REQUIREMENTS.md but is not declared in the `requirements:` field of either 03-01-PLAN.md or 03-02-PLAN.md. The implementation fully satisfies it (it is a subset of SURF-04 — same `home_handler.py`). No gap in functionality, but the plan frontmatter omits this ID. This is a documentation discrepancy only; no code work is needed.

### Anti-Patterns Found

No anti-patterns detected. Scanned all 5 handler files and `app.py` for TODO/FIXME/placeholder comments, empty implementations, and console-only handlers. None found.

### Human Verification Required

The SUMMARY for 03-02 documents that all 6 live scenarios were human-verified during Task 3 (blocking checkpoint). The items below are listed for completeness and re-confirmation if needed.

#### 1. `/ask` Slash Command — Live Response

**Test:** In any Slack channel, type `/ask What is the capital of France?`
**Expected:** A visible threaded reply appears in that channel with a Perplexity-sourced cited answer (not ephemeral; other users can see it)
**Why human:** Slash command routing requires the command to be registered in the Slack API dashboard (`commands` scope, `/ask` command created, app reinstalled). Cannot be verified from source code alone.

#### 2. Group DM @mention — Live Response

**Test:** Create a group DM with the bot and one other user. Send `@botname What is Python?`. Then send a plain message without @mention.
**Expected:** Bot replies in-thread to the @mention with a cited answer; bot does not reply to the plain message.
**Why human:** `mpim:history` scope must be active and the app must be reinstalled. Unit tests confirm handler logic, but real event delivery requires a live workspace.

#### 3. App Home Tab — Visual Rendering

**Test:** Open the bot in the Slack sidebar and click the "Home" tab.
**Expected:** Header showing "Kahm-pew-terr", description text, usage instructions listing DM, @mention, `/ask`, and group DM methods, and a contact line at the bottom.
**Why human:** Block Kit rendering and the Home Tab toggle (App Home settings in Slack API dashboard) require a live connected workspace.

### Gaps Summary

No gaps in implementation. All code artifacts exist, are substantive, and are properly wired. The full test suite (50 tests) passes with zero failures. The only outstanding items are:

1. **SURF-01 orphaned ID** — REQUIREMENTS.md maps SURF-01 to Phase 3 but neither plan claims it. Functionally implemented by `home_handler.py` as part of SURF-04. Documentation-only discrepancy.

2. **Human smoke test** — Three live-interaction scenarios cannot be confirmed from source code. Per the 03-02-SUMMARY, these were completed during the blocking Task 3 checkpoint. If that record is trusted, the phase goal is fully achieved.

---

_Verified: 2026-03-13T02:10:00Z_
_Verifier: Claude (gsd-verifier)_
