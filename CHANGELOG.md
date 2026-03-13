# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2026-03-13

### Added

- Conversation context — follow-up questions in threads are answered with awareness of prior messages
- UID resolution — `<@UID>` mention tags are resolved to human-readable display names before querying Perplexity
- Channel context — @mentions in channels include recent channel messages as context
- Thread history fetching — DMs, group DMs, and mentions in threads fetch prior thread messages
- Configurable context depth via `HISTORY_DEPTH` (default 10) and `MSG_TRUNCATE_LENGTH` (default 500) env vars
- `services/context.py` — UID resolver with in-memory cache, thread and channel history fetchers
- Structured multi-turn message support in Perplexity service — `query_perplexity` accepts optional `messages` list
- Bot user ID caching in `handlers/shared.py` via `get_bot_user_id()` to filter bot's own messages from history
- 44 new tests (94 total) covering context assembly, UID resolution, handler wiring, and structured message passing

### Changed

- `_handle_question` in `handlers/shared.py` now accepts `messages=` parameter and resolves UIDs centrally
- `handlers/message_handler.py` and `handlers/mention_handler.py` fetch thread or channel history before answering
- `/ask` slash command intentionally unchanged — remains standalone with no conversation context

## [0.3.0] - 2026-03-13

### Added

- `/ask` slash command — run `/ask <question>` from any channel for a visible threaded reply
- Group DM support — @mention the bot in a group DM to get a cited answer
- App Home tab — bot description, usage instructions for all interaction methods, and admin contact
- `ADMIN_UID` env var — configurable admin contact shown in error messages and App Home

### Changed

- Refactored monolithic `dm_handler.py` into `shared.py`, `message_handler.py`, `mention_handler.py`, `slash_handler.py`, and `home_handler.py`
- Error messages now reference `ADMIN_UID` from env instead of a hardcoded name
- Test suite expanded from 21 to 50 tests

## [0.2.0] - 2026-03-13

### Added

- @mention support — use the bot in any channel via `@Kahm-pew-terr`
- Markdown-to-Slack formatting (bold, headings, links, code blocks, dividers)
- Strip Perplexity inline references (`[web:N]`) — citations shown at bottom only

### Changed

- Refactored handler into shared `_handle_question()` for DMs and mentions
- "No web sources" disclaimer now renders in italic

## [0.1.0] - 2026-03-13

### Added

- Perplexity AI service layer with pro-search and citation extraction
- DM message handler with lazy listener pattern for immediate ack
- "Searching..." loading indicator that updates in-place with the answer
- Citation formatting with clickable Slack mrkdwn links
- Message splitting for responses exceeding Slack's character limit
- First-time greeting for new users
- 60-second slow-response fallback message
- Error handling with user-friendly error message
- Test suite with 21 tests and shared fixtures
