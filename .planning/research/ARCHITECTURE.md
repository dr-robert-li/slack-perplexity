# Architecture Research

**Domain:** Slack bot with external LLM API integration (Python + Slack Bolt + Perplexity Agent API)
**Researched:** 2026-03-13
**Confidence:** HIGH — based on official Slack Bolt docs and Perplexity Agent API docs provided locally

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        Slack Platform                            │
│  ┌────────────┐  ┌───────────────┐  ┌──────────────────────┐    │
│  │  DM / IM   │  │  Channel @    │  │  /ask Slash Command  │    │
│  │  message   │  │  mention      │  │                      │    │
│  └─────┬──────┘  └──────┬────────┘  └──────────┬───────────┘    │
│        │                │                      │                │
│        └────────────────┴──────────────────────┘                │
│                         │ WebSocket (Socket Mode)               │
└─────────────────────────┼────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                        Bot Process (app.py)                      │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                  Slack Bolt App                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │   │
│  │  │ SocketMode   │  │  Event       │  │   App Home     │  │   │
│  │  │ Handler      │  │  Listeners   │  │   Handler      │  │   │
│  │  │ (xapp token) │  │  (@mention,  │  │ (app_home_     │  │   │
│  │  │              │  │   DM, /ask)  │  │  opened event) │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘  │   │
│  └─────────┼─────────────────┼──────────────────┼───────────┘   │
│            │                 │                  │               │
│  ┌──────────▼─────────────────▼──────────────────▼───────────┐   │
│  │                    Handler Logic                          │   │
│  │  1. ack() (slash commands only — 3s deadline)             │   │
│  │  2. Post "Searching..." placeholder message               │   │
│  │  3. Call Perplexity service                               │   │
│  │  4. Format response + citations                           │   │
│  │  5. Update or reply in thread                             │   │
│  └───────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────────────────▼───────────────────────────────┐   │
│  │               Perplexity Service Layer                    │   │
│  │  client.responses.create(preset="pro-search", input=...)  │   │
│  └───────────────────────────┬───────────────────────────────┘   │
└──────────────────────────────┼───────────────────────────────────┘
                               │ HTTPS POST
                               │ POST https://api.perplexity.ai/v1/agent
┌──────────────────────────────▼───────────────────────────────────┐
│                      Perplexity Agent API                        │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│  │  Web Search     │  │  URL Fetch       │  │  LLM (auto-    │   │
│  │  Tool           │  │  Tool            │  │  selected by   │   │
│  │                 │  │                  │  │  pro-search)   │   │
│  └─────────────────┘  └──────────────────┘  └────────────────┘   │
│                                                                  │
│  Response output[] contains:                                     │
│    - type: "search_results" (urls, titles, snippets)             │
│    - type: "fetch_url_results" (page contents)                   │
│    - type: "message" (output_text — the answer)                  │
└──────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| SocketModeHandler | Maintains persistent WebSocket to Slack; receives event payloads | `SocketModeHandler(app, SLACK_APP_TOKEN).start()` in `app.py` |
| Event Listeners | Dispatch incoming Slack events to the right handler function | `@app.event("app_mention")`, `@app.message()`, `@app.command("/ask")` decorators |
| Handler Logic | Orchestrate: acknowledge, post placeholder, call Perplexity, reply in thread | Functions registered with listener decorators; use `say()` or `client.chat_postMessage()` |
| Perplexity Service Layer | Wrap Perplexity SDK calls; extract answer text and citations from response | Thin module: `perplexity_client.py` — accepts a query string, returns `(answer, citations)` |
| App Home Handler | Render a static info/instructions view in the App Home tab | `@app.event("app_home_opened")` calling `client.views_publish()` |
| Config / Env | Provide credentials to both Bolt and Perplexity SDK at startup | `.env` file read via `python-dotenv`; `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `PERPLEXITY_API_KEY` |

## Recommended Project Structure

```
slack-computer/
├── app.py                  # Entry point: App init, SocketModeHandler.start()
├── handlers/
│   ├── mention.py          # @app.event("app_mention") handler
│   ├── direct_message.py   # @app.message() handler for DMs
│   ├── slash_command.py    # @app.command("/ask") handler
│   └── app_home.py         # @app.event("app_home_opened") handler
├── services/
│   └── perplexity.py       # Perplexity SDK wrapper: query() -> (answer, citations)
├── utils/
│   └── formatting.py       # Format answer + numbered citations for Slack mrkdwn
├── requirements.txt        # slack_bolt, perplexityai, python-dotenv
└── .env                    # SLACK_BOT_TOKEN, SLACK_APP_TOKEN, PERPLEXITY_API_KEY
```

### Structure Rationale

- **handlers/:** One file per entry point (mention, DM, slash, home) keeps each event's logic isolated and independently testable. All handlers import from `services/` — never call Perplexity directly.
- **services/perplexity.py:** Single place where `perplexityai` SDK is touched. If the API contract changes, only this file needs updating. Returns typed plain data (strings/lists), not SDK objects.
- **utils/formatting.py:** Slack mrkdwn rules (citation numbering, URL formatting) belong here, not inside handlers.
- **app.py:** Thin entry point. Registers handlers via `from handlers import mention, direct_message, slash_command, app_home` and starts the socket loop.

## Architectural Patterns

### Pattern 1: Acknowledge Immediately, Work Asynchronously

**What:** Slash commands must call `ack()` within 3 seconds or Slack shows an error. Post a "Searching..." placeholder immediately, then do the slow Perplexity call, then update or reply.

**When to use:** Always for `/ask` slash command. Also good practice for `app_mention` and DM handlers to post a loading indicator before the API call.

**Trade-offs:** Adds one extra Slack API call per interaction (post placeholder + post answer). Worth it — users see immediate feedback and the 3s deadline is not a constraint.

**Example:**
```python
@app.command("/ask")
def handle_ask(ack, body, client):
    ack()  # Must happen within 3 seconds
    channel = body["channel_id"]
    user = body["user_id"]
    query = body["text"]

    # Post placeholder in thread
    placeholder = client.chat_postMessage(
        channel=channel,
        text=f"<@{user}> :mag: Searching...",
    )
    thread_ts = placeholder["ts"]

    # Call Perplexity (slow)
    answer, citations = perplexity_service.query(query)
    formatted = format_response(answer, citations)

    # Reply in thread (not update — keeps the "Searching..." visible briefly)
    client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text=formatted,
    )
```

### Pattern 2: Thread Pinning

**What:** All bot replies go into threads to keep channels clean. The thread root is always the original user message (for mentions/DMs) or the placeholder message (for slash commands).

**When to use:** Every event type. Required by the project spec.

**Trade-offs:** Slash command responses aren't auto-threaded by Slack — you must post a message first and then reply to its `ts`. For `app_mention` and DM, use `say(thread_ts=event["ts"])` to reply in the same thread as the triggering message.

**Example:**
```python
@app.event("app_mention")
def handle_mention(event, say, client):
    query = strip_bot_mention(event["text"])
    say(text=":mag: Searching...", thread_ts=event["ts"])
    answer, citations = perplexity_service.query(query)
    say(text=format_response(answer, citations), thread_ts=event["ts"])
```

### Pattern 3: Service Layer Isolation

**What:** The Perplexity SDK is called only inside `services/perplexity.py`. Handlers receive plain Python data back (strings and lists). The service layer handles SDK exceptions and translates them to a friendly error string.

**When to use:** Always. This is the boundary that makes handlers testable without a live API.

**Trade-offs:** One extra indirection layer. For a project this size it's minimal overhead and pays off during testing and when the SDK version bumps.

**Example:**
```python
# services/perplexity.py
from perplexity import Perplexity

_client = Perplexity()  # reads PERPLEXITY_API_KEY from env automatically

def query(question: str) -> tuple[str, list[dict]]:
    """Returns (answer_text, citations) or raises PerplexityError."""
    try:
        response = _client.responses.create(preset="pro-search", input=question)
        answer = response.output_text
        citations = _extract_citations(response.output)
        return answer, citations
    except Exception as e:
        raise PerplexityError(str(e)) from e

def _extract_citations(output: list) -> list[dict]:
    """Pull search_results items from response output."""
    for item in output:
        if item.type == "search_results":
            return [{"title": r.title, "url": r.url} for r in item.results]
    return []
```

## Data Flow

### Request Flow: @mention in Channel

```
User types "@BotName what is X?" in #channel
    |
    | WebSocket frame (Socket Mode)
    v
SocketModeHandler receives app_mention event payload
    |
    | dispatches to registered handler
    v
handle_mention(event, say, client)
    |
    +---> say("Searching...", thread_ts=event["ts"])   [Slack API: chat.postMessage]
    |
    +---> perplexity_service.query(query)
    |         |
    |         | HTTPS POST to api.perplexity.ai/v1/agent
    |         |   body: { "preset": "pro-search", "input": "what is X?" }
    |         |
    |         | Response: { output: [search_results, message] }
    |         |
    |     returns (answer_text, citations_list)
    |
    +---> format_response(answer_text, citations_list) -> mrkdwn string
    |
    +---> say(formatted_text, thread_ts=event["ts"])   [Slack API: chat.postMessage]

User sees threaded reply with answer + numbered clickable citations
```

### Request Flow: /ask Slash Command

```
User types "/ask what is X?" in any channel
    |
    | WebSocket frame (Socket Mode)
    v
SocketModeHandler receives slash_command payload
    |
    v
handle_ask(ack, body, client)
    |
    +---> ack()                                         [MUST happen <3s]
    |
    +---> client.chat_postMessage("Searching...")       [Slack API]
    |         returns placeholder_ts
    |
    +---> perplexity_service.query(body["text"])
    |         |
    |         | (same HTTPS POST flow as above)
    |         |
    |     returns (answer_text, citations_list)
    |
    +---> client.chat_postMessage(                      [Slack API]
              channel=channel_id,
              thread_ts=placeholder_ts,
              text=formatted_text
          )
```

### Key Data Flows

1. **Perplexity response parsing:** `response.output` is a list of typed items. The `search_results` item contains citation URLs/titles/snippets. The `message` item contains the answer via `output_text`. Both are needed; extract separately in the service layer.

2. **Error propagation:** `PerplexityError` raised in `services/perplexity.py` is caught in each handler, which then calls `say()` with the user-friendly error message: "Uh oh, it seems my brain is offline — talk to @Robert Li about trying to kick start it."

3. **Bot mention stripping:** For `app_mention` events, the raw `event["text"]` includes the bot's user ID (e.g., `<@U12345> what is X`). The handler must strip this prefix before sending to Perplexity.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 users (current) | Single process, Socket Mode, no queue needed. One `Perplexity()` client instance at module level. |
| 100-1k users | Perplexity API rate limits become relevant. Add per-user or per-workspace request throttling in the service layer. Socket Mode handles reconnection natively. |
| 1k+ users | Consider HTTP mode + a queue (e.g., Redis + Celery) to decouple Slack event receipt from Perplexity calls. Switch to HTTP deployment with a load balancer. Socket Mode is not designed for high-throughput multi-instance deployments. |

### Scaling Priorities

1. **First bottleneck:** Perplexity API latency and rate limits. Each `pro-search` call takes several seconds and has per-key quotas. Mitigation at small scale: just let calls run sequentially per handler invocation (Bolt handles concurrent events in separate threads by default).
2. **Second bottleneck:** Socket Mode is single-connection per app instance. At high event volume, switch to HTTP mode with horizontal scaling.

## Anti-Patterns

### Anti-Pattern 1: Calling Perplexity Directly Inside Handlers

**What people do:** Import and call the Perplexity SDK directly inside `handle_mention`, `handle_ask`, etc.

**Why it's wrong:** Each handler becomes tightly coupled to SDK internals. Testing requires mocking the SDK everywhere it appears. Error handling logic duplicates across handlers.

**Do this instead:** Use `services/perplexity.py` as the single call site. Handlers only call `perplexity_service.query(text)` and handle the result or a raised exception.

### Anti-Pattern 2: Forgetting to ack() Slash Commands

**What people do:** Start the Perplexity call before calling `ack()` inside a slash command handler.

**Why it's wrong:** Perplexity `pro-search` takes several seconds. Slack requires acknowledgment within 3 seconds or it shows an error to the user. The entire interaction fails visibly.

**Do this instead:** Call `ack()` as the very first line of every slash command handler, before any I/O.

### Anti-Pattern 3: Replying Outside Threads

**What people do:** Use `say(text)` without `thread_ts` in channel-based handlers.

**Why it's wrong:** Bot replies land as top-level channel messages, cluttering the channel for all members. The channel fills with bot answers unattached to the questions that prompted them.

**Do this instead:** Always pass `thread_ts=event["ts"]` to `say()` for `app_mention` events. For slash commands, post a placeholder message first and reply to its `ts`.

### Anti-Pattern 4: Posting Bot Responses to Bot's Own Messages

**What people do:** Subscribe to `message` events without filtering bot-originated messages, causing infinite response loops.

**Why it's wrong:** Bot responds to its own "Searching..." placeholder, triggering another Perplexity call, looping until rate-limited.

**Do this instead:** In `message` event handlers, check `event.get("bot_id")` or `event.get("subtype") == "bot_message"` and return early. Bolt's `@app.message()` listener filters this by default for DM handlers, but be explicit when using `@app.event("message")`.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Slack Events API | WebSocket via Socket Mode (`SocketModeHandler`) | Requires `SLACK_APP_TOKEN` (xapp-) with `connections:write` scope |
| Slack Web API | `client.chat_postMessage()`, `client.views_publish()` | Injected by Bolt into handler functions via `client` parameter; uses `SLACK_BOT_TOKEN` (xoxb-) |
| Perplexity Agent API | `POST https://api.perplexity.ai/v1/agent` via `perplexityai` SDK | `PERPLEXITY_API_KEY` env var; use `preset="pro-search"` — auto-selects model, enables web_search + fetch_url tools |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Handler -> Service | Direct function call: `perplexity_service.query(text)` | Service raises `PerplexityError` on failure; handler catches it |
| Handler -> Slack | Via Bolt-injected `say()` or `client` object | `say()` is context-aware (knows channel/thread); `client.chat_postMessage()` is explicit |
| App Home Handler -> Slack | `client.views_publish(user_id=..., view={...})` | Triggered by `app_home_opened` event; publishes a static Block Kit view |
| Entry Point -> Handlers | Python module imports (`from handlers import mention`) | Handlers self-register via decorators at import time; no manual wiring needed |

### Build Order Implications

Build in this dependency order:

1. **Config + env layer** — `.env`, `requirements.txt`, credential loading. Everything depends on credentials being available.
2. **Perplexity service layer** (`services/perplexity.py`) — No Slack dependency. Can be tested standalone with `python -c "from services.perplexity import query; print(query('test'))"`.
3. **Slack Bolt skeleton** (`app.py` + `SocketModeHandler`) — Verifies tokens work and bot connects. No handlers registered yet; just the bare `App` init.
4. **First handler: DM handler** — Simplest surface. No mention-stripping needed. Validates the full pipeline: event in -> Perplexity call -> threaded reply.
5. **Mention handler** — Adds mention-stripping logic. Builds on DM handler pattern.
6. **Slash command handler** — Adds `ack()` + placeholder + thread-reply pattern.
7. **App Home handler** — Independent of Perplexity; just `views_publish()` with static Block Kit content. Can be done any time after the skeleton.
8. **Formatting utils** — Can be extracted from handlers at any point once the response shape is understood.

## Sources

- Slack Bolt for Python official docs: https://docs.slack.dev/tools/bolt-python/getting-started (provided locally as `slack-bolt-docs.md`)
- Slack Bolt AI Chatbot tutorial: https://docs.slack.dev/tools/bolt-python/tutorial/ai-chatbot (provided locally)
- Perplexity Agent API docs: https://docs.perplexity.ai (provided locally as `pplx-docs.md`)
- Project context: `.planning/PROJECT.md`

---
*Architecture research for: Slack bot with Perplexity Agent API integration*
*Researched: 2026-03-13*
