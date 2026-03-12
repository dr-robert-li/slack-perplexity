"""DM message handler — full pipeline from Slack DM to cited Perplexity answer."""
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


def update_slow_message(client, channel: str, loading_ts: str) -> None:
    """Called by the 60-second timer if Perplexity is still running."""
    client.chat_update(
        channel=channel,
        ts=loading_ts,
        text="Taking longer than expected, still working on it...",
    )


def handle_dm(client, event: dict) -> None:
    """Lazy listener: process a DM, post loading indicator, call Perplexity, update in-place.

    Guards:
        - Ignores events with ``bot_id`` set (prevent infinite loops).
        - Ignores events whose ``channel_type`` is not ``"im"``.
        - Ignores events with a ``subtype`` (e.g. ``message_changed``).
    """
    # --- Guards ---
    if event.get("bot_id"):
        return
    if event.get("subtype"):
        return
    if event.get("channel_type") != "im":
        return

    channel = event["channel"]
    thread_ts = event["ts"]
    user_id = event.get("user", "")
    user_text = event.get("text", "")

    # Post the loading indicator in the thread
    loading_response = client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text="Searching...",
    )
    loading_ts = loading_response["ts"]

    # Start 60-second slow-response timer
    timer = threading.Timer(60, update_slow_message, args=[client, channel, loading_ts])
    timer.start()

    try:
        result = query_perplexity(user_text)
        timer.cancel()

        formatted = format_answer(result["answer"], result["citations"])

        # Determine greeting prefix
        if user_id not in greeted_users:
            greeted_users.add(user_id)
            full_text = GREETING + formatted
        else:
            full_text = formatted

        chunks = split_message(full_text)

        # Update loading message with first chunk
        client.chat_update(
            channel=channel,
            ts=loading_ts,
            text=chunks[0],
        )

        # Post any remaining chunks as new thread messages
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


def register_dm_handler(app) -> None:
    """Register the DM message handler on the given Bolt app."""

    def ack_dm_message(ack, event):
        # Skip ack (and lazy processing) for events we don't handle
        if event.get("bot_id"):
            return
        if event.get("subtype"):
            return
        if event.get("channel_type") != "im":
            return
        ack()

    app.event("message", lazy=[handle_dm])(ack_dm_message)
