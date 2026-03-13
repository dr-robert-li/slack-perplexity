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
        with patch("handlers.message_handler._handle_question") as mock_q:
            handle_mpim(mock_slack_client, event)
            mock_q.assert_called_once_with(
                mock_slack_client,
                channel="G001",
                thread_ts="123.456",
                user_id="U_HUMAN",
                user_text="what is Python?",
            )
