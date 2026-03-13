"""Tests for handlers/message_handler.py — DM and group DM (mpim) handlers."""
from unittest.mock import MagicMock, patch
import pytest


def make_event(
    text="Hello bot",
    user="U123",
    ts="111.222",
    subtype=None,
    bot_id=None,
    channel_type="mpim",
    channel="C001",
):
    event = {
        "type": "message",
        "channel": channel,
        "channel_type": channel_type,
        "user": user,
        "text": text,
        "ts": ts,
    }
    if subtype is not None:
        event["subtype"] = subtype
    if bot_id is not None:
        event["bot_id"] = bot_id
    return event


class TestHandleMpimGuards:
    """handle_mpim returns early without calling _handle_question for disallowed events."""

    def test_ignores_bot_id(self, mock_slack_client):
        """Group DM event with bot_id is ignored."""
        from handlers.message_handler import handle_mpim

        event = make_event(bot_id="B999", text="<@UBOTABC> question")
        with patch("handlers.message_handler._handle_question") as mock_q:
            handle_mpim(mock_slack_client, event)
            mock_q.assert_not_called()

    def test_ignores_subtype(self, mock_slack_client):
        """Group DM event with subtype is ignored."""
        from handlers.message_handler import handle_mpim

        event = make_event(subtype="message_changed", text="<@UBOTABC> question")
        with patch("handlers.message_handler._handle_question") as mock_q:
            handle_mpim(mock_slack_client, event)
            mock_q.assert_not_called()

    def test_ignores_non_mpim(self, mock_slack_client):
        """Event with channel_type != 'mpim' is ignored by handle_mpim."""
        from handlers.message_handler import handle_mpim

        event = make_event(channel_type="channel", text="<@UBOTABC> question")
        with patch("handlers.message_handler._handle_question") as mock_q:
            handle_mpim(mock_slack_client, event)
            mock_q.assert_not_called()

    def test_ignores_mpim_without_mention(self, mock_slack_client):
        """Group DM message without @mention is ignored."""
        from handlers.message_handler import handle_mpim

        event = make_event(channel_type="mpim", text="just chatting")
        with patch("handlers.message_handler._handle_question") as mock_q:
            handle_mpim(mock_slack_client, event)
            mock_q.assert_not_called()


class TestHandleMpimHappyPath:
    """handle_mpim fires _handle_question with stripped text for valid mpim @mention."""

    def test_mpim_mention_triggers_question(self, mock_slack_client):
        """Group DM with @mention calls _handle_question with stripped text and thread_ts=event ts."""
        from handlers.message_handler import handle_mpim

        event = make_event(
            channel_type="mpim",
            text="<@UBOTABC123> what is Python?",
            ts="123.456",
            user="U_HUMAN",
            channel="G001",
        )
        with patch("handlers.message_handler._handle_question") as mock_q, \
             patch("handlers.message_handler.fetch_channel_history", return_value=[]) as mock_ch, \
             patch("handlers.message_handler.get_bot_user_id", return_value="UBOT"):
            handle_mpim(mock_slack_client, event)
            mock_q.assert_called_once_with(
                mock_slack_client,
                channel="G001",
                thread_ts="123.456",
                user_id="U_HUMAN",
                user_text="what is Python?",
                messages=[],
            )


class TestHandleDmContextFetching:
    """handle_dm fetches thread or channel history based on event structure."""

    def test_dm_with_thread_ts_fetches_thread_history(self, mock_slack_client):
        """When DM event has thread_ts, fetch_thread_history is called (not channel history)."""
        from handlers.message_handler import handle_dm

        event = make_event(
            channel_type="im",
            text="follow-up question",
            ts="222.333",
            channel="D001",
        )
        event["thread_ts"] = "111.000"  # user replying in existing thread

        thread_messages = [{"type": "message", "role": "user", "content": "original"}]
        with patch("handlers.message_handler._handle_question") as mock_q, \
             patch("handlers.message_handler.fetch_thread_history", return_value=thread_messages) as mock_th, \
             patch("handlers.message_handler.fetch_channel_history") as mock_ch, \
             patch("handlers.message_handler.get_bot_user_id", return_value="UBOT"):
            handle_dm(mock_slack_client, event)

        mock_th.assert_called_once_with(mock_slack_client, "D001", "111.000", "222.333", "UBOT")
        mock_ch.assert_not_called()
        mock_q.assert_called_once_with(
            mock_slack_client,
            channel="D001",
            thread_ts="222.333",
            user_id=event.get("user", ""),
            user_text="follow-up question",
            messages=thread_messages,
        )

    def test_dm_without_thread_ts_fetches_channel_history(self, mock_slack_client):
        """When DM event has no thread_ts, fetch_channel_history is called (not thread history)."""
        from handlers.message_handler import handle_dm

        event = make_event(
            channel_type="im",
            text="new question",
            ts="333.444",
            user="U_NEW",
            channel="D002",
        )
        # No thread_ts in event

        channel_messages = [{"type": "message", "role": "user", "content": "prior dm"}]
        with patch("handlers.message_handler._handle_question") as mock_q, \
             patch("handlers.message_handler.fetch_thread_history") as mock_th, \
             patch("handlers.message_handler.fetch_channel_history", return_value=channel_messages) as mock_ch, \
             patch("handlers.message_handler.get_bot_user_id", return_value="UBOT"):
            handle_dm(mock_slack_client, event)

        mock_ch.assert_called_once_with(mock_slack_client, "D002", "UBOT")
        mock_th.assert_not_called()
        mock_q.assert_called_once_with(
            mock_slack_client,
            channel="D002",
            thread_ts="333.444",
            user_id="U_NEW",
            user_text="new question",
            messages=channel_messages,
        )


class TestHandleMpimContextFetching:
    """handle_mpim fetches thread or channel history based on event structure."""

    def test_mpim_with_thread_ts_fetches_thread_history(self, mock_slack_client):
        """When mpim event has thread_ts, fetch_thread_history is called."""
        from handlers.message_handler import handle_mpim

        event = make_event(
            channel_type="mpim",
            text="<@UBOT> follow-up",
            ts="444.555",
            channel="G001",
        )
        event["thread_ts"] = "400.000"

        thread_messages = [{"type": "message", "role": "user", "content": "original mpim"}]
        with patch("handlers.message_handler._handle_question") as mock_q, \
             patch("handlers.message_handler.fetch_thread_history", return_value=thread_messages) as mock_th, \
             patch("handlers.message_handler.fetch_channel_history") as mock_ch, \
             patch("handlers.message_handler.get_bot_user_id", return_value="UBOT"):
            handle_mpim(mock_slack_client, event)

        mock_th.assert_called_once_with(mock_slack_client, "G001", "400.000", "444.555", "UBOT")
        mock_ch.assert_not_called()

    def test_mpim_without_thread_ts_fetches_channel_history(self, mock_slack_client):
        """When mpim event has no thread_ts, fetch_channel_history is called."""
        from handlers.message_handler import handle_mpim

        event = make_event(
            channel_type="mpim",
            text="<@UBOT> new question",
            ts="555.666",
            channel="G002",
        )
        # No thread_ts

        channel_messages = [{"type": "message", "role": "user", "content": "prior mpim"}]
        with patch("handlers.message_handler._handle_question") as mock_q, \
             patch("handlers.message_handler.fetch_thread_history") as mock_th, \
             patch("handlers.message_handler.fetch_channel_history", return_value=channel_messages) as mock_ch, \
             patch("handlers.message_handler.get_bot_user_id", return_value="UBOT"):
            handle_mpim(mock_slack_client, event)

        mock_ch.assert_called_once_with(mock_slack_client, "G002", "UBOT")
        mock_th.assert_not_called()
