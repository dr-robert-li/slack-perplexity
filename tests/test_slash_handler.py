"""Unit tests for /ask slash command handler."""
from unittest.mock import MagicMock, patch
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
    def test_empty_text_calls_respond_ephemeral(self, text, mock_slack_client):
        """Empty or whitespace-only text returns ephemeral usage hint."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text=text)
        respond = MagicMock()
        run_ask(client=mock_slack_client, body=body, respond=respond)

        respond.assert_called_once()
        call_kwargs = respond.call_args
        # Must include "Usage: /ask" somewhere in the text
        text_arg = call_kwargs.kwargs.get("text") or call_kwargs.args[0]
        assert "Usage: /ask" in text_arg
        assert call_kwargs.kwargs.get("response_type") == "ephemeral"

    @pytest.mark.parametrize("text", ["", "   ", None])
    def test_empty_text_does_not_call_handle_question(self, text, mock_slack_client):
        """_handle_question must NOT be invoked when text is empty."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text=text)
        respond = MagicMock()

        with patch("handlers.shared._handle_question") as mock_hq:
            run_ask(client=mock_slack_client, body=body, respond=respond)
            mock_hq.assert_not_called()


# ---------------------------------------------------------------------------
# Valid text → pipeline
# ---------------------------------------------------------------------------

class TestSlashHandlerPipeline:
    def test_valid_text_calls_handle_question(self, mock_slack_client):
        """Valid text must invoke _handle_question with correct args."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text="What is Python?", channel="C001", user="U123")
        respond = MagicMock()

        with patch("handlers.shared._handle_question") as mock_hq:
            run_ask(client=mock_slack_client, body=body, respond=respond)

            mock_hq.assert_called_once_with(
                mock_slack_client,
                channel="C001",
                thread_ts=None,
                user_id="U123",
                user_text="What is Python?",
            )

    def test_valid_text_does_not_call_respond(self, mock_slack_client):
        """respond() must NOT be called when text is present."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text="What is Python?")
        respond = MagicMock()

        with patch("handlers.shared._handle_question"):
            run_ask(client=mock_slack_client, body=body, respond=respond)
            respond.assert_not_called()

    def test_text_is_stripped(self, mock_slack_client):
        """Surrounding whitespace is stripped before passing to _handle_question."""
        from handlers.slash_handler import run_ask

        body = make_slash_body(text="  What is Python?  ")
        respond = MagicMock()

        with patch("handlers.shared._handle_question") as mock_hq:
            run_ask(client=mock_slack_client, body=body, respond=respond)

            _, kwargs = mock_hq.call_args
            assert kwargs["user_text"] == "What is Python?"
