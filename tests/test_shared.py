"""Tests for handlers/shared.py — the shared question-handling pipeline."""
from unittest.mock import MagicMock, patch, call
import pytest


class TestHandleQuestionWithContext:
    """Tests for _handle_question with the new messages= and UID resolution behavior."""

    def test_messages_passed_to_query_perplexity(self, mock_slack_client):
        """When messages=[...] is provided, query_perplexity receives messages= kwarg."""
        from handlers.shared import _handle_question

        prior_messages = [{"type": "message", "role": "user", "content": "prior question"}]
        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt, \
             patch("handlers.shared.resolve_uids", side_effect=lambda t, c: t):
            mock_pplx.return_value = {"answer": "A", "citations": []}
            mock_fmt.return_value = "Formatted"
            _handle_question(mock_slack_client, "C001", "123.456", "U001", "follow-up", messages=prior_messages)

        mock_pplx.assert_called_once_with("follow-up", messages=prior_messages)

    def test_messages_none_passes_none_to_query_perplexity(self, mock_slack_client):
        """When messages=None (default), query_perplexity is called with messages=None."""
        from handlers.shared import _handle_question

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt, \
             patch("handlers.shared.resolve_uids", side_effect=lambda t, c: t):
            mock_pplx.return_value = {"answer": "A", "citations": []}
            mock_fmt.return_value = "Formatted"
            _handle_question(mock_slack_client, "C001", "123.456", "U001", "question")

        mock_pplx.assert_called_once_with("question", messages=None)

    def test_resolve_uids_called_on_user_text(self, mock_slack_client):
        """resolve_uids is called on user_text before passing to query_perplexity."""
        from handlers.shared import _handle_question

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt, \
             patch("handlers.shared.resolve_uids") as mock_resolve:
            mock_pplx.return_value = {"answer": "A", "citations": []}
            mock_fmt.return_value = "Formatted"
            mock_resolve.return_value = "resolved text"
            _handle_question(mock_slack_client, "C001", "123.456", "U001", "<@UABC> hello")

        mock_resolve.assert_called_once_with("<@UABC> hello", mock_slack_client)
        mock_pplx.assert_called_once_with("resolved text", messages=None)

    def test_get_bot_user_id_caches_after_first_call(self, mock_slack_client):
        """get_bot_user_id() returns bot ID from auth_test and caches it."""
        import handlers.shared as mod
        from handlers.shared import get_bot_user_id

        # Reset module-level cache to ensure clean test
        mod._bot_user_id = None
        mock_slack_client.auth_test.return_value = {"user_id": "UBOT123"}

        result = get_bot_user_id(mock_slack_client)
        assert result == "UBOT123"
        mock_slack_client.auth_test.assert_called_once()

        # Second call should use cache — auth_test NOT called again
        result2 = get_bot_user_id(mock_slack_client)
        assert result2 == "UBOT123"
        mock_slack_client.auth_test.assert_called_once()  # still only once


class TestHandleQuestionWithThreadTs:
    """Tests for _handle_question when thread_ts is a real ts string."""

    def test_loading_message_threaded_on_event_ts(self, mock_slack_client):
        """When thread_ts='123.456', 'Searching...' is posted with that thread_ts."""
        from handlers.shared import _handle_question

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt:
            mock_pplx.return_value = {"answer": "A", "citations": []}
            mock_fmt.return_value = "Formatted"
            _handle_question(mock_slack_client, "C001", "123.456", "U001", "question")

        first_call_kwargs = mock_slack_client.chat_postMessage.call_args_list[0][1]
        assert first_call_kwargs["text"] == "Searching..."
        assert first_call_kwargs["thread_ts"] == "123.456"

    def test_overflow_chunks_use_thread_ts(self, mock_slack_client):
        """When thread_ts is given, overflow chunks are posted with that same thread_ts."""
        from handlers.shared import _handle_question

        loading_ts = "999.111"
        mock_slack_client.chat_postMessage.return_value = {"ts": loading_ts}
        long_answer = "X" * 10000

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt:
            mock_pplx.return_value = {"answer": long_answer, "citations": []}
            mock_fmt.return_value = long_answer
            _handle_question(mock_slack_client, "C001", "123.456", "U_OVF_TS", long_answer)

        overflow_calls = [
            c for c in mock_slack_client.chat_postMessage.call_args_list
            if c[1].get("text") != "Searching..."
        ]
        assert len(overflow_calls) >= 2
        for c in overflow_calls:
            assert c[1]["thread_ts"] == "123.456"


class TestHandleQuestionWithoutThreadTs:
    """Tests for _handle_question when thread_ts=None (slash command / App Home use case)."""

    def test_loading_message_posted_without_thread_ts(self, mock_slack_client):
        """When thread_ts=None, 'Searching...' is posted WITHOUT a thread_ts kwarg (top-level)."""
        from handlers.shared import _handle_question

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt:
            mock_pplx.return_value = {"answer": "A", "citations": []}
            mock_fmt.return_value = "Formatted"
            _handle_question(mock_slack_client, "C001", None, "U001", "question")

        first_call_kwargs = mock_slack_client.chat_postMessage.call_args_list[0][1]
        assert first_call_kwargs["text"] == "Searching..."
        assert "thread_ts" not in first_call_kwargs

    def test_overflow_chunks_use_loading_ts_as_anchor(self, mock_slack_client):
        """When thread_ts=None, overflow chunks are anchored to the loading message ts."""
        from handlers.shared import _handle_question

        loading_ts = "555.777"
        mock_slack_client.chat_postMessage.return_value = {"ts": loading_ts}
        long_answer = "Y" * 10000

        with patch("handlers.shared.query_perplexity") as mock_pplx, \
             patch("handlers.shared.format_answer") as mock_fmt:
            mock_pplx.return_value = {"answer": long_answer, "citations": []}
            mock_fmt.return_value = long_answer
            _handle_question(mock_slack_client, "C001", None, "U_OVF_NONE", long_answer)

        overflow_calls = [
            c for c in mock_slack_client.chat_postMessage.call_args_list
            if c[1].get("text") != "Searching..."
        ]
        assert len(overflow_calls) >= 2
        for c in overflow_calls:
            assert c[1]["thread_ts"] == loading_ts
