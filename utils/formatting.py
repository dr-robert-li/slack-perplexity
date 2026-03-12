"""Formatting utilities — citation formatter and message splitter for Slack."""


def format_answer(answer: str, citations: list[dict]) -> str:
    """Format a Perplexity answer with Slack mrkdwn citation footnotes.

    Args:
        answer: The answer text from query_perplexity.
        citations: List of {title, url} dicts from query_perplexity (max 5 enforced).

    Returns:
        Formatted string ready to post to Slack. If citations exist, appends a
        `---` divider followed by numbered sources in `<url|title>` mrkdwn syntax.
        If no citations, appends a "No web sources" disclaimer.
    """
    # Safety net: cap at 5 even if caller passes more
    limited_citations = citations[:5]

    if not limited_citations:
        return f"{answer}\n\nNo web sources found for this query"

    lines = [f"{answer}\n---"]
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
