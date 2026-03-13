"""Slash command handler for /ask command."""
from handlers.shared import _handle_question


def ack_ask(ack) -> None:
    """Acknowledge the /ask command unconditionally.

    Per Bolt's ack/lazy pattern the ack function must respond within 3 seconds.
    Empty-text handling is deferred to the lazy run_ask function.
    """
    ack()


def run_ask(client, body: dict, respond) -> None:
    """Lazy handler: validate text and invoke the shared question pipeline.

    If no text is provided, send an ephemeral usage hint back to the user.
    Otherwise call _handle_question with thread_ts=None so the answer is
    posted as a top-level message (with overflow chunks threaded off it).
    """
    text = (body.get("text") or "").strip()
    if not text:
        respond(
            text="Usage: /ask <your question>",
            response_type="ephemeral",
        )
        return

    _handle_question(
        client,
        channel=body["channel_id"],
        thread_ts=None,
        user_id=body["user_id"],
        user_text=text,
    )


def register_slash_handler(app) -> None:
    """Register /ask command with the Bolt app using ack/lazy pattern."""
    app.command("/ask")(ack=ack_ask, lazy=[run_ask])
