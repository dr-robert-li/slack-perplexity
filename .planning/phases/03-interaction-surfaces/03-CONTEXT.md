# Phase 3: Interaction Surfaces - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Add three new interaction surfaces to the bot: `/ask` slash command, group DM support, and App Home tab. All use the existing `_handle_question()` pipeline from Phase 1. No changes to Perplexity service or formatting.

</domain>

<decisions>
## Implementation Decisions

### Slash command (/ask)
- Visible threaded reply in the channel (not ephemeral) — consistent with @mention behavior
- Empty `/ask` (no question text) returns ephemeral help text: "Usage: /ask <your question>"
- Slash command requires creating the command in Slack API dashboard and a new `app.command("/ask")` handler
- Must ack() within 3 seconds, then use `respond()` or `client.chat_postMessage` for the answer

### Group DM handling
- Bot responds only to @mentions in group DMs, not all messages
- Prevents noise in multi-person conversations
- Uses `message.mpim` event with `channel_type == "mpim"` guard
- Same `_handle_question()` pipeline after stripping @mention tag

### App Home tab
- Static info page — no dynamic content or recent queries
- Shows: bot description, usage instructions for all 4 methods (DM, @mention, /ask, group DM), and contact link to @Robert Li
- Uses `views.publish` API with Block Kit layout
- Replace existing no-op `app_home_opened` handler

### Handler organization
- Split into separate files by trigger type:
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

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_handle_question()` in `handlers/dm_handler.py`: Shared pipeline (loading indicator, Perplexity query, formatting, error handling) — reuse for all new surfaces
- `MENTION_RE` regex: Strips `<@UID>` tags — reuse for group DM @mention parsing
- `GREETING`, `ERROR_MSG` constants: Reuse across all handlers
- `greeted_users` set: First-time greeting detection — works across all surfaces

### Established Patterns
- Lazy listener pattern: `app.event("message")(ack=fn, lazy=[fn])` for message events
- Direct handler: `app.event("app_mention")(handler_fn)` for non-lazy events
- Guards: bot_id, subtype, channel_type checks at handler entry

### Integration Points
- `app.py` line 17: `register_dm_handler(app)` — replace with per-file registration calls
- `app.py` line 22: `app_home_opened` no-op — replace with real handler
- `app.py` line 14: `app = App(...)` — slash command needs this app instance
- Slack API dashboard: Must create `/ask` command definition

</code_context>

<specifics>
## Specific Ideas

- /ask slash command should feel identical to @mention — same response format, same citations, same threading
- App Home tab should be simple and helpful — not a dashboard, just "here's how to use me"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-interaction-surfaces*
*Context gathered: 2026-03-13*
