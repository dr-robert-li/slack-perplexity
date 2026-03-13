"""Slash command handler for /ask command."""
from handlers.shared import (
    ERROR_MSG,
    GREETING,
    greeted_users,
    query_perplexity,
    format_answer,
    split_message,
)


def ack_ask(ack) -> None:
    """Acknowledge the /ask command unconditionally.

    Per Bolt's ack/lazy pattern the ack function must respond within 3 seconds.
    Empty-text handling is deferred to the lazy run_ask function.
    """
    ack()


def run_ask(body: dict, respond) -> None:
    """Lazy handler: validate text and call Perplexity via respond().

    Uses respond() instead of chat.postMessage so the slash command works in
    any channel — even ones the bot hasn't joined. respond() posts via the
    response_url which doesn't require channel membership.
    """
    text = (body.get("text") or "").strip()
    if not text:
        respond(
            text="Usage: /ask <your question>",
            response_type="ephemeral",
        )
        return

    user_id = body["user_id"]

    respond(text="Searching...", response_type="in_channel")

    try:
        result = query_perplexity(text)
        formatted = format_answer(result["answer"], result["citations"])

        if user_id not in greeted_users:
            greeted_users.add(user_id)
            full_text = GREETING + formatted
        else:
            full_text = formatted

        chunks = split_message(full_text)

        respond(text=chunks[0], response_type="in_channel", replace_original=True)

        for chunk in chunks[1:]:
            respond(text=chunk, response_type="in_channel")

    except Exception:
        respond(text=ERROR_MSG, response_type="in_channel", replace_original=True)


def register_slash_handler(app) -> None:
    """Register /ask command with the Bolt app using ack/lazy pattern."""
    app.command("/ask")(ack=ack_ask, lazy=[run_ask])
