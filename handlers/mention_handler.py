"""Mention handler — @mention event handler for channel mentions."""
from handlers.shared import _handle_question, MENTION_RE


def handle_mention(event, client) -> None:
    """Handle @mentions in channels — strip the mention tag, then answer."""
    raw_text = event.get("text", "")
    user_text = MENTION_RE.sub("", raw_text).strip()

    if not user_text:
        return

    _handle_question(
        client,
        channel=event["channel"],
        thread_ts=event["ts"],
        user_id=event.get("user", ""),
        user_text=user_text,
    )


def register_mention_handler(app) -> None:
    """Register the @mention handler on the given Bolt app."""
    app.event("app_mention")(handle_mention)
