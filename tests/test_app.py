"""Tests for app.py — Slack Bolt app initialization."""
import sys
from unittest.mock import MagicMock, patch


class TestAppInitializes:
    """Tests for the Slack Bolt app object initialization."""

    def test_app_initializes(self):
        """App object can be imported from app module with mocked env vars."""
        from slack_bolt import App

        # Remove cached app module if previously imported
        if "app" in sys.modules:
            del sys.modules["app"]

        fake_env = {
            "SLACK_BOT_TOKEN": "xoxb-fake-token",
            "SLACK_APP_TOKEN": "xapp-fake-token",
            "PERPLEXITY_API_KEY": "placeholder",
        }

        # Mock the WebClient's auth_test so Bolt doesn't make a real API call
        mock_auth_result = {"ok": True, "bot_id": "BTEST", "team_id": "TTEST"}

        with patch.dict("os.environ", fake_env, clear=False), \
             patch("slack_sdk.web.client.WebClient.auth_test", return_value=mock_auth_result):
            import app as app_module

        assert isinstance(app_module.app, App)
