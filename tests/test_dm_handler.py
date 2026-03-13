"""Tests for the DM message handler."""
from unittest.mock import MagicMock, patch
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_dm_event(text="Hello bot", user="U123", ts="111.222", subtype=None, bot_id=None, channel_type="im"):
    event = {
        "type": "message",
        "channel": "D001",
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDMHandlerGuards:
    """Tests for early-exit guards in handle_dm."""

    def test_ignores_bot_messages(self, mock_slack_client):
        """When event has bot_id set, handler does not call chat_postMessage."""
        from handlers.message_handler import handle_dm

        event = make_dm_event(bot_id="B999")
        handle_dm(mock_slack_client, event)

        mock_slack_client.chat_postMessage.assert_not_called()

    def test_ignores_non_dm(self, mock_slack_client):
        """When event has channel_type != 'im', handler does not call chat_postMessage."""
        from handlers.message_handler import handle_dm

        event = make_dm_event(channel_type="channel")
        handle_dm(mock_slack_client, event)

        mock_slack_client.chat_postMessage.assert_not_called()

    def test_ignores_message_subtypes(self, mock_slack_client):
        """When event has a subtype, handler does not process it."""
        from handlers.message_handler import handle_dm

        event = make_dm_event(subtype="message_changed")
        handle_dm(mock_slack_client, event)

        mock_slack_client.chat_postMessage.assert_not_called()


class TestDMHandlerPipeline:
    """Tests for the main DM processing pipeline."""

    def test_loading_message_posted(self, mock_slack_client):
        """Handler calls chat_postMessage with 'Searching...' and thread_ts=event['ts']."""
        from handlers.message_handler import handle_dm

        event = make_dm_event(ts="111.222")

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt, \
             patch("handlers.shared.resolve_uids", side_effect=lambda t, c: t), \
             patch("handlers.message_handler.fetch_channel_history", return_value=[]), \
             patch("handlers.message_handler.get_bot_user_id", return_value="UBOT"):
            mock_pplx.return_value = {"answer": "Answer", "citations": []}
            mock_fmt.return_value = "Formatted answer"
            handle_dm(mock_slack_client, event)

        # First postMessage call should be the "Searching..." indicator
        first_call_kwargs = mock_slack_client.chat_postMessage.call_args_list[0][1]
        assert first_call_kwargs["text"] == "Searching..."
        assert first_call_kwargs["thread_ts"] == "111.222"

    def test_loading_message_updated(self, mock_slack_client):
        """After Perplexity returns, handler calls chat_update with loading_ts and answer."""
        from handlers.message_handler import handle_dm

        event = make_dm_event(ts="111.222")
        loading_ts = "333.444"
        mock_slack_client.chat_postMessage.return_value = {"ts": loading_ts}

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt, \
             patch("handlers.shared.resolve_uids", side_effect=lambda t, c: t), \
             patch("handlers.message_handler.fetch_channel_history", return_value=[]), \
             patch("handlers.message_handler.get_bot_user_id", return_value="UBOT"):
            mock_pplx.return_value = {"answer": "Answer", "citations": []}
            mock_fmt.return_value = "Formatted answer"
            handle_dm(mock_slack_client, event)

        # chat_update should use the loading message ts
        update_kwargs = mock_slack_client.chat_update.call_args[1]
        assert update_kwargs["ts"] == loading_ts
        assert "Formatted answer" in update_kwargs["text"]

    def test_dm_triggers_response(self, mock_slack_client):
        """Given valid DM event, handler calls query_perplexity with event text, then format_answer, then chat_update."""
        from handlers.message_handler import handle_dm

        event = make_dm_event(text="What is Python?", user="U_FRESH_1a")

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt, \
             patch("handlers.shared.resolve_uids", side_effect=lambda t, c: t), \
             patch("handlers.message_handler.fetch_channel_history", return_value=[]), \
             patch("handlers.message_handler.get_bot_user_id", return_value="UBOT"):
            mock_pplx.return_value = {"answer": "Python is...", "citations": [{"url": "u", "title": "t"}]}
            mock_fmt.return_value = "Python is...\n---\n[1] <u|t>"
            handle_dm(mock_slack_client, event)

        mock_pplx.assert_called_once_with("What is Python?", messages=[])
        mock_fmt.assert_called_once_with("Python is...", [{"url": "u", "title": "t"}])
        mock_slack_client.chat_update.assert_called_once()

    def test_reply_is_threaded(self, mock_slack_client):
        """All chat_postMessage calls include thread_ts matching the original event ts."""
        from handlers.message_handler import handle_dm

        event_ts = "555.666"
        event = make_dm_event(ts=event_ts, user="U_FRESH_2b")

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt, \
             patch("handlers.shared.resolve_uids", side_effect=lambda t, c: t), \
             patch("handlers.message_handler.fetch_channel_history", return_value=[]), \
             patch("handlers.message_handler.get_bot_user_id", return_value="UBOT"):
            mock_pplx.return_value = {"answer": "A", "citations": []}
            mock_fmt.return_value = "A"
            handle_dm(mock_slack_client, event)

        for call in mock_slack_client.chat_postMessage.call_args_list:
            assert call[1]["thread_ts"] == event_ts

    def test_error_message(self, mock_slack_client):
        """When query_perplexity raises an exception, handler calls chat_update with friendly error message."""
        from handlers.message_handler import handle_dm

        event = make_dm_event()
        loading_ts = "777.888"
        mock_slack_client.chat_postMessage.return_value = {"ts": loading_ts}

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.resolve_uids", side_effect=lambda t, c: t), \
             patch("handlers.message_handler.fetch_channel_history", return_value=[]), \
             patch("handlers.message_handler.get_bot_user_id", return_value="UBOT"):
            mock_pplx.side_effect = RuntimeError("API down")
            handle_dm(mock_slack_client, event)

        update_kwargs = mock_slack_client.chat_update.call_args[1]
        assert "brain is offline" in update_kwargs["text"]
        assert update_kwargs["ts"] == loading_ts

    def test_first_time_greeting(self, mock_slack_client):
        """First message from a user_id prepends greeting text; second does not."""
        import handlers.shared as mod
        from handlers.message_handler import handle_dm

        # Use a unique user id not used by other tests
        unique_user = "U_UNIQUE_GREETING_XYZ"
        # Ensure this user is NOT in greeted_users
        mod.greeted_users.discard(unique_user)

        event = make_dm_event(user=unique_user)

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt, \
             patch("handlers.shared.resolve_uids", side_effect=lambda t, c: t), \
             patch("handlers.message_handler.fetch_channel_history", return_value=[]), \
             patch("handlers.message_handler.get_bot_user_id", return_value="UBOT"):
            mock_pplx.return_value = {"answer": "A", "citations": []}
            mock_fmt.return_value = "Formatted"

            # First message — greeting expected
            handle_dm(mock_slack_client, event)
            first_update_text = mock_slack_client.chat_update.call_args[1]["text"]
            assert "Kahm-pew-terr" in first_update_text

            mock_slack_client.reset_mock()

            # Second message — no greeting
            handle_dm(mock_slack_client, event)
            second_update_text = mock_slack_client.chat_update.call_args[1]["text"]
            assert "Kahm-pew-terr" not in second_update_text

    def test_long_response_split(self, mock_slack_client):
        """When formatted answer exceeds 3800 chars, first chunk updates loading message, additional chunks post as new thread messages."""
        from handlers.message_handler import handle_dm

        event = make_dm_event(ts="999.000", user="U_FRESH_3c")
        loading_ts = "111.999"
        mock_slack_client.chat_postMessage.return_value = {"ts": loading_ts}

        long_answer = "X" * 10000  # Exceeds 3800-char limit

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt, \
             patch("handlers.shared.resolve_uids", side_effect=lambda t, c: t), \
             patch("handlers.message_handler.fetch_channel_history", return_value=[]), \
             patch("handlers.message_handler.get_bot_user_id", return_value="UBOT"):
            mock_pplx.return_value = {"answer": long_answer, "citations": []}
            mock_fmt.return_value = long_answer
            handle_dm(mock_slack_client, event)

        # chat_update called with loading_ts for first chunk
        update_kwargs = mock_slack_client.chat_update.call_args[1]
        assert update_kwargs["ts"] == loading_ts
        assert len(update_kwargs["text"]) <= 3800

        # Remaining chunks posted as new thread messages (after the initial Searching... postMessage)
        post_calls = mock_slack_client.chat_postMessage.call_args_list
        # First call is "Searching...", subsequent calls are overflow chunks
        overflow_calls = [c for c in post_calls if c[1].get("text") != "Searching..."]
        assert len(overflow_calls) >= 2  # At least 2 overflow chunks for 10000 chars
        for call in overflow_calls:
            assert call[1]["thread_ts"] == "999.000"
