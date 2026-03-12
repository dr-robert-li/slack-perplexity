# Phase 1: Core Pipeline - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Project setup, Perplexity service layer, and DM handler with full reliability and response quality. Users can DM the bot a question and receive a cited, threaded answer — with a loading indicator, graceful error handling, and zero infinite-loop risk. Runs via Socket Mode.

</domain>

<decisions>
## Implementation Decisions

### Citation formatting
- Footnotes at bottom: answer text with [1][2] markers inline, then a numbered sources list below a `---` divider
- Each source shown as a linked title only (e.g. `[IBM Quantum Computing](https://ibm.com/quantum)`)
- Maximum 5 sources — show only the most relevant
- If Perplexity returns no search results, show the answer with a disclaimer: "No web sources found for this query"

### Bot personality & tone
- Bot name in Slack: "Kahm-pew-terr" (phonetic spelling of "Computer")
- No custom system instructions — let Perplexity's `pro-search` preset respond naturally
- Answer length: adaptive — short for simple questions, longer for complex ones
- First-time DM greeting: brief intro on first message, then just answers after that

### Error scenarios
- All API errors (rate limits, connection failures, timeouts) use the same friendly message: "Uh oh, it seems my brain is offline — talk to @Robert Li about trying to kick start it"
- Empty/nonsensical messages: pass to Perplexity anyway — let the API handle it
- Long responses exceeding Slack's block limit: split into multiple messages in the thread

### Loading experience
- Loading indicator text: "Searching..."
- Edit in place: update the "Searching..." message with the full answer (single message, no delete-and-repost)
- After 60 seconds without a response: update loading message to "Taking longer than expected, still working on it..."
- No hard timeout — let Perplexity finish

### Claude's Discretion
- Exact first-time greeting wording
- How to detect "first-time" DM (simple approach is fine — no persistent storage needed)
- Loading message formatting (plain text vs block kit)
- How to handle the 60s timer implementation

</decisions>

<specifics>
## Specific Ideas

- Bot name "Kahm-pew-terr" is a deliberate phonetic joke — preserve the exact spelling
- The offline error message must mention @Robert Li by name — this is non-negotiable
- Citations should look clean: linked titles only, no raw URLs cluttering the message

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no existing code

### Established Patterns
- None — first phase establishes all patterns

### Integration Points
- Environment variables: `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `PERPLEXITY_API_KEY`
- Perplexity SDK: `from perplexity import Perplexity` → `client.responses.create(preset="pro-search", input=...)`
- Slack Bolt: `App(token=...)` + `SocketModeHandler(app, token)`
- Response parsing: `response.output_text` for answer, iterate `response.output` for `type == "search_results"` items

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-core-pipeline*
*Context gathered: 2026-03-13*
