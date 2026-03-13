"""Unit tests for /ask slash command handler."""
from unittest.mock import MagicMock, patch, call
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_slash_body(text="test question", channel="C001", user="U123"):
    """Build a minimal slash command body dict."""
    return {
        "text": text,
        "channel_id": channel,
        "user_id": user,
    }


# ---------------------------------------------------------------------------
# Ack always called
# ---------------------------------------------------------------------------

class TestSlashHandlerAck:
    def test_ack_called(self):
        """ack() must be called unconditionally — even on empty text."""
        from handlers.slash_handler import ack_ask

        ack = MagicMock()
        ack_ask(ack=ack)
        ack.assert_called_once()

    def test_ack_called_when_empty(self):
        """ack() must also be called when body text is empty."""
        from handlers.slash_handler import ack_ask

        ack = MagicMock()
        ack_ask(ack=ack)
        ack.assert_called_once()


# ---------------------------------------------------------------------------
# Empty text → ephemeral help
# ---------------------------------------------------------------------------

class TestSlashHandlerEmpty:
    @pytest.mark.parametrize("text", ["", "   ", None])
    def test_empty_text_calls_respond_ephemeral(self, text):
        """Empty or whitespace-only text returns ephemeral usage hint."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text=text)
        respond = MagicMock()
        run_ask(body=body, respond=respond)

        respond.assert_called_once()
        call_kwargs = respond.call_args
        text_arg = call_kwargs.kwargs.get("text") or call_kwargs.args[0]
        assert "Usage: /ask" in text_arg
        assert call_kwargs.kwargs.get("response_type") == "ephemeral"

    @pytest.mark.parametrize("text", ["", "   ", None])
    def test_empty_text_does_not_call_perplexity(self, text):
        """query_perplexity must NOT be invoked when text is empty."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text=text)
        respond = MagicMock()

        with patch("handlers.slash_handler.query_perplexity") as mock_pplx:
            run_ask(body=body, respond=respond)
            mock_pplx.assert_not_called()


# ---------------------------------------------------------------------------
# Valid text → respond-based pipeline
# ---------------------------------------------------------------------------

class TestSlashHandlerPipeline:
    def test_valid_text_posts_searching_then_answer(self):
        """Valid text posts 'Searching...' via respond, then replaces with answer."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text="What is Python?", user="U999")
        respond = MagicMock()

        with patch("handlers.slash_handler.query_perplexity") as mock_pplx, \
             patch("handlers.slash_handler.format_answer") as mock_fmt, \
             patch("handlers.slash_handler.split_message") as mock_split, \
             patch("handlers.slash_handler.greeted_users", set()):
            mock_pplx.return_value = {"answer": "A language", "citations": []}
            mock_fmt.return_value = "A language"
            mock_split.return_value = ["A language"]

            run_ask(body=body, respond=respond)

        calls = respond.call_args_list
        # First call: Searching...
        assert calls[0] == call(text="Searching...", response_type="in_channel")
        # Second call: replace with answer
        assert calls[1].kwargs["replace_original"] is True
        assert "A language" in calls[1].kwargs["text"]

    def test_valid_text_does_not_call_respond_ephemeral(self):
        """respond() with ephemeral must NOT be called when text is present."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text="What is Python?")
        respond = MagicMock()

        with patch("handlers.slash_handler.query_perplexity") as mock_pplx, \
             patch("handlers.slash_handler.format_answer") as mock_fmt, \
             patch("handlers.slash_handler.split_message") as mock_split, \
             patch("handlers.slash_handler.greeted_users", set()):
            mock_pplx.return_value = {"answer": "A", "citations": []}
            mock_fmt.return_value = "A"
            mock_split.return_value = ["A"]

            run_ask(body=body, respond=respond)

        for c in respond.call_args_list:
            assert c.kwargs.get("response_type") != "ephemeral"

    def test_text_is_stripped(self):
        """Surrounding whitespace is stripped before passing to Perplexity."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text="  What is Python?  ")
        respond = MagicMock()

        with patch("handlers.slash_handler.query_perplexity") as mock_pplx, \
             patch("handlers.slash_handler.format_answer") as mock_fmt, \
             patch("handlers.slash_handler.split_message") as mock_split, \
             patch("handlers.slash_handler.greeted_users", set()):
            mock_pplx.return_value = {"answer": "A", "citations": []}
            mock_fmt.return_value = "A"
            mock_split.return_value = ["A"]

            run_ask(body=body, respond=respond)

            mock_pplx.assert_called_once_with("What is Python?")

    def test_error_calls_respond_with_error_msg(self):
        """When query_perplexity raises, respond replaces with error message."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text="What is Python?")
        respond = MagicMock()

        with patch("handlers.slash_handler.query_perplexity") as mock_pplx:
            mock_pplx.side_effect = RuntimeError("API down")
            run_ask(body=body, respond=respond)

        last_call = respond.call_args_list[-1]
        assert "brain is offline" in last_call.kwargs["text"]
        assert last_call.kwargs["replace_original"] is True

    def test_run_ask_does_not_call_context_functions(self):
        """run_ask must NOT call fetch_thread_history or fetch_channel_history — /ask is standalone."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text="What is Python?")
        respond = MagicMock()

        # If slash_handler imports context functions and calls them, these patches will detect it.
        # If slash_handler doesn't import them at all, the patches simply do nothing — pass either way.
        with patch("handlers.slash_handler.query_perplexity") as mock_pplx, \
             patch("handlers.slash_handler.format_answer") as mock_fmt, \
             patch("handlers.slash_handler.split_message") as mock_split, \
             patch("handlers.slash_handler.greeted_users", set()):
            mock_pplx.return_value = {"answer": "A", "citations": []}
            mock_fmt.return_value = "A"
            mock_split.return_value = ["A"]

            # Verify no context module attributes exist on the slash_handler module
            import handlers.slash_handler as slash_mod
            assert not hasattr(slash_mod, "fetch_thread_history"), \
                "slash_handler must NOT import fetch_thread_history"
            assert not hasattr(slash_mod, "fetch_channel_history"), \
                "slash_handler must NOT import fetch_channel_history"

            run_ask(body=body, respond=respond)

    def test_overflow_chunks_sent_as_separate_messages(self):
        """When answer splits into multiple chunks, extras are sent as follow-ups."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text="Big question")
        respond = MagicMock()

        with patch("handlers.slash_handler.query_perplexity") as mock_pplx, \
             patch("handlers.slash_handler.format_answer") as mock_fmt, \
             patch("handlers.slash_handler.split_message") as mock_split, \
             patch("handlers.slash_handler.greeted_users", set()):
            mock_pplx.return_value = {"answer": "Long", "citations": []}
            mock_fmt.return_value = "Long"
            mock_split.return_value = ["chunk1", "chunk2", "chunk3"]

            run_ask(body=body, respond=respond)

        calls = respond.call_args_list
        # Searching + replace + 2 overflow = 4 calls
        assert len(calls) == 4
        assert calls[2].kwargs["text"] == "chunk2"
        assert calls[3].kwargs["text"] == "chunk3"
