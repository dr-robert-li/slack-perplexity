"""Message handler — DM (im) and group DM (mpim) message event handlers."""
from handlers.shared import _handle_question, MENTION_RE, greeted_users, get_bot_user_id
from services.context import fetch_thread_history, fetch_channel_history


def ack_message(ack, event):
    """Acknowledge message events for DM (im) and group DM (mpim) channels.

    For mpim, also requires that the message @mentions the bot.
    """
    if event.get("bot_id"):
        return
    if event.get("subtype"):
        return
    channel_type = event.get("channel_type")
    if channel_type == "im":
        ack()
    elif channel_type == "mpim" and MENTION_RE.search(event.get("text", "")):
        ack()


def handle_dm(client, event: dict) -> None:
    """Lazy listener: process a DM, call Perplexity, reply with cited answer."""
    if event.get("bot_id"):
        return
    if event.get("subtype"):
        return
    if event.get("channel_type") != "im":
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
        user_text=event.get("text", ""),
        messages=messages,
    )


def handle_mpim(client, event: dict) -> None:
    """Lazy listener: handle @mentions in group DMs (mpim), strip mention, answer."""
    if event.get("bot_id"):
        return
    if event.get("subtype"):
        return
    if event.get("channel_type") != "mpim":
        return

    raw_text = event.get("text", "")
    if not MENTION_RE.search(raw_text):
        return

    user_text = MENTION_RE.sub("", raw_text).strip()

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


def register_message_handlers(app) -> None:
    """Register DM and group DM handlers on the given Bolt app.

    Both handle_dm and handle_mpim are registered as lazy listeners on the 'message'
    event. Each function guards on channel_type so only one fires per event.
    """
    app.event("message")(ack=ack_message, lazy=[handle_dm, handle_mpim])
