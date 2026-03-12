# Stack Research

**Domain:** Python Slack bot with Perplexity Agent API integration (Socket Mode)
**Researched:** 2026-03-13
**Confidence:** HIGH — all versions verified against PyPI, all API patterns verified against local reference docs (slack-bolt-docs.md, pplx-docs.md)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Runtime | 3.11 is the current stable LTS target; 3.14 works but is newer than most CI images. Slack Bolt requires 3.7+ but 3.11 gives asyncio improvements and better error messages. |
| slack_bolt | 1.27.0 | Slack app framework — event routing, ack, say, slash commands, App Home | Official Slack framework; SocketModeHandler is built-in. Handles the 3-second Slack ack deadline automatically. No alternative offers this out of the box. |
| slack_sdk | 3.41.0 | Slack Web API client — `client.chat_update`, `client.chat_postMessage` | Bundled as a dependency of slack_bolt. Used directly when you need fine-grained message control (e.g., posting the "Searching..." placeholder then updating it). |
| perplexityai | 0.30.1 | Perplexity Agent API client | Official Python SDK from Perplexity AI. Provides `client.responses.create()` with `preset="pro-search"`. The `output_text` convenience property aggregates all text content without iteration. Auto-reads `PERPLEXITY_API_KEY` from environment. |
| python-dotenv | 1.2.2 | Load `.env` file into environment variables | Standard for local dev; keeps secrets out of source. Read at startup with `load_dotenv()`. Zero setup overhead. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| slack_sdk (WebClient) | 3.41.0 (bundled) | Post and update Slack messages directly | Use `client.chat_postMessage` when you need to capture a `ts` (message timestamp) for threading or updating a placeholder message. `say()` in Bolt listeners doesn't return the `ts` needed for `chat_update`. |
| logging (stdlib) | — | Structured logging | Use Python's built-in logging module. Bolt passes a `logger` kwarg to listeners — use that, not `print()`. Set level to `INFO` in production, `DEBUG` during dev. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| venv | Dependency isolation | `python3 -m venv .venv && source .venv/bin/activate`. Standard Python practice; no third-party tooling needed for a project this size. |
| `.env` file + python-dotenv | Secret management | Store `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `PERPLEXITY_API_KEY` locally. Never commit this file. |
| Slack App config (api.slack.com) | App manifest setup | Requires enabling Socket Mode, generating `xapp` token with `connections:write` scope, and subscribing to `message.im`, `message.channels`, `message.groups`, `app_mention` events. |

## Installation

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install all dependencies
pip install slack_bolt==1.27.0 perplexityai==0.30.1 python-dotenv==1.2.2

# Pin versions for reproducibility
pip freeze > requirements.txt
```

**Minimal requirements.txt:**
```
slack-bolt==1.27.0
perplexityai==0.30.1
python-dotenv==1.2.2
```

`slack_sdk` is installed automatically as a transitive dependency of `slack_bolt`.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| slack_bolt | slack_sdk (raw WebClient only) | Only when you need raw HTTP control without event routing abstraction. Not worth it here — Bolt's decorator pattern eliminates ack boilerplate and timeout risk. |
| slack_bolt | slack-machine, errbot | If you need a multi-plugin bot platform. Overkill for a single-purpose bot; adds framework complexity with no benefit. |
| perplexityai SDK | httpx + raw HTTP to `api.perplexity.ai/v1/agent` | If you need async HTTP or the SDK doesn't support a new API feature yet. The SDK is synchronous; for async Bolt handlers you'd run it in a thread executor. |
| Socket Mode | HTTP mode (ngrok/public URL) | When deploying to a server with a stable public URL (Heroku, Fly.io, AWS Lambda). Socket Mode is correct for localhost-first development and single-workspace bots with no public endpoint requirement. |
| python-dotenv | os.environ (direct export) | CI/CD environments where secrets are injected as environment variables. `load_dotenv()` is a no-op if the variable is already set, so the same code works in both cases. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `slackclient` (legacy) | Deprecated in 2021. Uses old RTM API (not Events API). No Socket Mode support. Unmaintained. | `slack_bolt` + `slack_sdk` |
| `slack` PyPI package (not slack_bolt or slack_sdk) | Name-squatted package, not from Slack. Different from the official SDK. Confusingly named. | `slack_bolt==1.27.0` explicitly |
| `openai` SDK pointed at Perplexity | Perplexity supports `/v1/responses` as an OpenAI-compatible alias, but the native `perplexityai` SDK exposes `preset="pro-search"` and `search_results` output items that the OpenAI SDK doesn't model. | `perplexityai` SDK |
| `asyncio` / `async def` handlers in Bolt | Bolt for Python uses synchronous handlers by default. Async mode requires `AsyncApp` + `AsyncSocketModeHandler` + an ASGI runner (uvicorn). For a simple bot this doubles setup complexity for no benefit. | Synchronous handlers with `SocketModeHandler` |
| Storing tokens in source code | Obvious security risk. Slack tokens rotate when exposed. | `.env` + `python-dotenv`, never commit tokens |
| `threading` for Perplexity calls | The Perplexity SDK is synchronous and will block the Bolt listener thread during API calls. Bolt handles this correctly in sync mode — the listener runs in a thread pool. No manual threading needed. | Let Bolt manage the thread pool via `SocketModeHandler` |

## Stack Patterns by Variant

**For this project (Socket Mode, single workspace, localhost):**
- Use `SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()`
- Requires `SLACK_APP_TOKEN` (xapp-...) with `connections:write` scope
- Requires `SLACK_BOT_TOKEN` (xoxb-...) with `chat:write`, `app_mentions:read`, `im:history` scopes
- No public URL, no ngrok, no web server

**If migrating to HTTP deployment later:**
- Replace `SocketModeHandler` with `app.start(port=3000)`
- Add `signing_secret=os.environ["SLACK_SIGNING_SECRET"]` to `App()` constructor
- Deploy behind a reverse proxy or use a platform like Fly.io/Railway

**For posting the "Searching..." indicator pattern:**
```python
# Step 1: post placeholder (capture ts for later update)
result = client.chat_postMessage(
    channel=channel_id,
    thread_ts=thread_ts,   # reply in thread
    text="Searching..."
)
placeholder_ts = result["ts"]

# Step 2: call Perplexity
pplx_response = pplx_client.responses.create(preset="pro-search", input=user_query)

# Step 3: update placeholder with real answer
client.chat_update(
    channel=channel_id,
    ts=placeholder_ts,
    text=format_answer(pplx_response)
)
```
This pattern requires `chat:write` scope and uses `chat_update`, not `say()`. `say()` cannot update an existing message.

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| slack_bolt==1.27.0 | slack_sdk==3.41.0 | slack_sdk is a declared dependency of slack_bolt — installing bolt installs the compatible sdk automatically. Do not pin slack_sdk independently unless you need a specific feature. |
| slack_bolt==1.27.0 | Python 3.7–3.14 | Officially tested against 3.7+. Python 3.14.2 (current on this machine) works. |
| perplexityai==0.30.1 | Python 3.8+ | SDK requires 3.8 minimum per package metadata. Python 3.11+ recommended. |
| python-dotenv==1.2.2 | Python 3.8+ | No known conflicts with either slack_bolt or perplexityai. |

## API Configuration Notes

**Perplexity Agent API:**
- Endpoint: `POST https://api.perplexity.ai/v1/agent`
- SDK import: `from perplexity import Perplexity` (note: package is `perplexityai`, import is `perplexity`)
- The `pro-search` preset auto-selects the model, includes `web_search` + `fetch_url` tools, and returns `search_results` output items with `url`, `title`, `snippet`, and `date` fields
- `response.output_text` aggregates text; iterate `response.output` to find `type == "search_results"` items for citations
- Error types to catch: `perplexity.APIConnectionError`, `perplexity.RateLimitError`, `perplexity.APIStatusError`

**Slack Socket Mode tokens:**
- `SLACK_BOT_TOKEN`: xoxb-... (OAuth & Permissions page, "Bot User OAuth Token")
- `SLACK_APP_TOKEN`: xapp-... (Basic Information > App-Level Tokens, must have `connections:write` scope)

**Required Slack OAuth scopes for this bot:**
- `chat:write` — post and update messages
- `app_mentions:read` — receive @mention events
- `im:history` — receive DM messages
- `channels:history` — receive channel messages (for channels bot is in)
- `commands` — enable slash commands

**Required event subscriptions (Socket Mode):**
- `app_mention` — @mention in channels
- `message.im` — DM messages
- `message.channels` — channel messages (optional, only needed if listening to all channel messages vs. just @mentions)

## Sources

- PyPI live version query (verified 2026-03-13): `slack_bolt==1.27.0`, `perplexityai==0.30.1`, `slack_sdk==3.41.0`, `python-dotenv==1.2.2` — HIGH confidence
- `slack-bolt-docs.md` (local reference from docs.slack.dev): SocketModeHandler pattern, token types, event subscriptions, message listener API — HIGH confidence
- `pplx-docs.md` (local reference from docs.perplexity.ai): Agent API endpoint, `perplexityai` SDK, `pro-search` preset, `output_text` convenience property, `search_results` output structure, error types — HIGH confidence
- `PROJECT.md`: Confirmed constraints (Socket Mode, Python, Perplexity Python SDK, `pro-search` preset, no conversation history) — HIGH confidence

---
*Stack research for: Python Slack bot + Perplexity Agent API (Socket Mode)*
*Researched: 2026-03-13*
