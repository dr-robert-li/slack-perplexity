"""Mention handler — @mention event handler for channel mentions."""
from handlers.shared import _handle_question, MENTION_RE, get_bot_user_id
from services.context import fetch_thread_history, fetch_channel_history


def handle_mention(event, client) -> None:
    """Handle @mentions in channels — strip the mention tag, fetch context, then answer."""
    raw_text = event.get("text", "")
    user_text = MENTION_RE.sub("", raw_text).strip()

    if not user_text:
        return

    bot_user_id = get_bot_user_id(client)
    channel = event["channel"]

    if event.get("thread_ts"):
        messages = fetch_thread_history(client, channel, event["thread_ts"], event["ts"], bot_user_id)
    else:
        messages = fetch_channel_history(client, channel, bot_user_id)

    _handle_question(
        client,
        channel=channel,
        thread_ts=event["ts"],
        user_id=event.get("user", ""),
        user_text=user_text,
        messages=messages,
    )


def register_mention_handler(app) -> None:
    """Register the @mention handler on the given Bolt app."""
    app.event("app_mention")(handle_mention)
