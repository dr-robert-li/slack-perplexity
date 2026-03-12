"""Message handler — full pipeline from Slack message to cited Perplexity answer.

Supports both DMs and @mentions in channels.
"""
import re
import threading

from services.perplexity import query_perplexity
from utils.formatting import format_answer, split_message

# Module-level state for first-time greeting detection
greeted_users: set = set()

# Constants
ERROR_MSG = (
    "Uh oh, it seems my brain is offline \u2014 talk to @Robert Li about trying to kick start it"
)
GREETING = (
    "Hey there! I'm Kahm-pew-terr, your AI research assistant. "
    "Ask me anything and I'll search the web for a cited answer.\n\n"
)

# Regex to strip @mention tags from message text
MENTION_RE = re.compile(r"<@[A-Z0-9]+>\s*")


def update_slow_message(client, channel: str, loading_ts: str) -> None:
    """Called by the 60-second timer if Perplexity is still running."""
    client.chat_update(
        channel=channel,
        ts=loading_ts,
        text="Taking longer than expected, still working on it...",
    )


def _handle_question(client, channel: str, thread_ts: str, user_id: str, user_text: str) -> None:
    """Shared logic: post loading indicator, call Perplexity, update with cited answer."""
    loading_response = client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text="Searching...",
    )
    loading_ts = loading_response["ts"]

    timer = threading.Timer(60, update_slow_message, args=[client, channel, loading_ts])
    timer.start()

    try:
        result = query_perplexity(user_text)
        timer.cancel()

        formatted = format_answer(result["answer"], result["citations"])

        if user_id not in greeted_users:
            greeted_users.add(user_id)
            full_text = GREETING + formatted
        else:
            full_text = formatted

        chunks = split_message(full_text)

        client.chat_update(
            channel=channel,
            ts=loading_ts,
            text=chunks[0],
        )

        for chunk in chunks[1:]:
            client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=chunk,
            )

    except Exception:
        timer.cancel()
        client.chat_update(
            channel=channel,
            ts=loading_ts,
            text=ERROR_MSG,
        )


def handle_dm(client, event: dict) -> None:
    """Lazy listener: process a DM, call Perplexity, reply with cited answer."""
    if event.get("bot_id"):
        return
    if event.get("subtype"):
        return
    if event.get("channel_type") != "im":
        return

    _handle_question(
        client,
        channel=event["channel"],
        thread_ts=event["ts"],
        user_id=event.get("user", ""),
        user_text=event.get("text", ""),
    )


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


def register_dm_handler(app) -> None:
    """Register DM and @mention handlers on the given Bolt app."""

    def ack_dm_message(ack, event):
        if event.get("bot_id"):
            return
        if event.get("subtype"):
            return
        if event.get("channel_type") != "im":
            return
        ack()

    app.event("message")(ack=ack_dm_message, lazy=[handle_dm])
    app.event("app_mention")(handle_mention)
