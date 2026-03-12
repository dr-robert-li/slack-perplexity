"""Formatting utilities — citation formatter and message splitter for Slack."""
import re


def markdown_to_slack(text: str) -> str:
    """Convert common Markdown patterns to Slack mrkdwn format.

    Handles: bold, italic, headings, inline code, code blocks,
    links, horizontal rules, and list markers.
    """
    # Preserve code blocks (``` ... ```) — don't transform inside them
    code_blocks: list[str] = []

    def _stash_code_block(match):
        code_blocks.append(match.group(0))
        return f"\x00CODEBLOCK{len(code_blocks) - 1}\x00"

    text = re.sub(r"```[\s\S]*?```", _stash_code_block, text)

    # Preserve inline code (` ... `)
    inline_codes: list[str] = []

    def _stash_inline_code(match):
        inline_codes.append(match.group(0))
        return f"\x00INLINE{len(inline_codes) - 1}\x00"

    text = re.sub(r"`[^`]+`", _stash_inline_code, text)

    # Headings → bold text (Slack has no heading support)
    text = re.sub(r"^#{1,6}\s+(.+)$", r"*\1*", text, flags=re.MULTILINE)

    # Bold+italic ***text*** or ___text___ → Slack bold *text*
    text = re.sub(r"\*{3}(.+?)\*{3}", r"*\1*", text)
    text = re.sub(r"_{3}(.+?)_{3}", r"*\1*", text)

    # Bold **text** → *text* (Slack uses single asterisks for bold)
    text = re.sub(r"\*{2}(.+?)\*{2}", r"*\1*", text)

    # Italic _text_ stays as _text_ (same in Slack)
    # No transformation needed

    # Markdown links [text](url) → Slack <url|text>
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<\2|\1>", text)

    # Horizontal rules (---, ***, ___) → Slack divider
    text = re.sub(r"^[\-\*_]{3,}\s*$", "───", text, flags=re.MULTILINE)

    # Numbered reference-style citations [1], [2] etc. — leave as-is

    # Restore inline code
    for i, code in enumerate(inline_codes):
        text = text.replace(f"\x00INLINE{i}\x00", code)

    # Restore code blocks
    for i, block in enumerate(code_blocks):
        text = text.replace(f"\x00CODEBLOCK{i}\x00", block)

    # Strip inline Perplexity references like [web:1], [web:3][web:6], etc.
    text = re.sub(r"(\[web:\d+\])+", "", text)

    # Clean up excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def format_answer(answer: str, citations: list[dict]) -> str:
    """Format a Perplexity answer with Slack mrkdwn citation footnotes.

    Converts Markdown to Slack mrkdwn and appends clickable source links.
    """
    slack_answer = markdown_to_slack(answer)

    # Safety net: cap at 5 even if caller passes more
    limited_citations = citations[:5]

    if not limited_citations:
        return f"{slack_answer}\n\n_No web sources found for this query_"

    lines = [f"{slack_answer}\n───"]
    for i, citation in enumerate(limited_citations, start=1):
        lines.append(f"[{i}] <{citation['url']}|{citation['title']}>")

    return "\n".join(lines)


def split_message(text: str, limit: int = 3800) -> list[str]:
    """Split a long message into chunks that fit within Slack's character limit.

    Args:
        text: The message text to split.
        limit: Maximum characters per chunk (default 3800, well under Slack's 4000).

    Returns:
        List of string chunks. Always contains at least one element.
    """
    if len(text) <= limit:
        return [text]

    chunks = []
    while text:
        chunks.append(text[:limit])
        text = text[limit:]

    return chunks
