"""Shared handler pipeline — shared logic for DMs, @mentions, slash commands, App Home."""
import os
import re
import threading

from services.perplexity import query_perplexity
from services.context import resolve_uids
from utils.formatting import format_answer, split_message

# Module-level state for first-time greeting detection
greeted_users: set = set()

# Cached bot user ID — populated on first call to get_bot_user_id()
_bot_user_id: str | None = None


def get_bot_user_id(client) -> str:
    """Return the bot's Slack user ID, fetching and caching it on first call."""
    global _bot_user_id
    if _bot_user_id is None:
        _bot_user_id = client.auth_test()["user_id"]
    return _bot_user_id


# Constants
ADMIN_UID = os.environ.get("ADMIN_UID", "")
_ERROR_BASE = "Uh oh, it seems my brain is offline"
ERROR_MSG = (
    f"{_ERROR_BASE} \u2014 talk to <@{ADMIN_UID}> about trying to kick start it"
    if ADMIN_UID
    else f"{_ERROR_BASE} \u2014 please contact an admin"
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


def _handle_question(
    client,
    channel: str,
    thread_ts: str | None,
    user_id: str,
    user_text: str,
    messages: list[dict] | None = None,
) -> None:
    """Shared logic: post loading indicator, call Perplexity, update with cited answer.

    When thread_ts is None (e.g. slash command / App Home), the loading message is posted
    as a top-level message. The loading message ts is then used as the thread anchor for
    all subsequent overflow chunk replies.

    Args:
        client: Slack WebClient.
        channel: Channel ID to post into.
        thread_ts: Thread timestamp to reply in, or None for top-level.
        user_id: Slack user ID of the asker.
        user_text: The question text (may contain <@UID> tags).
        messages: Optional prior conversation history for Perplexity context.
    """
    # Resolve any <@UID> tags in the question text to display names.
    user_text = resolve_uids(user_text, client)

    # Build loading message kwargs — omit thread_ts entirely when None so the message
    # is posted at the top level (not inside any thread).
    loading_kwargs: dict = {"channel": channel, "text": "Searching..."}
    if thread_ts is not None:
        loading_kwargs["thread_ts"] = thread_ts

    loading_response = client.chat_postMessage(**loading_kwargs)
    loading_ts = loading_response["ts"]

    # anchor_ts: where overflow chunks are threaded.
    # If we had a real thread_ts, use it; otherwise use the loading message ts.
    anchor_ts = thread_ts if thread_ts is not None else loading_ts

    timer = threading.Timer(60, update_slow_message, args=[client, channel, loading_ts])
    timer.start()

    try:
        result = query_perplexity(user_text, messages=messages)
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
                thread_ts=anchor_ts,
                text=chunk,
            )

    except Exception:
        timer.cancel()
        client.chat_update(
            channel=channel,
            ts=loading_ts,
            text=ERROR_MSG,
        )
