---
phase: 1
slug: core-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (to be installed — Wave 0) |
| **Config file** | `pytest.ini` — Wave 0 creation |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | 01 | 1 | INTR-01 | integration | `pytest tests/test_dm_handler.py::test_dm_triggers_response -x` | ❌ W0 | ⬜ pending |
| TBD | 01 | 1 | INTR-04 | unit | `pytest tests/test_dm_handler.py::test_reply_is_threaded -x` | ❌ W0 | ⬜ pending |
| TBD | 01 | 1 | RESP-01 | unit | `pytest tests/test_dm_handler.py::test_loading_message_posted -x` | ❌ W0 | ⬜ pending |
| TBD | 01 | 1 | RESP-02 | unit | `pytest tests/test_dm_handler.py::test_loading_message_updated -x` | ❌ W0 | ⬜ pending |
| TBD | 01 | 1 | RESP-03 | unit | `pytest tests/test_formatting.py::test_citation_formatting -x` | ❌ W0 | ⬜ pending |
| TBD | 01 | 1 | RESP-04 | unit | `pytest tests/test_perplexity_service.py::test_uses_pro_search -x` | ❌ W0 | ⬜ pending |
| TBD | 01 | 1 | RELY-01 | unit | `pytest tests/test_dm_handler.py::test_error_message -x` | ❌ W0 | ⬜ pending |
| TBD | 01 | 1 | RELY-02 | unit | `pytest tests/test_dm_handler.py::test_ignores_bot_messages -x` | ❌ W0 | ⬜ pending |
| TBD | 01 | 1 | RELY-03 | manual smoke | Manual: send DM, verify no timeout in Slack | N/A | ⬜ pending |
| TBD | 01 | 1 | SURF-02 | smoke | `pytest tests/test_app.py::test_app_initializes -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — test package
- [ ] `tests/test_dm_handler.py` — stubs for INTR-01, INTR-04, RESP-01, RESP-02, RELY-01, RELY-02
- [ ] `tests/test_formatting.py` — stubs for RESP-03
- [ ] `tests/test_perplexity_service.py` — stubs for RESP-04
- [ ] `tests/test_app.py` — stubs for SURF-02
- [ ] `tests/conftest.py` — shared fixtures (mock Slack client, mock Perplexity client)
- [ ] `pytest` — install via requirements.txt

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ack() fires before Perplexity call | RELY-03 | Architectural — lazy listener pattern verified by absence of Slack timeout | Send DM to bot, verify no "dispatch_failed" in Slack |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
