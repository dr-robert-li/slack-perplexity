# Phase 3: Interaction Surfaces - Research

**Researched:** 2026-03-13
**Domain:** Slack Bolt Python — slash commands, group DM events, App Home tab, handler refactoring
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Slash command (/ask):** Visible threaded reply in the channel (not ephemeral) — consistent with @mention behavior
- **Empty /ask (no question text):** Returns ephemeral help text: "Usage: /ask <your question>"
- **Slash command requires:** Creating the command in Slack API dashboard and a new `app.command("/ask")` handler
- **Must ack() within 3 seconds**, then use `respond()` or `client.chat_postMessage` for the answer
- **Group DM:** Bot responds only to @mentions in group DMs, not all messages (prevents noise)
- **Group DM event:** Uses `message.mpim` event with `channel_type == "mpim"` guard
- **Group DM pipeline:** Same `_handle_question()` pipeline after stripping @mention tag
- **App Home tab:** Static info page — no dynamic content or recent queries
- **App Home content:** Bot description, usage instructions for all 4 methods (DM, @mention, /ask, group DM), and contact link to @Robert Li
- **App Home API:** Uses `views.publish` API with Block Kit layout
- **App Home handler:** Replace existing no-op `app_home_opened` handler
- **Handler organization:**
  - `handlers/message_handler.py` — DM and group DM message events
  - `handlers/mention_handler.py` — @mention events
  - `handlers/slash_handler.py` — /ask slash command
  - `handlers/home_handler.py` — App Home tab
  - Shared `_handle_question()` moves to `handlers/shared.py` or stays importable
  - `register_handlers(app)` in each file, called from `app.py`
  - Delete `dm_handler.py` after migration

### Claude's Discretion
- Exact Block Kit layout for App Home tab
- Whether `_handle_question()` lives in `handlers/shared.py` or `utils/`
- Exact ephemeral help text wording for empty /ask

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SURF-03 | User runs `/ask <question>` from any channel and receives a cited answer as a visible threaded reply | `app.command("/ask")` with lazy listener pattern; `ack()` + `client.chat_postMessage` with `thread_ts` for threading |
| SURF-04 | App Home tab displays bot description, usage instructions for all interaction methods, and current status | `app_home_opened` event + `client.views_publish` with Block Kit `"type": "home"` view |
| SURF-05 | Bot responds to messages in group DMs (multi-person DMs) using the same pipeline | `message.mpim` event subscription; `channel_type == "mpim"` guard; lazy listener pattern matching existing DM handler |
</phase_requirements>

---

## Summary

Phase 3 adds three interaction surfaces on top of the already-complete `_handle_question()` pipeline from Phase 1. All three surfaces are well-supported by Slack Bolt Python and require no new external dependencies.

The slash command (`/ask`) must ack within 3 seconds and then post a visible threaded reply. The lazy listener pattern (`app.command("/ask")(ack=fn, lazy=[fn])`) is the correct approach — it mirrors the existing DM handler pattern and keeps the long-running Perplexity call off the ack thread. The key implementation decision is to use `client.chat_postMessage` for the answer rather than `respond()`, because `respond()` does not support threading — it posts to the channel root. To get a threaded reply, the handler must extract `channel_id` from the slash command body and call `chat_postMessage` with `thread_ts` set to the slash command's invocation timestamp (`body["ts"]` is not present; use the response from the initial "Searching..." postMessage as the thread anchor).

Group DM support requires subscribing to the `message.mpim` event (scope: `mpim:history`) and guarding on `channel_type == "mpim"`. Only @mentions should trigger responses, so the existing `MENTION_RE` regex guard from `dm_handler.py` applies directly.

The App Home tab replaces the existing no-op `app_home_opened` handler with a `client.views_publish` call using a Block Kit view of `"type": "home"`. The content is static and defined at handler-write time.

**Primary recommendation:** Use the lazy listener pattern for all three new surfaces to maintain the established ack/lazy separation. Move `_handle_question()` to `handlers/shared.py` to eliminate any circular import risk when splitting handlers across files.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| slack_bolt | current (in requirements.txt) | Slash command, event, and App Home handlers | Already in use; `app.command()`, `app.event()`, `client.views_publish` all built-in |
| slack_sdk | (transitive via slack_bolt) | Block Kit view construction (dicts), Slack Web API methods | Already in use; `client.chat_postMessage`, `client.chat_update`, `client.views_publish` |

### No New Dependencies
All functionality is provided by the existing `slack_bolt` install. No new packages are required for this phase.

**Installation:**
```bash
# No new packages — existing requirements.txt is sufficient
```

---

## Architecture Patterns

### Recommended Project Structure

```
handlers/
├── shared.py          # _handle_question(), MENTION_RE, ERROR_MSG, GREETING, greeted_users
├── message_handler.py # DM (channel_type im) + group DM (channel_type mpim)
├── mention_handler.py # app_mention events (unchanged behavior)
├── slash_handler.py   # /ask command
├── home_handler.py    # app_home_opened — views.publish
└── __init__.py        # unchanged
app.py                 # imports register_* from each handler file
```

### Pattern 1: Slash Command with Lazy Listener

**What:** `app.command("/ask")` with ack/lazy split — ack within 3 seconds, Perplexity call in lazy
**When to use:** Any slash command triggering a slow operation (Perplexity P95 > 3s)

```python
# Source: https://docs.slack.dev/tools/bolt-python/concepts/lazy-listeners
def ack_ask_command(ack, body):
    text = (body.get("text") or "").strip()
    if not text:
        ack(response_action=None)  # ack first, ephemeral help posted separately
    else:
        ack()

def handle_ask_command(client, body, respond):
    text = (body.get("text") or "").strip()
    if not text:
        respond(
            text="Usage: /ask <your question>",
            response_type="ephemeral",
        )
        return
    channel = body["channel_id"]
    user_id = body["user_id"]
    _handle_question(client, channel=channel, thread_ts=None, user_id=user_id, user_text=text)

app.command("/ask")(ack=ack_ask_command, lazy=[handle_ask_command])
```

**Threading note for /ask:** Slash commands do not carry a message `ts` in the body. To thread the answer, `_handle_question` posts "Searching..." with no `thread_ts` first (creating a top-level message), then uses that message's `ts` as the thread anchor for all subsequent updates/posts. This is the same behavior as @mention: the loading message becomes the thread parent.

### Pattern 2: Group DM Handler with @mention Guard

**What:** Listen to `message` events, filter to `channel_type == "mpim"`, require @mention
**When to use:** Any bot that should respond in group DMs only when addressed

```python
# Source: https://docs.slack.dev/reference/events/message.mpim
def ack_mpim_message(ack, event):
    if event.get("bot_id"):
        return
    if event.get("subtype"):
        return
    if event.get("channel_type") != "mpim":
        return
    # Only ack if @mentioned
    raw_text = event.get("text", "")
    if not MENTION_RE.search(raw_text):
        return
    ack()

def handle_mpim_message(client, event):
    if event.get("bot_id"):
        return
    if event.get("subtype"):
        return
    if event.get("channel_type") != "mpim":
        return
    raw_text = event.get("text", "")
    user_text = MENTION_RE.sub("", raw_text).strip()
    if not user_text:
        return
    _handle_question(
        client,
        channel=event["channel"],
        thread_ts=event["ts"],
        user_id=event.get("user", ""),
        user_text=user_text,
    )

app.event("message")(ack=ack_mpim_message, lazy=[handle_mpim_message])
```

**Important:** The existing DM ack function only acks `channel_type == "im"` events. This new handler must be a separate registration or the combined `message_handler.py` must ack both `im` and `mpim` events correctly. The safest pattern is two separate `app.event("message")` registrations (one per channel_type), each with their own ack/lazy pair.

### Pattern 3: App Home Tab

**What:** Publish a static Block Kit view when user opens App Home
**When to use:** Any informational home tab

```python
# Source: https://docs.slack.dev/tools/bolt-python/concepts/app-home
@app.event("app_home_opened")
def handle_app_home_opened(client, event, logger):
    try:
        client.views_publish(
            user_id=event["user"],
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "Kahm-pew-terr"},
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Your AI research assistant. Ask a question, get a cited answer from the web.",
                        },
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*How to use:*\n• *DM the bot* — send any question directly\n• *@mention in a channel* — `@Kahm-pew-terr what is X?`\n• */ask command* — `/ask <your question>` from any channel\n• *Group DM* — @mention the bot in a group DM",
                        },
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Issues? Contact <@UROBERTLI> (Robert Li).",
                        },
                    },
                ],
            },
        )
    except Exception as e:
        logger.error(f"App Home publish failed: {e}")
```

**Discretion note:** The planner may choose the exact block layout. The above is the recommended minimal structure using mrkdwn bullets for instructions and a header block. Robert Li's user ID (`UROBERTLI` is a placeholder) needs to be hardcoded or fetched via `client.users_lookupByEmail` — hardcoding is simpler and appropriate for a single-workspace install.

### Pattern 4: Shared Module (`handlers/shared.py`)

**What:** Move `_handle_question()`, `MENTION_RE`, `ERROR_MSG`, `GREETING`, `greeted_users` to a shared module
**Why:** Prevents circular imports when `message_handler.py`, `mention_handler.py`, and `slash_handler.py` all need the same pipeline

```python
# handlers/shared.py
import re
import threading

from services.perplexity import query_perplexity
from utils.formatting import format_answer, split_message

greeted_users: set = set()
ERROR_MSG = "Uh oh, it seems my brain is offline — talk to @Robert Li about trying to kick start it"
GREETING = (
    "Hey there! I'm Kahm-pew-terr, your AI research assistant. "
    "Ask me anything and I'll search the web for a cited answer.\n\n"
)
MENTION_RE = re.compile(r"<@[A-Z0-9]+>\s*")

def _handle_question(client, channel: str, thread_ts: str | None, user_id: str, user_text: str) -> None:
    ...  # exact code from dm_handler.py
```

### Anti-Patterns to Avoid

- **Using `respond()` for threaded replies from `/ask`:** `respond()` posts to the channel root or as ephemeral — it cannot set `thread_ts`. Use `client.chat_postMessage` with explicit `thread_ts` for threading.
- **Registering a single `app.event("message")` handler that acks both `im` and `mpim`:** If the ack function returns without calling `ack()` for one channel type, Slack logs "unhandled event" warnings. Use separate registrations or ensure ack covers both `im` and `mpim` branches.
- **Leaving the no-op `app_home_opened` in `app.py`:** Must be replaced, not added to — Bolt raises an error for duplicate event registrations.
- **Posting App Home content as top-level messages:** Must use `client.views_publish`, not `chat_postMessage`, for the Home tab.
- **Using `respond()` with `response_type: "in_channel"` for slash command answers:** While this posts visibly, it does not thread the reply. `chat_postMessage` with `thread_ts` is required for the threaded pattern.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 3-second ack timeout | Custom threading/timeout logic | Bolt lazy listener pattern | Bolt handles the ack/lazy split natively |
| Block Kit JSON | Custom HTML/template rendering | Inline dicts or Block Kit Builder | Slack renders Block Kit; no HTML needed |
| @mention stripping in group DMs | New regex | Existing `MENTION_RE` from `dm_handler.py` | Already correct and tested |
| Response URL handling | Manual HTTP POST to response_url | `respond()` (for ephemeral) or `client.chat_postMessage` (for visible) | Bolt injects both; no manual requests needed |

---

## Common Pitfalls

### Pitfall 1: Slash Command Threading — No `ts` in Body

**What goes wrong:** Developer tries to use `body["ts"]` or `body["message_ts"]` to thread the answer. These keys do not exist in slash command payloads.

**Why it happens:** Slash commands are not message events — their body contains `channel_id`, `user_id`, `text`, `command`, `response_url`, `trigger_id`, but no message timestamp.

**How to avoid:** Post the "Searching..." message first (no `thread_ts`) to get a timestamp from Slack, then use that timestamp as the `thread_ts` for the final answer. This creates a two-message thread anchored by the loading message.

**Warning signs:** `KeyError: 'ts'` in slash handler on first attempt.

### Pitfall 2: Double Registration of `message` Event

**What goes wrong:** `app.event("message")` is registered twice — once for `im` (existing) and once for `mpim` (new). Bolt may process both handlers or warn about duplicate registrations depending on version.

**Why it happens:** Bolt routes all `message` events to all registered `message` handlers; the filtering is up to each handler's ack/lazy logic.

**How to avoid:** Combine both `im` and `mpim` handling into a single `message_handler.py` with a shared ack function that acks both channel types, and separate lazy functions that each guard on their specific channel_type before processing.

**Warning signs:** Both handlers fire on a DM, or "unhandled event" warnings for mpim messages.

### Pitfall 3: `views_publish` Requires `home` Tab Enabled in App Config

**What goes wrong:** `views_publish` call fails silently or returns an error — App Home tab not visible in Slack.

**Why it happens:** The App Home tab must be enabled in the Slack app configuration under "App Home > Show Tabs > Home Tab".

**How to avoid:** Verify "Home Tab" is enabled in the Slack API dashboard before testing. This is a one-time dashboard configuration, not a code change.

**Warning signs:** `views_publish` returns `{"ok": false, "error": "invalid_arguments"}` or Home tab shows blank.

### Pitfall 4: `mpim:history` Scope Not Granted

**What goes wrong:** Bot receives no `message.mpim` events even after subscription.

**Why it happens:** The bot token needs the `mpim:history` scope to receive group DM message events. If the app was installed before this scope was added, the token must be re-issued by reinstalling the app.

**How to avoid:** Add `mpim:history` to OAuth scopes before testing. After adding scopes, reinstall the app to the workspace to issue a new token with the updated scope set.

**Warning signs:** No events appear in logs for group DM messages; no Bolt listener fires.

### Pitfall 5: `respond()` Default Is Ephemeral

**What goes wrong:** Developer uses `respond(text="...")` expecting a visible in-channel reply but gets an ephemeral message only the invoking user can see.

**Why it happens:** `respond()` defaults to `response_type: "ephemeral"`. The empty `/ask` help text is intentionally ephemeral — but the answer must be visible.

**How to avoid:** For the help text on empty `/ask`, use `respond(text="...", response_type="ephemeral")` explicitly. For the actual answer, use `client.chat_postMessage` (not `respond()`).

**Warning signs:** Answer appears only to the user who ran `/ask`, not the rest of the channel.

---

## Code Examples

### Slash Command — Ack + Lazy (verified pattern)

```python
# Source: https://docs.slack.dev/tools/bolt-python/concepts/lazy-listeners
def ack_ask(ack, body):
    ack()  # Always ack; lazy function handles empty-text case

def run_ask(client, body, respond):
    text = (body.get("text") or "").strip()
    if not text:
        respond(text="Usage: /ask <your question>", response_type="ephemeral")
        return
    _handle_question(
        client,
        channel=body["channel_id"],
        thread_ts=None,   # slash commands have no ts; _handle_question creates thread anchor
        user_id=body["user_id"],
        user_text=text,
    )

app.command("/ask")(ack=ack_ask, lazy=[run_ask])
```

### App Home — views.publish (verified pattern)

```python
# Source: https://docs.slack.dev/tools/bolt-python/concepts/app-home
@app.event("app_home_opened")
def handle_home(client, event, logger):
    try:
        client.views_publish(
            user_id=event["user"],
            view={"type": "home", "blocks": [...]},
        )
    except Exception as e:
        logger.error(f"Home publish error: {e}")
```

### Group DM Guard (verified pattern)

```python
# Source: https://docs.slack.dev/reference/events/message.mpim
# channel_type == "mpim" for group DMs
if event.get("channel_type") != "mpim":
    return
raw_text = event.get("text", "")
if not MENTION_RE.search(raw_text):
    return  # Only respond to @mentions in group DMs
```

### `_handle_question` — Threading for Slash Commands

The current signature is `_handle_question(client, channel, thread_ts, user_id, user_text)`.
For slash commands, pass `thread_ts=None` — the function posts "Searching..." without `thread_ts` (creating a top-level message), then threads all subsequent messages on that loading message's `ts`.

No signature change is needed if the function already handles `thread_ts=None` by omitting the param from the first `chat_postMessage` call. Verify this during implementation.

---

## Slack API Dashboard Configuration Required

This phase has one mandatory out-of-code step:

1. **Create `/ask` slash command** in the Slack API dashboard (api.slack.com/apps):
   - Navigate to your app → "Slash Commands" → "Create New Command"
   - Command: `/ask`
   - Description: `Ask a question and get a cited answer`
   - Usage hint: `<your question>`
   - For Socket Mode apps: **no URL required** — leave blank or the field will be hidden

2. **Enable App Home tab** in the Slack API dashboard:
   - Navigate to your app → "App Home" → "Show Tabs" → enable "Home Tab"

3. **Add OAuth scopes** (if not already present):
   - `commands` — required for slash commands
   - `mpim:history` — required to receive group DM message events

4. **Re-install app** to workspace after scope changes to issue updated token.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HTTP webhook URL required for slash commands | Socket Mode — no URL needed | 2020 (Socket Mode GA) | Slash commands work without public URL |
| `respond()` for all slash command replies | `respond()` for ephemeral, `chat_postMessage` for visible/threaded | N/A | Threading requires chat_postMessage |

---

## Open Questions

1. **`_handle_question` behavior when `thread_ts=None`**
   - What we know: Current implementation always passes `thread_ts=event["ts"]` for messages
   - What's unclear: Does the function handle `thread_ts=None` correctly (omits param from postMessage)?
   - Recommendation: Read `_handle_question` source during Wave 1 and add a `thread_ts=None` guard if needed before wiring up the slash handler

2. **Robert Li's Slack user ID for App Home**
   - What we know: App Home should link to @Robert Li; need the actual Slack user ID
   - What's unclear: The user ID is workspace-specific and not in code
   - Recommendation: Hardcode as a constant in `home_handler.py`; the planner should note this as a value to confirm at implementation time

3. **`app_home_opened` duplicate handler conflict**
   - What we know: `app.py` currently has a no-op `app_home_opened` handler
   - What's unclear: Whether Bolt raises on duplicate registration or silently uses last-registered
   - Recommendation: Delete the no-op from `app.py` before adding the real handler in `home_handler.py`

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pytest.ini` (testpaths = tests) |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SURF-03 | `/ask <question>` posts visible threaded reply | unit | `python -m pytest tests/test_slash_handler.py -x` | Wave 0 |
| SURF-03 | Empty `/ask` returns ephemeral help text | unit | `python -m pytest tests/test_slash_handler.py::TestSlashHandlerGuards::test_empty_text_returns_ephemeral -x` | Wave 0 |
| SURF-03 | `/ask` acks within 3 seconds (lazy pattern) | unit | `python -m pytest tests/test_slash_handler.py::TestSlashHandlerGuards::test_ack_called -x` | Wave 0 |
| SURF-04 | `app_home_opened` calls `views_publish` | unit | `python -m pytest tests/test_home_handler.py -x` | Wave 0 |
| SURF-04 | Home view has `type: home` with blocks | unit | `python -m pytest tests/test_home_handler.py::TestHomeHandler::test_publishes_home_view -x` | Wave 0 |
| SURF-05 | Group DM @mention triggers `_handle_question` | unit | `python -m pytest tests/test_message_handler.py::TestGroupDMHandler -x` | Wave 0 |
| SURF-05 | Group DM non-mention is ignored | unit | `python -m pytest tests/test_message_handler.py::TestGroupDMHandler::test_ignores_non_mention -x` | Wave 0 |
| SURF-05 | Group DM bot message is ignored | unit | `python -m pytest tests/test_message_handler.py::TestGroupDMHandler::test_ignores_bot_messages -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_slash_handler.py` — covers SURF-03 (slash command ack, empty text, pipeline invocation)
- [ ] `tests/test_home_handler.py` — covers SURF-04 (views_publish called, view type, blocks non-empty)
- [ ] `tests/test_message_handler.py` — covers SURF-05 (mpim guard, @mention guard, pipeline) + existing DM tests migrated from `test_dm_handler.py`
- [ ] `handlers/shared.py` — shared pipeline module (Wave 0 prerequisite for all new handler tests)

*(Existing `tests/test_dm_handler.py` — DM tests migrate to `test_message_handler.py` or remain as-is; recommend keeping as-is to avoid breaking changes during migration)*

---

## Sources

### Primary (HIGH confidence)
- [Slack Bolt Python — Lazy Listeners](https://docs.slack.dev/tools/bolt-python/concepts/lazy-listeners) — slash command lazy pattern, ack/lazy syntax
- [Slack Bolt Python — Slash Commands](https://docs.slack.dev/tools/bolt-python/concepts/commands) — app.command() registration, respond() usage
- [Slack Bolt Python — App Home](https://docs.slack.dev/tools/bolt-python/concepts/app-home) — views_publish, app_home_opened event pattern
- [Slack Docs — message.mpim event](https://docs.slack.dev/reference/events/message.mpim) — event payload structure, channel_type == "mpim"
- [Slack Docs — Implementing Slash Commands](https://docs.slack.dev/interactivity/implementing-slash-commands) — response_type in_channel vs ephemeral, payload fields

### Secondary (MEDIUM confidence)
- [Slack Docs — App Manifest Reference](https://docs.slack.dev/reference/app-manifest/) — slash_commands definition, Socket Mode omits url field
- [Slack Docs — mpim:read scope](https://docs.slack.dev/reference/scopes/mpim.read/) — MPIM scope family (mpim:history required for events)
- WebSearch: `commands` bot scope required for slash commands; Socket Mode omits URL for slash command definition

### Tertiary (LOW confidence)
- None — all critical claims verified with official documentation

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use; no new packages
- Architecture: HIGH — patterns verified against official Bolt Python docs and existing code
- Pitfalls: HIGH — slash command threading trap and respond() default verified against official Slack docs
- Slack dashboard config: HIGH — verified Socket Mode omits URL, App Home tab enable documented

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (Slack Bolt API is stable; unlikely to change in 30 days)
