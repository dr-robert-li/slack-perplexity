# Phase 1: Core Pipeline - Research

**Researched:** 2026-03-13
**Domain:** Slack Bolt for Python (Socket Mode) + Perplexity Agent API (`pro-search` preset)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Citation formatting:**
- Footnotes at bottom: answer text with [1][2] markers inline, then a numbered sources list below a `---` divider
- Each source shown as a linked title only (e.g. `[IBM Quantum Computing](https://ibm.com/quantum)`)
- Maximum 5 sources — show only the most relevant
- If Perplexity returns no search results, show the answer with a disclaimer: "No web sources found for this query"

**Bot personality & tone:**
- Bot name in Slack: "Kahm-pew-terr" (phonetic spelling of "Computer")
- No custom system instructions — let Perplexity's `pro-search` preset respond naturally
- Answer length: adaptive — short for simple questions, longer for complex ones
- First-time DM greeting: brief intro on first message, then just answers after that

**Error scenarios:**
- All API errors (rate limits, connection failures, timeouts) use the same friendly message: "Uh oh, it seems my brain is offline — talk to @Robert Li about trying to kick start it"
- Empty/nonsensical messages: pass to Perplexity anyway — let the API handle it
- Long responses exceeding Slack's block limit: split into multiple messages in the thread

**Loading experience:**
- Loading indicator text: "Searching..."
- Edit in place: update the "Searching..." message with the full answer (single message, no delete-and-repost)
- After 60 seconds without a response: update loading message to "Taking longer than expected, still working on it..."
- No hard timeout — let Perplexity finish

### Claude's Discretion
- Exact first-time greeting wording
- How to detect "first-time" DM (simple approach is fine — no persistent storage needed)
- Loading message formatting (plain text vs block kit)
- How to handle the 60s timer implementation

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INTR-01 | User can DM the bot a question and receive a Perplexity-powered answer | `@app.event("message")` with `channel_type == "im"` filter; run Perplexity call in background thread via `app.client` |
| INTR-04 | All bot responses are posted as threaded replies (not top-level messages) | `say(thread_ts=event["ts"])` or `client.chat_postMessage(thread_ts=...)` ensures threading |
| RESP-01 | Bot posts a "Searching..." loading indicator before the answer arrives | Post loading message immediately after `ack()`, capture returned `ts`; Perplexity call happens after |
| RESP-02 | Bot updates the loading message with the full answer once Perplexity responds | `client.chat_update(channel=..., ts=loading_ts, text=...)` replaces the "Searching..." message |
| RESP-03 | Answers include numbered source citations with clickable URLs extracted from Perplexity search results | Iterate `response.output` for items with `type == "search_results"`, extract `url` and `title`, format as mrkdwn links |
| RESP-04 | Bot uses Perplexity `pro-search` preset for optimized model selection and web search | `client.responses.create(preset="pro-search", input=user_text)` — confirmed in pplx-docs |
| RELY-01 | Bot displays friendly error message when backend/Perplexity is unreachable | `except (perplexity.APIConnectionError, perplexity.RateLimitError, perplexity.APIStatusError)` → update loading message to error text |
| RELY-02 | Bot ignores its own messages to prevent self-response loops | Check `event.get("bot_id")` or compare `event["user"]` against bot's own user ID |
| RELY-03 | Handlers ack() within 3 seconds before making Perplexity API calls | Use `@app.event(..., lazy=[handler_fn])` OR post loading message synchronously then call Perplexity; the background lazy pattern is the canonical Bolt solution |
| SURF-02 | Bot runs via Socket Mode (no public URL required) | `from slack_bolt.adapter.socket_mode import SocketModeHandler; SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()` |
</phase_requirements>

---

## Summary

This phase builds a greenfield Python app using **Slack Bolt for Python** in Socket Mode and the **Perplexity Agent API** with the `pro-search` preset. The entire interaction flow is: user sends a DM → bot acks immediately + posts "Searching..." in a thread → calls Perplexity in a background thread → updates "Searching..." in-place with cited answer.

The critical architectural challenge is Slack's 3-second acknowledgment deadline. Perplexity's `pro-search` preset performs real web search, which easily exceeds 3 seconds. Bolt solves this with its **lazy listener** pattern: `@app.event("message", lazy=[do_perplexity_call])`. The decorator-based `ack()` fires instantly; the lazy function runs in a worker thread with full access to `client` and the event payload.

The response content challenge is citation extraction. The Perplexity API returns a structured `response.output` array. When `pro-search` is used, one item has `type == "search_results"` containing a `results` list with `title` and `url` fields per source. The answer text is retrieved via `response.output_text`. Combining these produces the footnote-style citation format required.

**Primary recommendation:** Use Bolt lazy listeners for the 3-second deadline. Post the loading message synchronously inside the lazy function's first action (before calling Perplexity), then update it in-place after the Perplexity call returns.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `slack_bolt` | latest (>=1.18) | Slack app framework, event routing, Socket Mode | Official Slack SDK; canonical Python framework for Slack bots |
| `slack_sdk` | bundled with bolt | `WebClient` for `chat_update`, `chat_postMessage` | Same official SDK; `bolt` depends on it |
| `perplexityai` | latest | Perplexity Agent API client | Official SDK; `from perplexity import Perplexity`; provides `output_text` convenience property |
| `python-dotenv` | latest | Load `.env` file for credentials | Standard for local dev credential management |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `threading` (stdlib) | built-in | 60-second timer for "still working" message | `threading.Timer(60, callback)` for the slow-response indicator |

### Installation
```bash
pip install slack_bolt perplexityai python-dotenv
```

---

## Architecture Patterns

### Recommended Project Structure
```
slack-computer/
├── app.py               # Entry point: App init, handler registration, SocketModeHandler.start()
├── handlers/
│   └── dm_handler.py    # DM message listener (lazy pattern)
├── services/
│   └── perplexity.py    # Perplexity client wrapper, citation parser
├── utils/
│   └── formatting.py    # Citation formatter, message splitter
├── requirements.txt
└── .env                 # SLACK_BOT_TOKEN, SLACK_APP_TOKEN, PERPLEXITY_API_KEY
```

### Pattern 1: Lazy Listener for 3-Second Deadline (RELY-03)

**What:** Bolt's lazy listener separates the `ack()` (must fire in <3 sec) from the actual work (runs in a background thread).
**When to use:** Any handler that makes a slow external API call.

```python
# Source: https://docs.slack.dev/tools/bolt-python/concepts/lazy-listeners
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.environ["SLACK_BOT_TOKEN"])

def handle_dm_message(client, event, say):
    # This runs in a background thread — no 3-second limit
    channel = event["channel"]
    thread_ts = event["ts"]
    user_text = event.get("text", "")

    # Post loading indicator as first action in this thread
    loading_resp = client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text="Searching..."
    )
    loading_ts = loading_resp["ts"]

    # Call Perplexity (may take 10-60+ seconds)
    # ... see Perplexity pattern below ...

@app.event("message", lazy=[handle_dm_message])
def ack_dm_message(ack):
    ack()  # Fires in microseconds — satisfies Slack's 3s window

if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
```

**Key insight:** The `lazy=[]` list receives the actual work functions. The decorated function only needs to call `ack()`.

### Pattern 2: Edit-in-Place Loading Message (RESP-01, RESP-02)

**What:** Post "Searching...", capture the message `ts`, then call `chat_update` with the final answer.
**When to use:** Any async response pattern where you need a placeholder.

```python
# Source: Slack Web API docs — chat.update method
# Post loading message
loading_resp = client.chat_postMessage(
    channel=channel,
    thread_ts=thread_ts,
    text="Searching..."
)
loading_ts = loading_resp["ts"]

# After Perplexity returns:
client.chat_update(
    channel=channel,
    ts=loading_ts,
    text=final_answer_text  # replaces "Searching..." in-place
)
```

### Pattern 3: Perplexity pro-search + Citation Extraction (RESP-03, RESP-04)

**What:** Call `pro-search` preset; iterate `response.output` to find search results; build footnotes.
**When to use:** All DM answers in this phase.

```python
# Source: pplx-docs.md — Agent API, Using a Preset + response structure
from perplexity import Perplexity

pplx_client = Perplexity()

response = pplx_client.responses.create(
    preset="pro-search",
    input=user_text
)

# Extract answer text
answer_text = response.output_text

# Extract search result citations
citations = []
for item in response.output:
    if item.type == "search_results":
        for result in item.results[:5]:  # max 5 sources
            citations.append({
                "title": result.title,
                "url": result.url
            })
        break  # only one search_results block expected

# Build footnote-style message
if citations:
    sources_block = "\n---\n" + "\n".join(
        f"[{i+1}] [{c['title']}]({c['url']})"
        for i, c in enumerate(citations)
    )
    full_message = answer_text + sources_block
else:
    full_message = answer_text + "\n\nNo web sources found for this query"
```

### Pattern 4: Self-Message Loop Prevention (RELY-02)

**What:** Check event for bot authorship before processing.
**When to use:** All `message` event handlers.

```python
# Source: Slack Events API docs — message event payload
@app.event("message", lazy=[handle_dm_message])
def ack_dm_message(ack, event):
    # Ignore messages from bots (including self)
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return
    ack()
```

**Note:** Bolt also accepts a filter on the decorator itself. Messages posted by the bot's own bot token carry a `bot_id` field; checking this is the standard guard.

### Pattern 5: DM Channel Type Filter (INTR-01)

**What:** Only respond to direct messages, not channel messages.
**When to use:** Phase 1 scope is DMs only.

```python
# channel_type "im" = direct message
@app.event("message")
def handle_all_messages(event, ack, client):
    ack()
    if event.get("channel_type") != "im":
        return  # ignore non-DM messages in Phase 1
    if event.get("bot_id"):
        return  # ignore bot messages
    # ... proceed with lazy handler
```

### Pattern 6: 60-Second "Still Working" Timer (Claude's Discretion)

**What:** Use `threading.Timer` to fire a callback after 60 seconds that updates the loading message.
**When to use:** Long Perplexity calls.

```python
import threading

def update_to_slow_message(client, channel, loading_ts):
    client.chat_update(
        channel=channel,
        ts=loading_ts,
        text="Taking longer than expected, still working on it..."
    )

# Start timer before Perplexity call
timer = threading.Timer(60, update_to_slow_message, args=[client, channel, loading_ts])
timer.start()

try:
    response = pplx_client.responses.create(preset="pro-search", input=user_text)
    timer.cancel()  # Cancel if Perplexity finishes before 60s
    # ... update with real answer
except Exception:
    timer.cancel()
    # ... update with error message
```

### Pattern 7: First-Time Greeting (Claude's Discretion)

**What:** Detect first DM session without persistent storage using a module-level in-memory set.
**When to use:** First message only from each user.

```python
# Simple in-memory set — resets on restart (acceptable per CONTEXT.md)
greeted_users = set()

def is_first_time(user_id: str) -> bool:
    if user_id in greeted_users:
        return False
    greeted_users.add(user_id)
    return True
```

### Pattern 8: Long Response Splitting (Locked Decision)

**What:** Slack's `chat_postMessage` text limit is ~4000 characters for plain text (40k for blocks). If the Perplexity answer exceeds this, post the first chunk as the updated loading message, then post continuation messages in the same thread.
**When to use:** Responses where `len(text) > 3800` (safe buffer below 4000 char limit).

```python
def split_message(text: str, limit: int = 3800) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:limit])
        text = text[limit:]
    return chunks
```

### Anti-Patterns to Avoid
- **Calling Perplexity before ack():** The handler will timeout. Always `ack()` immediately, do API calls after.
- **Using `say()` for threaded replies in lazy handlers:** `say()` in a lazy handler may not carry `thread_ts` context correctly. Use `client.chat_postMessage(thread_ts=...)` explicitly.
- **Deleting and reposting loading message:** The user sees a flash. Use `chat_update` to edit in-place.
- **Not cancelling the threading.Timer:** If Perplexity returns before 60s and the timer isn't cancelled, the "still working" message will overwrite the completed answer.
- **Blocking on event subtypes:** Bolt's `app.event("message")` receives ALL message subtypes (edits, deletes, bot messages). Always check `event.get("subtype")` and `event.get("bot_id")`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Slack event routing | Custom webhook parser | `slack_bolt` `@app.event()` | Handles retry deduplication, token verification, all event subtypes |
| Slack 3s deadline | `threading.Thread` manually | Bolt lazy listeners `lazy=[]` | Bolt manages thread pool, handles exceptions, logs errors |
| Perplexity auth + retries | Custom `requests` wrapper | `perplexityai` SDK | SDK provides `APIConnectionError`, `RateLimitError`, `APIStatusError` exception types; auto-retries |
| Message editing | `requests.post` to Slack API | `client.chat_update()` | SDK handles auth headers and error parsing |

---

## Common Pitfalls

### Pitfall 1: Missing `message.im` Event Subscription
**What goes wrong:** Bot never receives DMs even though code is correct.
**Why it happens:** The Slack app manifest must explicitly subscribe to `message.im` under Event Subscriptions > Bot Events.
**How to avoid:** Add `message.im` in the app's Event Subscriptions. Required scopes: `chat:write`, `im:history`, `im:read`, `im:write`.
**Warning signs:** No events arrive at all for DMs; works in channels.

### Pitfall 2: `say()` vs `client.chat_postMessage()` in Lazy Handlers
**What goes wrong:** `say(thread_ts=...)` inside a lazy handler posts to the wrong channel or fails silently.
**Why it happens:** The `say()` shortcut in lazy handlers may not capture the original channel context reliably.
**How to avoid:** In lazy handlers, always extract `channel = event["channel"]` and use `client.chat_postMessage(channel=channel, thread_ts=thread_ts, ...)` explicitly.
**Warning signs:** Messages post to DM root instead of thread, or not at all.

### Pitfall 3: Timer Races with Perplexity Response
**What goes wrong:** "Taking longer than expected..." message overwrites the completed answer if the timer fires during `chat_update`.
**Why it happens:** Race condition between the 60s timer callback and the response update.
**How to avoid:** Call `timer.cancel()` as the FIRST action after Perplexity returns (before `chat_update`). Also cancel in the `except` block.
**Warning signs:** Users see "Taking longer..." even after the answer appeared.

### Pitfall 4: Infinite Loop from Bot Own-Message Events
**What goes wrong:** Bot responds to its own "Searching..." message, entering an infinite loop.
**Why it happens:** When the bot posts any message, Slack fires a `message` event with `bot_id` set.
**How to avoid:** Check `event.get("bot_id")` at the top of every message handler and return immediately if truthy.
**Warning signs:** Bot starts sending "Searching..." messages repeatedly; API costs spike.

### Pitfall 5: `response.output` Field Access Depends on `type`
**What goes wrong:** `AttributeError` when accessing `.results` or `.content` on output items.
**Why it happens:** `response.output` is a heterogeneous list. Different items have different shapes: `type == "search_results"` has `.results`, `type == "message"` has `.content`, `type == "fetch_url_results"` has `.contents`.
**How to avoid:** Always check `item.type` before accessing fields. Only `type == "search_results"` contains citation data.
**Warning signs:** `AttributeError: 'MessageOutputItem' object has no attribute 'results'`.

### Pitfall 6: Slack `mrkdwn` vs Markdown Link Syntax
**What goes wrong:** Links render as raw text `[Title](URL)` instead of clickable links.
**Why it happens:** Slack uses its own mrkdwn format: `<URL|Title>` — NOT standard Markdown `[Title](URL)`.
**How to avoid:** Format links as `<https://example.com|Title>` for Slack messages.
**Warning signs:** Citations appear as literal bracketed text.

---

## Code Examples

### Full DM Handler (combining all patterns)

```python
# Source: Derived from slack-bolt-docs.md lazy listener pattern +
#         pplx-docs.md preset usage + response structure
import os
import threading
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from perplexity import Perplexity
import perplexity as pplx_errors

app = App(token=os.environ["SLACK_BOT_TOKEN"])
pplx_client = Perplexity()
greeted_users = set()

ERROR_MSG = "Uh oh, it seems my brain is offline — talk to @Robert Li about trying to kick start it"
GREETING = "Hey there! I'm Kahm-pew-terr, your AI research assistant. Ask me anything and I'll search the web for a cited answer."

def format_citations(output) -> str:
    for item in output:
        if item.type == "search_results":
            sources = item.results[:5]
            if not sources:
                return "\n\nNo web sources found for this query"
            lines = ["\n---"]
            for i, r in enumerate(sources, 1):
                lines.append(f"[{i}] <{r.url}|{r.title}>")
            return "\n".join(lines)
    return "\n\nNo web sources found for this query"

def handle_dm(client, event):
    channel = event["channel"]
    thread_ts = event["ts"]
    user_id = event.get("user", "")
    user_text = event.get("text", "")

    # Post loading message in thread
    loading_resp = client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text="Searching..."
    )
    loading_ts = loading_resp["ts"]

    # 60-second slow indicator timer
    timer = threading.Timer(
        60,
        lambda: client.chat_update(
            channel=channel,
            ts=loading_ts,
            text="Taking longer than expected, still working on it..."
        )
    )
    timer.start()

    try:
        # Prepend greeting for first-time users
        prompt = user_text
        if user_id not in greeted_users:
            greeted_users.add(user_id)
            greeting_prefix = GREETING + "\n\n"
        else:
            greeting_prefix = ""

        response = pplx_client.responses.create(
            preset="pro-search",
            input=prompt
        )
        timer.cancel()

        citations = format_citations(response.output)
        answer = greeting_prefix + response.output_text + citations

        # Split if needed (Slack ~4000 char plain text limit)
        chunks = [answer[i:i+3800] for i in range(0, len(answer), 3800)]

        # Update loading message with first chunk
        client.chat_update(
            channel=channel,
            ts=loading_ts,
            text=chunks[0]
        )
        # Post additional chunks as follow-ups in thread
        for chunk in chunks[1:]:
            client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=chunk
            )

    except (pplx_errors.APIConnectionError, pplx_errors.RateLimitError,
            pplx_errors.APIStatusError, Exception):
        timer.cancel()
        client.chat_update(
            channel=channel,
            ts=loading_ts,
            text=ERROR_MSG
        )

@app.event("message", lazy=[handle_dm])
def ack_message(ack, event):
    if event.get("bot_id") or event.get("subtype"):
        return  # ignore bot/system messages
    if event.get("channel_type") != "im":
        return  # Phase 1: DMs only
    ack()

if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
```

### Perplexity pro-search Response Structure (confirmed from pplx-docs.md)

```python
# response.output is a list of heterogeneous items:
# Item type "search_results" — present when pro-search runs web search:
{
  "type": "search_results",
  "queries": ["query string"],
  "results": [
    {
      "id": 1,
      "title": "Page Title",
      "url": "https://...",
      "snippet": "...",
      "date": "2025-...",
      "source": "web"
    },
    # up to N results
  ]
}

# Item type "message" — the answer text:
{
  "type": "message",
  "role": "assistant",
  "status": "completed",
  "content": [{"type": "output_text", "text": "..."}]
}

# Shortcut: response.output_text aggregates all output_text content
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Perplexity Chat Completions API (`/chat/completions`) | Perplexity Agent API (`/v1/agent` or `/v1/responses`) | 2025-2026 | New SDK `perplexityai`; `preset="pro-search"` replaces `model="llama-3.1-sonar-huge-128k-online"` |
| Manual `threading.Thread` for Slack long tasks | Bolt lazy listeners `lazy=[]` | Bolt v1.x | Bolt manages thread pool; standardized pattern |
| ngrok for local development | Socket Mode | 2021 | No public URL needed; `xapp` token + `connections:write` scope |

**Deprecated/outdated:**
- Perplexity Chat Completions API endpoint (`/chat/completions`): Replaced by Agent API. Old `model` strings like `"llama-3.1-sonar-huge-128k-online"` are not used with the new SDK.
- Slack RTM API: Replaced by Events API + Socket Mode.

---

## Open Questions

1. **Perplexity `pro-search` P95 latency under load**
   - What we know: Pro-search does real web search + URL fetching; example responses in docs show multiple search results and fetched pages
   - What's unclear: Real-world latency at P95 — could be 15s, could be 90s
   - Recommendation: The 60-second timer is a reasonable heuristic. No hard timeout by design. Monitor first real uses.

2. **`response.output` item attribute access — SDK vs raw dict**
   - What we know: The docs show JSON structure; the SDK wraps it in typed objects (`item.type`, `item.results`)
   - What's unclear: Whether `item.results` is a list of typed objects or raw dicts; whether `.url` and `.title` are direct attributes
   - Recommendation: Test SDK object access in Wave 0 smoke test. Fall back to `item.model_dump()` dict access if needed.

3. **Slack character limit for `chat_update`**
   - What we know: `chat_postMessage` text field limit is ~4000 chars; blocks have different limits
   - What's unclear: Whether `chat_update` has the same limit
   - Recommendation: Apply the same 3800-char split logic to `chat_update` to be safe.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (to be installed — not yet present) |
| Config file | `pytest.ini` — Wave 0 creation |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INTR-01 | DM triggers Perplexity call and returns answer | integration (mock Slack + Perplexity) | `pytest tests/test_dm_handler.py::test_dm_triggers_response -x` | Wave 0 |
| INTR-04 | All replies post with `thread_ts` | unit | `pytest tests/test_dm_handler.py::test_reply_is_threaded -x` | Wave 0 |
| RESP-01 | "Searching..." posted before Perplexity call | unit | `pytest tests/test_dm_handler.py::test_loading_message_posted -x` | Wave 0 |
| RESP-02 | Loading message updated in-place with answer | unit | `pytest tests/test_dm_handler.py::test_loading_message_updated -x` | Wave 0 |
| RESP-03 | Citations extracted and formatted as footnotes | unit | `pytest tests/test_formatting.py::test_citation_formatting -x` | Wave 0 |
| RESP-04 | `pro-search` preset used in Perplexity call | unit | `pytest tests/test_perplexity_service.py::test_uses_pro_search -x` | Wave 0 |
| RELY-01 | API errors trigger friendly error message | unit | `pytest tests/test_dm_handler.py::test_error_message -x` | Wave 0 |
| RELY-02 | Bot messages are ignored (no loop) | unit | `pytest tests/test_dm_handler.py::test_ignores_bot_messages -x` | Wave 0 |
| RELY-03 | `ack()` fires before Perplexity call (lazy pattern) | manual smoke | Manual: send DM, verify no timeout in Slack | N/A — architectural |
| SURF-02 | App starts with SocketModeHandler | smoke | `pytest tests/test_app.py::test_app_initializes -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/__init__.py` — test package
- [ ] `tests/test_dm_handler.py` — DM flow tests (mocked Slack client + mocked Perplexity)
- [ ] `tests/test_formatting.py` — citation formatter unit tests
- [ ] `tests/test_perplexity_service.py` — service wrapper unit tests
- [ ] `tests/test_app.py` — app initialization smoke test
- [ ] `tests/conftest.py` — shared fixtures (mock Slack client, mock Perplexity response)
- [ ] `pytest.ini` — test config
- [ ] Framework install: `pip install pytest pytest-mock` — not yet present

---

## Sources

### Primary (HIGH confidence)
- `pplx-docs.md` (local file from `docs.perplexity.ai`) — Agent API, presets, response structure, error types, streaming, tools
- `slack-bolt-docs.md` (local file from `docs.slack.dev`) — Socket Mode setup, lazy listeners, event handling, `chat_update`, `chat_postMessage`

### Secondary (MEDIUM confidence)
- CONTEXT.md integration point notes: `response.output_text`, `response.output` iteration pattern, `type == "search_results"` — consistent with official pplx-docs response examples
- Slack Events API event payload structure (`bot_id`, `channel_type`, `subtype`) — documented in slack-bolt-docs message event examples

### Tertiary (LOW confidence)
- Slack `chat_update` 4000-char limit: derived from `chat_postMessage` documented limit; `chat_update` limit not explicitly stated in provided docs — flagged as open question

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — both official SDKs confirmed from provided docs
- Architecture: HIGH — lazy listener pattern, `chat_update`, Perplexity response structure all directly shown in provided docs
- Pitfalls: HIGH for mrkdwn syntax, bot_id loop guard, timer race; MEDIUM for `chat_update` char limit (inferred)

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable APIs, but Perplexity SDK is new — check for breaking changes if > 30 days)
