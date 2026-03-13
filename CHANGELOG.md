# Changelog

All notable changes to this project will be documented in this file.

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
