# Pitfalls Research

**Domain:** Slack bot with external LLM API integration (Slack Bolt for Python + Perplexity Agent API)
**Researched:** 2026-03-13
**Confidence:** HIGH (drawn from official Slack Bolt docs, Perplexity Agent API docs, and known Slack platform behavior)

---

## Critical Pitfalls

### Pitfall 1: Missing the 3-Second Acknowledgment Deadline

**What goes wrong:**
Slack requires every event, action, or slash command to be acknowledged within 3 seconds or it retries delivery — sending the same event again. When the Perplexity API call is made synchronously inside the handler before `ack()`, the handler routinely blows past the deadline. Slack retries, the bot fires the Perplexity call again, and the user gets duplicate "Searching..." messages and duplicate answers in the thread.

**Why it happens:**
Developers new to Bolt assume the handler is like a normal HTTP request handler where you do work and then respond. The 3-second deadline is easy to miss in local testing because Perplexity sometimes responds fast — but it fails under any real latency (busy model, long search query, network hiccup).

**How to avoid:**
Call `ack()` immediately as the first line of every handler. Then do the Perplexity call in a separate thread or async task. Bolt's `say()` method can be called after the fact — it uses the bot token, not the ack channel. For slash commands, ack with an empty body, then post a follow-up message via the client.

```python
@app.command("/ask")
def handle_ask(ack, say, command, client):
    ack()  # Must be first — within 3 seconds
    # Now do the slow work
    client.chat_postMessage(channel=command["channel_id"], text="Searching...")
    response = perplexity_client.responses.create(...)
```

**Warning signs:**
- User sees the bot respond twice to the same question
- Slack console shows event delivery retries
- Bot works fine for short queries but fails or duplicates on longer ones

**Phase to address:** Core bot implementation (the first phase that wires up event handlers)

---

### Pitfall 2: Bot Responding to Its Own Messages (Infinite Loop)

**What goes wrong:**
The bot listens for `message` events (including DMs) and posts a reply. That reply also fires a `message` event. If the bot does not filter out its own messages, it answers its own answers — an infinite loop that drains API credits and spams the thread.

**Why it happens:**
The `message.im` event fires for all messages in a DM, including messages the bot itself sends. Developers subscribe to the event and forget to check `message['bot_id']` or `message.get('subtype')`.

**How to avoid:**
Filter bot messages at the top of every message handler. Bolt's `app.message()` does not filter bot messages automatically for all event types. Explicitly check:

```python
@app.event("message")
def handle_dm(event, say):
    # Ignore bot messages and message subtypes (edits, deletes, etc.)
    if event.get("bot_id") or event.get("subtype"):
        return
    # Safe to proceed
```

**Warning signs:**
- Thread fills up rapidly with bot messages after one user message
- API usage spikes unexpectedly
- Bot token rate limit errors appear in logs

**Phase to address:** Core bot implementation (DM and mention handlers)

---

### Pitfall 3: Blocking the Bolt Event Loop with Synchronous Perplexity Calls

**What goes wrong:**
Bolt for Python runs event handlers synchronously by default. A Perplexity `pro-search` call can take 10–30+ seconds (especially with web search and URL fetch tool calls). During this time, the Bolt process cannot handle any other incoming Slack events. In a busy workspace, events queue up or time out.

**Why it happens:**
The default Bolt setup is synchronous. The `pro-search` preset uses web_search and fetch_url tools, which involve multiple round trips. Developers test with simple questions (fast responses) and don't discover the blocking problem until the bot is in real use.

**How to avoid:**
Use Python's `threading` module or `concurrent.futures` to run the Perplexity call in a background thread. Bolt's listeners are thread-safe — `say()` and `client` can be called from any thread.

```python
import threading

@app.event("app_mention")
def handle_mention(event, say, ack):
    ack()
    thread = threading.Thread(target=call_perplexity_and_reply, args=(event, say))
    thread.start()
```

**Warning signs:**
- Bot stops responding during high traffic periods
- Multiple users asking simultaneously causes timeouts
- Single Perplexity call locks up the entire bot process

**Phase to address:** Core bot implementation — must be addressed before any multi-user testing

---

### Pitfall 4: Incorrect Thread Targeting for Replies

**What goes wrong:**
The bot posts top-level messages instead of threaded replies, or posts a reply to the wrong thread. In channels with many users, top-level bot replies create noise. Worse, if the `thread_ts` is taken from the wrong field, the reply appears in an unrelated thread.

**Why it happens:**
Slack events use different fields for different contexts:
- In a DM: `event['ts']` is the timestamp of the message — use this as `thread_ts` to reply in a thread
- In a channel mention: `event['ts']` is the mention's timestamp; if the mention is already in a thread, `event['thread_ts']` contains the parent thread's ts
- Slash commands have no thread context at all — you must decide where to post

Developers use `event['ts']` everywhere and get inconsistent threading behavior.

**How to avoid:**
Use `event.get('thread_ts') or event['ts']` to respect existing thread context. For slash commands, post to the channel without threading (or instruct users to use `/ask` in a thread they create).

```python
thread_ts = event.get("thread_ts") or event["ts"]
say(text="Searching...", thread_ts=thread_ts)
```

**Warning signs:**
- Bot replies appear as top-level messages in channels
- Reply appears in wrong thread when user asks from within an existing thread
- DM replies appear as new DM messages, not threads

**Phase to address:** Core bot implementation (reply logic)

---

### Pitfall 5: Not Handling the `search_results` Output Type in the Perplexity Response

**What goes wrong:**
The Perplexity `pro-search` response `output` field is an array with multiple items of different types: `search_results`, `fetch_url_results`, and `message`. Developers who iterate `output` looking for the text or who access `output[0].text` directly get a `KeyError` or miss the actual answer because the message item is not first in the array.

**Why it happens:**
The docs show `response.output_text` as a convenience shortcut, but developers building citation display need to manually walk `response.output` to find search result URLs. This is easy to get wrong — the output array order is not guaranteed and types vary per request.

**How to avoid:**
Use `response.output_text` for the answer text. Walk `response.output` by type to extract citations:

```python
answer = response.output_text  # Always use this for the text

citations = []
for item in response.output:
    if item.type == "search_results":
        for result in item.results:
            citations.append({"title": result.title, "url": result.url})
```

**Warning signs:**
- `AttributeError: 'SearchResultsOutputItem' has no attribute 'text'`
- Bot posts answers without citations despite `pro-search` returning search results
- Citation URLs are empty or missing from bot replies

**Phase to address:** Core bot implementation (Perplexity response parsing)

---

### Pitfall 6: Perplexity API Latency Causing Silent Failures in Slash Commands

**What goes wrong:**
Slash commands have a 3-second acknowledgment window and Slack's interface shows a "loading" spinner while waiting. If the bot acks with a response body (not just `ack()`), Slack shows that response immediately. But if the actual Perplexity answer isn't ready and the bot tries to use Slack's `respond()` hook after the response window closes, the message silently fails to appear.

**Why it happens:**
Slash command `respond()` uses the response_url which expires after 30 minutes but can fail if the connection is dropped. Developers mix up `say()` (uses bot token, always works) with `respond()` (uses response_url, can expire or fail).

**How to avoid:**
For slash commands: `ack()` immediately with no content. Then use `client.chat_postMessage()` or `say()` to post the result asynchronously. Do not rely on `respond()` for long-running operations.

```python
@app.command("/ask")
def handle_ask(ack, say, command):
    ack()
    # Post "Searching..." to give immediate feedback
    say(text="Searching...", channel=command["channel_id"])
    # Do the work, then update or post the final answer
```

**Warning signs:**
- Slash command shows spinner but result never appears
- Users report command "doesn't work" but logs show successful Perplexity responses
- `respond()` calls return errors in logs after successful API calls

**Phase to address:** Slash command implementation

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode `pro-search` preset with no error fallback | Simple code path | If Perplexity changes preset behavior or it's unavailable, bot silently fails or throws unhandled exception | Never — always wrap in try/except with user-friendly error |
| Store bot token as plain string in code | Easy dev setup | Credential exposure in git history | Never — use environment variables or secrets manager |
| No deduplication of event retries | Simpler logic | Slack retries on ack timeout → duplicate API calls and duplicate bot messages | Never in production |
| Single-threaded synchronous handler | Less code | Bot freezes under concurrent load | Only for personal single-user workspace |
| No "Searching..." indicator before Perplexity call | One fewer API call | Users wait 10-30s with no feedback and think bot is broken | Never — always show loading state |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Slack Socket Mode | Using `SLACK_SIGNING_SECRET` (HTTP mode) instead of `SLACK_APP_TOKEN` (xapp) for Socket Mode | Socket Mode requires `SLACK_APP_TOKEN` (xapp-prefixed) and `SLACK_BOT_TOKEN` (xoxb-prefixed); signing secret not needed |
| Perplexity Agent API | Passing `model` and `preset` together in the same request | Use either `preset="pro-search"` OR `model="..."`, not both — they are mutually exclusive configuration modes |
| Perplexity response output | Calling `response.output[0].text` to get the answer | Use `response.output_text` (convenience property); the output array has multiple types and the message is not always first |
| Slack `say()` in DMs | `say()` without `thread_ts` in a DM creates a new DM message instead of threading | Always compute `thread_ts = event.get("thread_ts") or event["ts"]` before calling `say()` |
| Perplexity `APIConnectionError` | No error handling → uncaught exception crashes the handler | Wrap all Perplexity calls in try/except for `APIConnectionError`, `RateLimitError`, `APIStatusError` and post the user-friendly error message |
| Slack `app_mention` event | Bot processes `app_mention` in a thread where user @mentioned it, but posts reply to wrong level | Extract `thread_ts` from event correctly; see Pitfall 4 |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous Perplexity call in Bolt handler | All events queue behind one slow API call | Run Perplexity call in a background thread | First time 2+ users ask simultaneously |
| Posting "Searching..." then editing the message | Requires `chat:write` + `chat:update` scopes and message ts tracking | Post "Searching..." then post the final answer as a new message; simpler and requires fewer scopes | When scope or ts tracking is wrong; editing fails silently |
| No timeout on Perplexity calls | Pro-search with fetch_url can take 60+ seconds; bot process hangs | Set SDK-level timeout; post error if threshold exceeded | Whenever Perplexity is slow or a fetched URL is unresponsive |
| Re-creating Perplexity client per request | Small overhead per call | Instantiate `Perplexity()` once at module level | Only noticeable at high volume, but bad habit |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Hardcoding `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, or `PERPLEXITY_API_KEY` in source code | Credentials exposed in git history; anyone with repo access can impersonate the bot or exhaust API credits | Load all secrets exclusively from environment variables; add `.env` to `.gitignore` |
| Not verifying event source (HTTP mode only) | Fake events from bad actors trigger Perplexity API calls and bot replies | Socket Mode handles verification automatically; if ever switching to HTTP mode, `signing_secret` becomes mandatory |
| Logging full Slack event payloads at INFO level | User message content written to logs; privacy risk, potentially GDPR-relevant | Log only event type and ts at INFO; log full payload at DEBUG only |
| No rate limiting on Perplexity calls | One user spamming the bot drains API budget in minutes | Track calls per user per time window (even a simple in-memory dict) or rely on Perplexity's own rate limiting as a backstop |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No loading indicator before Perplexity response | User waits 10–30s with no feedback; assumes bot is broken; asks again (causing duplicate processing) | Post "Searching..." message immediately after ack, before Perplexity call |
| Raw markdown from Perplexity response rendered as plain text in Slack | Numbered lists, bold text, headers appear as asterisks and hashes; hard to read | Use Slack's mrkdwn format; convert or strip markdown headings (Slack doesn't support `#` headings in messages) |
| Citation URLs dumped as raw text | Long URLs clutter the reply; hard to distinguish answer from sources | Format citations as numbered list with Slack link syntax: `<URL|Title>` |
| Generic "something went wrong" error | User doesn't know who to contact or whether to retry | Use the specified error message: "Uh oh, it seems my brain is offline — talk to @Robert Li about trying to kick start it" |
| Bot replies to every message in a DM including its own | Infinite loop, spam | Filter `bot_id` and `subtype` at the start of every message handler |

---

## "Looks Done But Isn't" Checklist

- [ ] **Event deduplication:** Verify bot does NOT process Slack's retry events (events sent again because ack timed out). Check by deliberately delaying ack and confirming only one response appears.
- [ ] **Own-message filter:** Confirm bot ignores its own messages in DMs. Test by having bot post a message and verify it does not trigger another Perplexity call.
- [ ] **Thread continuity:** Verify that when user asks a question in an existing thread, bot replies in that same thread (not top-level).
- [ ] **Error message:** Confirm the specific error message copy appears when Perplexity is unreachable, not a stack trace or generic Python exception message.
- [ ] **Citation formatting:** Verify citations render as clickable links in Slack, not raw URLs.
- [ ] **Slash command in threads:** Test `/ask` from inside an existing thread — confirm bot posts to channel (or handles gracefully) without crashing.
- [ ] **Concurrent users:** Test two users asking simultaneously — confirm both get answers and the bot does not freeze.
- [ ] **Missing scopes:** Verify `chat:write` is in Bot Token Scopes; app will fail silently or with cryptic `missing_scope` error if not present.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Bot responding to its own messages (loop) | LOW | Add `bot_id` check to handler; restart bot process |
| Credentials exposed in git | HIGH | Rotate all three tokens (SLACK_BOT_TOKEN, SLACK_APP_TOKEN, PERPLEXITY_API_KEY) immediately; purge from git history with `git filter-branch` or BFG; audit access logs |
| Duplicate responses from retry storm | LOW | Add ack() as first line; deduplication by event ts if needed; existing duplicated messages cannot be recalled without `chat:delete` scope |
| Bot frozen due to synchronous blocking | MEDIUM | Restart process immediately; then refactor handlers to use threading before re-deploying |
| Wrong thread targets | LOW | Fix `thread_ts` logic; existing mis-threaded messages stay where they are |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 3-second ack deadline | Core event handler implementation | Delay handler artificially by 5s; confirm no duplicate responses |
| Bot responds to own messages | Core event handler implementation | Bot sends a message; confirm no second Perplexity call fires |
| Blocking event loop | Core event handler implementation | Two concurrent `/ask` calls; confirm both resolve without hanging |
| Wrong thread targeting | Reply logic implementation | Ask from channel, from DM, from inside existing thread; verify each reply lands in the correct thread |
| Perplexity output type mismatch | Perplexity integration implementation | Log raw `response.output` array; confirm citations extracted correctly |
| Slash command silent failure | Slash command implementation | Run `/ask` with a slow query; confirm answer appears |
| Missing scopes | App manifest / Slack app configuration | Attempt each interaction type; confirm no `missing_scope` errors |
| Secrets in code | Project setup / before first commit | `git log --all -S "xoxb"` confirms no token in history |

---

## Sources

- Slack Bolt for Python official docs: https://docs.slack.dev/tools/bolt-python/getting-started
- Slack Bolt for Python AI chatbot tutorial: https://docs.slack.dev/tools/bolt-python/tutorial/ai-chatbot
- Slack token types reference: https://docs.slack.dev/authentication/tokens
- Slack event subscriptions guide: https://docs.slack.dev/apis/events-api/
- Perplexity Agent API docs: https://docs.perplexity.ai
- Perplexity output control (streaming, structured outputs): https://docs.perplexity.ai/docs/agent-api/output-control
- Perplexity tools reference (web_search, fetch_url): https://docs.perplexity.ai/docs/agent-api/tools
- Perplexity models and presets: https://docs.perplexity.ai/docs/agent-api/models
- PROJECT.md context: .planning/PROJECT.md

---
*Pitfalls research for: Slack bot + Perplexity Agent API integration*
*Researched: 2026-03-13*
