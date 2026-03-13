---
phase: 3
slug: interaction-surfaces
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pytest.ini` (testpaths = tests) |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 0 | SURF-03 | unit | `python -m pytest tests/test_slash_handler.py -x` | Wave 0 | pending |
| 03-01-02 | 01 | 0 | SURF-04 | unit | `python -m pytest tests/test_home_handler.py -x` | Wave 0 | pending |
| 03-01-03 | 01 | 0 | SURF-05 | unit | `python -m pytest tests/test_message_handler.py::TestGroupDMHandler -x` | Wave 0 | pending |
| 03-02-01 | 02 | 1 | SURF-03 | unit | `python -m pytest tests/test_slash_handler.py -x` | Wave 0 | pending |
| 03-02-02 | 02 | 1 | SURF-03 | unit | `python -m pytest tests/test_slash_handler.py::TestSlashHandlerGuards::test_empty_text_returns_ephemeral -x` | Wave 0 | pending |
| 03-02-03 | 02 | 1 | SURF-03 | unit | `python -m pytest tests/test_slash_handler.py::TestSlashHandlerGuards::test_ack_called -x` | Wave 0 | pending |
| 03-03-01 | 03 | 1 | SURF-04 | unit | `python -m pytest tests/test_home_handler.py::TestHomeHandler::test_publishes_home_view -x` | Wave 0 | pending |
| 03-04-01 | 04 | 1 | SURF-05 | unit | `python -m pytest tests/test_message_handler.py::TestGroupDMHandler::test_ignores_non_mention -x` | Wave 0 | pending |
| 03-04-02 | 04 | 1 | SURF-05 | unit | `python -m pytest tests/test_message_handler.py::TestGroupDMHandler::test_ignores_bot_messages -x` | Wave 0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_slash_handler.py` — stubs for SURF-03 (slash command ack, empty text, pipeline invocation)
- [ ] `tests/test_home_handler.py` — stubs for SURF-04 (views_publish called, view type, blocks non-empty)
- [ ] `tests/test_message_handler.py` — stubs for SURF-05 (mpim guard, @mention guard, pipeline) + existing DM tests
- [ ] `handlers/shared.py` — shared pipeline module (Wave 0 prerequisite for all new handler tests)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `/ask` slash command registered in Slack dashboard | SURF-03 | Requires Slack API dashboard access | Verify slash command exists in app settings > Slash Commands |
| App Home tab enabled in Slack dashboard | SURF-04 | Requires Slack API dashboard access | Verify App Home is toggled on in app settings > App Home |
| `mpim:history` OAuth scope added | SURF-05 | Requires Slack API dashboard access | Verify scope exists in app settings > OAuth & Permissions |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
