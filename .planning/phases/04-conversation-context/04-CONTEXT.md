# Phase 4: Conversation Context - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

The bot reads prior thread or channel messages before querying Perplexity, enabling follow-up questions without repeating context. Raw Slack `<@UID>` tags are resolved to human-readable display names. History depth is configurable via environment variables.

</domain>

<decisions>
## Implementation Decisions

### Channel context trigger
- All non-threaded interactions include recent channel history: @mentions, group DM @mentions
- DMs (1:1 with bot) also include prior DM history for follow-up support
- `/ask` slash command does NOT include channel context (bot may not be in the channel; /ask is a quick standalone query)
- Thread replies always include thread history (the primary use case)

### Context formatting
- Structured message array format: `[{role: "user", content: "..."}, {role: "assistant", content: "..."}]`
- Bot messages map to `assistant` role, all human messages map to `user` role
- Bot's own messages are included in history (enables "elaborate on point 3" follow-ups)
- Long messages truncated to ~500 chars (configurable via `MSG_TRUNCATE_LENGTH` env var)
- No timestamps in context — name + text only
- If history is empty (first message), skip the context entirely — behaves like today

### UID resolution
- Resolve `<@UID>` to display names everywhere: current question AND all fetched history messages
- Output format: plain display name (e.g., "Robert Li"), not "@Robert Li"
- In-memory cache for UID-to-name lookups (dict, persists for bot lifetime)
- Fallback on lookup failure: keep raw UID as-is

### Configuration
- `HISTORY_DEPTH=10` env var in `.env` — single setting for both thread and channel history
- `MSG_TRUNCATE_LENGTH=500` env var in `.env` — per-message truncation limit
- Consistent with existing env var pattern (SLACK_BOT_TOKEN, PERPLEXITY_API_KEY, ADMIN_UID)
- Change requires bot restart (acceptable for single-workspace deployment)

### Claude's Discretion
- Exact Perplexity API integration for structured messages (may need to adapt based on what the API supports)
- How to structure the `query_perplexity()` signature change (list of messages vs separate context param)
- Error handling when `conversations.replies` or `conversations.history` API calls fail
- Whether to use `users.info` or `users.list` for UID resolution

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_handle_question()` in `handlers/shared.py`: Entry point for all surfaces — needs context param added
- `query_perplexity(question: str)` in `services/perplexity.py`: Currently takes single string — needs structured messages support
- `MENTION_RE` regex in `handlers/shared.py`: Already matches `<@UID>` patterns — extend for resolution
- `greeted_users` set pattern: Example of in-memory caching for the UID cache

### Established Patterns
- Lazy listener pattern: Context fetching must stay within the lazy handler (not the ack)
- All handlers call `_handle_question()` — context assembly should happen before this call
- Env vars loaded via `python-dotenv` in `app.py` — add new vars there

### Integration Points
- `handlers/shared.py` line 38: `_handle_question()` signature — add context parameter
- `services/perplexity.py` line 25: `pplx_client.responses.create(input=question)` — change input format
- `handlers/message_handler.py`: DM and mpim handlers — add history fetch before `_handle_question()`
- `handlers/mention_handler.py`: @mention handler — add channel history fetch
- `handlers/slash_handler.py`: Skip context (uses respond(), no channel access)
- Slack API: `conversations.replies` for thread history, `conversations.history` for channel history, `users.info` for UID resolution

</code_context>

<specifics>
## Specific Ideas

- Follow-up questions like "What about in Python?" should just work without the user restating the original question
- The structured message format should feel natural to Perplexity — like a multi-turn conversation
- UID resolution should be invisible to the user — they never see raw UIDs in bot behavior

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-conversation-context*
*Context gathered: 2026-03-13*
