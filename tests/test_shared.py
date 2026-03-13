"""Tests for handlers/shared.py — the shared question-handling pipeline."""
from unittest.mock import MagicMock, patch, call
import pytest


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
