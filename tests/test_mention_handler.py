"""Tests for handlers/mention_handler.py — @mention handler context fetching."""
from unittest.mock import MagicMock, patch
import pytest


def make_mention_event(
    text="<@UBOT> what is Python?",
    user="U123",
    ts="111.222",
    channel="C001",
    thread_ts=None,
):
    """Build a minimal app_mention event dict."""
    event = {
        "type": "app_mention",
        "channel": channel,
        "user": user,
        "text": text,
        "ts": ts,
    }
    if thread_ts is not None:
        event["thread_ts"] = thread_ts
    return event


class TestHandleMentionGuards:
    """handle_mention returns early for empty text after stripping mention."""

    def test_empty_text_after_strip_returns_without_calling_question(self, mock_slack_client):
        """When text is only the @mention tag, handler returns without action."""
        from handlers.mention_handler import handle_mention

        event = make_mention_event(text="<@UBOT>")
        with patch("handlers.mention_handler._handle_question") as mock_q, \
             patch("handlers.mention_handler.get_bot_user_id", return_value="UBOT"), \
             patch("handlers.mention_handler.fetch_channel_history", return_value=[]):
            handle_mention(event, mock_slack_client)
            mock_q.assert_not_called()

    def test_whitespace_only_text_after_strip_returns_early(self, mock_slack_client):
        """When text is only the @mention tag and whitespace, handler returns early."""
        from handlers.mention_handler import handle_mention

        event = make_mention_event(text="<@UBOT>   ")
        with patch("handlers.mention_handler._handle_question") as mock_q, \
             patch("handlers.mention_handler.get_bot_user_id", return_value="UBOT"), \
             patch("handlers.mention_handler.fetch_channel_history", return_value=[]):
            handle_mention(event, mock_slack_client)
            mock_q.assert_not_called()


class TestHandleMentionContextFetching:
    """handle_mention fetches thread or channel history based on event structure."""

    def test_mention_with_thread_ts_fetches_thread_history(self, mock_slack_client):
        """When mention event has thread_ts, fetch_thread_history is called (not channel)."""
        from handlers.mention_handler import handle_mention

        event = make_mention_event(
            text="<@UBOT> follow-up",
            ts="222.333",
            channel="C001",
            thread_ts="200.000",
        )

        thread_messages = [{"type": "message", "role": "user", "content": "prior"}]
        with patch("handlers.mention_handler._handle_question") as mock_q, \
             patch("handlers.mention_handler.fetch_thread_history", return_value=thread_messages) as mock_th, \
             patch("handlers.mention_handler.fetch_channel_history") as mock_ch, \
             patch("handlers.mention_handler.get_bot_user_id", return_value="UBOT"):
            handle_mention(event, mock_slack_client)

        mock_th.assert_called_once_with(mock_slack_client, "C001", "200.000", "222.333", "UBOT")
        mock_ch.assert_not_called()
        mock_q.assert_called_once_with(
            mock_slack_client,
            channel="C001",
            thread_ts="222.333",
            user_id="U123",
            user_text="follow-up",
            messages=thread_messages,
        )

    def test_mention_without_thread_ts_fetches_channel_history(self, mock_slack_client):
        """When mention event has no thread_ts, fetch_channel_history is called."""
        from handlers.mention_handler import handle_mention

        event = make_mention_event(
            text="<@UBOT> what is Python?",
            ts="333.444",
            user="U_NEW",
            channel="C002",
        )
        # No thread_ts

        channel_messages = [{"type": "message", "role": "user", "content": "prior channel msg"}]
        with patch("handlers.mention_handler._handle_question") as mock_q, \
             patch("handlers.mention_handler.fetch_thread_history") as mock_th, \
             patch("handlers.mention_handler.fetch_channel_history", return_value=channel_messages) as mock_ch, \
             patch("handlers.mention_handler.get_bot_user_id", return_value="UBOT"):
            handle_mention(event, mock_slack_client)

        mock_ch.assert_called_once_with(mock_slack_client, "C002", "UBOT")
        mock_th.assert_not_called()
        mock_q.assert_called_once_with(
            mock_slack_client,
            channel="C002",
            thread_ts="333.444",
            user_id="U_NEW",
            user_text="what is Python?",
            messages=channel_messages,
        )

    def test_mention_strips_mention_tag_from_user_text(self, mock_slack_client):
        """The @mention tag is stripped from user_text before passing to _handle_question."""
        from handlers.mention_handler import handle_mention

        event = make_mention_event(
            text="<@UBOT> what is the weather?",
            ts="444.555",
            channel="C003",
        )

        with patch("handlers.mention_handler._handle_question") as mock_q, \
             patch("handlers.mention_handler.fetch_channel_history", return_value=[]) as mock_ch, \
             patch("handlers.mention_handler.get_bot_user_id", return_value="UBOT"):
            handle_mention(event, mock_slack_client)

        call_kwargs = mock_q.call_args[1]
        assert call_kwargs["user_text"] == "what is the weather?"

    def test_mention_passes_messages_to_handle_question(self, mock_slack_client):
        """fetch result is forwarded as messages= to _handle_question."""
        from handlers.mention_handler import handle_mention

        event = make_mention_event(text="<@UBOT> question", ts="555.666", channel="C004")
        fetched = [{"type": "message", "role": "user", "content": "context"}]

        with patch("handlers.mention_handler._handle_question") as mock_q, \
             patch("handlers.mention_handler.fetch_channel_history", return_value=fetched), \
             patch("handlers.mention_handler.get_bot_user_id", return_value="UBOT"):
            handle_mention(event, mock_slack_client)

        mock_q.assert_called_once()
        assert mock_q.call_args[1]["messages"] == fetched
