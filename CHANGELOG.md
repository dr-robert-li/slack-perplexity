# Changelog

All notable changes to this project will be documented in this file.

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
