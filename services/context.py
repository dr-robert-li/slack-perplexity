"""Context assembly service — UID resolution, thread history, channel history."""
import os
import re

# ---------------------------------------------------------------------------
# Config constants — read from env vars with sensible defaults
# ---------------------------------------------------------------------------

HISTORY_DEPTH = int(os.environ.get("HISTORY_DEPTH", "10"))
MSG_TRUNCATE_LENGTH = int(os.environ.get("MSG_TRUNCATE_LENGTH", "500"))

# ---------------------------------------------------------------------------
# UID resolution cache — persists for bot lifetime (single-process Socket Mode)
# ---------------------------------------------------------------------------

_uid_cache: dict[str, str] = {}


def resolve_uids(text: str, client) -> str:
    """Replace all <@UID> tags in text with display names from Slack API.

    Lookups are cached in memory so the same UID is only fetched once.
    If a lookup fails for any reason, the raw tag is left unchanged.

    Args:
        text: The message text, potentially containing <@UID> tags.
        client: A Slack WebClient instance.

    Returns:
        The text with UID tags replaced by display names where available.
    """
    uids = re.findall(r"<@([A-Z0-9]+)>", text)
    for uid in uids:
        if uid not in _uid_cache:
            try:
                result = client.users_info(user=uid)
                display_name = result["user"]["profile"]["display_name"]
                real_name = result["user"]["real_name"]
                # Fall back to real_name if display_name is empty
                _uid_cache[uid] = display_name if display_name else real_name
            except Exception:
                # Leave raw tag — do not cache failures so future calls can retry
                continue
        if uid in _uid_cache:
            text = text.replace(f"<@{uid}>", _uid_cache[uid])
    return text


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _truncate(text: str) -> str:
    """Truncate text to MSG_TRUNCATE_LENGTH characters, appending '...' if cut."""
    if len(text) > MSG_TRUNCATE_LENGTH:
        return text[:MSG_TRUNCATE_LENGTH] + "..."
    return text


def _build_message(text: str, bot_user_id: str, sender_id: str) -> dict:
    """Build a structured message dict compatible with Perplexity InputMessage.

    Args:
        text: The message content (already truncated if needed).
        bot_user_id: The Slack user ID of this bot.
        sender_id: The Slack user ID of the message sender.

    Returns:
        A dict with type, role, and content keys.
    """
    role = "assistant" if sender_id == bot_user_id else "user"
    return {"type": "message", "role": role, "content": _truncate(text)}


# ---------------------------------------------------------------------------
# History fetchers
# ---------------------------------------------------------------------------

def fetch_thread_history(
    client,
    channel: str,
    thread_ts: str,
    current_ts: str,
    bot_user_id: str,
) -> list[dict]:
    """Fetch prior messages from a thread, excluding the current trigger message.

    Args:
        client: A Slack WebClient instance.
        channel: The channel ID containing the thread.
        thread_ts: The thread's root timestamp.
        current_ts: The timestamp of the message that triggered this handler
                    (excluded from results).
        bot_user_id: The Slack user ID of this bot, used for role assignment.

    Returns:
        A list of structured {type, role, content} dicts in thread order,
        up to HISTORY_DEPTH messages. Returns [] on API failure.
    """
    try:
        response = client.conversations_replies(
            channel=channel,
            ts=thread_ts,
            limit=HISTORY_DEPTH + 1,  # +1 to account for the current message
        )
        messages = [
            msg for msg in response["messages"]
            if msg["ts"] != current_ts
        ]
        messages = messages[:HISTORY_DEPTH]

        result = []
        for msg in messages:
            text = resolve_uids(msg.get("text", ""), client)
            sender_id = msg.get("user", "")
            result.append(_build_message(text, bot_user_id, sender_id))
        return result
    except Exception:
        return []


def fetch_channel_history(
    client,
    channel: str,
    bot_user_id: str,
) -> list[dict]:
    """Fetch recent messages from a channel in chronological order.

    Args:
        client: A Slack WebClient instance.
        channel: The channel ID to fetch history from.
        bot_user_id: The Slack user ID of this bot, used for role assignment.

    Returns:
        A list of structured {type, role, content} dicts, oldest-first,
        up to HISTORY_DEPTH messages. Returns [] on API failure.
    """
    try:
        response = client.conversations_history(
            channel=channel,
            limit=HISTORY_DEPTH,
        )
        # API returns newest-first — reverse to chronological order
        messages = list(reversed(response["messages"]))

        result = []
        for msg in messages:
            text = resolve_uids(msg.get("text", ""), client)
            sender_id = msg.get("user", "")
            result.append(_build_message(text, bot_user_id, sender_id))
        return result
    except Exception:
        return []
