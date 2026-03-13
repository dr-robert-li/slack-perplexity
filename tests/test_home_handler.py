"""Unit tests for App Home tab handler."""
from unittest.mock import MagicMock, patch
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_home_event(user="U123"):
    return {"user": user}


# ---------------------------------------------------------------------------
# views_publish called correctly
# ---------------------------------------------------------------------------

class TestHomeHandler:
    def test_publishes_home_view(self, mock_slack_client):
        """views_publish must be called with the user_id from the event."""
        from handlers.home_handler import handle_app_home_opened

        event = make_home_event(user="U456")
        logger = MagicMock()
        handle_app_home_opened(client=mock_slack_client, event=event, logger=logger)

        mock_slack_client.views_publish.assert_called_once()
        call_kwargs = mock_slack_client.views_publish.call_args.kwargs
        assert call_kwargs["user_id"] == "U456"

    def test_view_type_is_home(self, mock_slack_client):
        """Published view must have type 'home'."""
        from handlers.home_handler import handle_app_home_opened

        event = make_home_event()
        logger = MagicMock()
        handle_app_home_opened(client=mock_slack_client, event=event, logger=logger)

        view = mock_slack_client.views_publish.call_args.kwargs["view"]
        assert view["type"] == "home"

    def test_view_has_non_empty_blocks(self, mock_slack_client):
        """Published view must have at least one block."""
        from handlers.home_handler import handle_app_home_opened

        event = make_home_event()
        logger = MagicMock()
        handle_app_home_opened(client=mock_slack_client, event=event, logger=logger)

        view = mock_slack_client.views_publish.call_args.kwargs["view"]
        assert isinstance(view["blocks"], list)
        assert len(view["blocks"]) > 0


# ---------------------------------------------------------------------------
# Content verification — all 4 interaction methods documented
# ---------------------------------------------------------------------------

class TestHomeHandlerContent:
    def _get_all_text(self, view: dict) -> str:
        """Flatten all text values from blocks into one string."""
        parts = []
        for block in view.get("blocks", []):
            text_obj = block.get("text", {})
            if isinstance(text_obj, dict):
                parts.append(text_obj.get("text", ""))
            elif isinstance(text_obj, str):
                parts.append(text_obj)
            # Also check accessory / fields
            for field in block.get("fields", []):
                if isinstance(field, dict):
                    parts.append(field.get("text", ""))
        return " ".join(parts)

    def test_blocks_mention_dm(self, mock_slack_client):
        """Blocks must mention direct message / DM usage."""
        from handlers.home_handler import handle_app_home_opened

        event = make_home_event()
        logger = MagicMock()
        handle_app_home_opened(client=mock_slack_client, event=event, logger=logger)

        view = mock_slack_client.views_publish.call_args.kwargs["view"]
        all_text = self._get_all_text(view).lower()
        assert "dm" in all_text or "direct message" in all_text

    def test_blocks_mention_at_mention(self, mock_slack_client):
        """Blocks must mention @mention usage."""
        from handlers.home_handler import handle_app_home_opened

        event = make_home_event()
        logger = MagicMock()
        handle_app_home_opened(client=mock_slack_client, event=event, logger=logger)

        view = mock_slack_client.views_publish.call_args.kwargs["view"]
        all_text = self._get_all_text(view)
        assert "@mention" in all_text or "@" in all_text

    def test_blocks_mention_slash_ask(self, mock_slack_client):
        """Blocks must mention the /ask command."""
        from handlers.home_handler import handle_app_home_opened

        event = make_home_event()
        logger = MagicMock()
        handle_app_home_opened(client=mock_slack_client, event=event, logger=logger)

        view = mock_slack_client.views_publish.call_args.kwargs["view"]
        all_text = self._get_all_text(view)
        assert "/ask" in all_text

    def test_blocks_mention_group_dm(self, mock_slack_client):
        """Blocks must mention group DM usage."""
        from handlers.home_handler import handle_app_home_opened

        event = make_home_event()
        logger = MagicMock()
        handle_app_home_opened(client=mock_slack_client, event=event, logger=logger)

        view = mock_slack_client.views_publish.call_args.kwargs["view"]
        all_text = self._get_all_text(view).lower()
        assert "group dm" in all_text or "group direct message" in all_text or "group" in all_text


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestHomeHandlerError:
    def test_views_publish_exception_is_caught(self, mock_slack_client):
        """Exception from views_publish must be caught — must not propagate."""
        from handlers.home_handler import handle_app_home_opened

        mock_slack_client.views_publish.side_effect = Exception("Slack API error")
        event = make_home_event()
        logger = MagicMock()

        # Should not raise
        handle_app_home_opened(client=mock_slack_client, event=event, logger=logger)

    def test_views_publish_exception_is_logged(self, mock_slack_client):
        """Exception from views_publish must be logged via logger.error."""
        from handlers.home_handler import handle_app_home_opened

        mock_slack_client.views_publish.side_effect = Exception("Slack API error")
        event = make_home_event()
        logger = MagicMock()

        handle_app_home_opened(client=mock_slack_client, event=event, logger=logger)

        logger.error.assert_called()
