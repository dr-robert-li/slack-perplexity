"""Tests for services/context.py — UID resolution, history fetching, config."""
from unittest.mock import MagicMock, patch, call
import pytest


class TestConfig:
    """Tests for HISTORY_DEPTH and MSG_TRUNCATE_LENGTH config constants."""

    def test_history_depth_default(self):
        """HISTORY_DEPTH defaults to 10 when env var is absent."""
        with patch.dict("os.environ", {}, clear=False):
            # Remove the key if present, then reimport
            import os
            env_backup = os.environ.pop("HISTORY_DEPTH", None)
            try:
                import importlib
                import services.context
                importlib.reload(services.context)
                assert services.context.HISTORY_DEPTH == 10
            finally:
                if env_backup is not None:
                    os.environ["HISTORY_DEPTH"] = env_backup
                importlib.reload(services.context)

    def test_history_depth_from_env(self):
        """HISTORY_DEPTH is overridden by HISTORY_DEPTH env var."""
        import importlib
        with patch.dict("os.environ", {"HISTORY_DEPTH": "20"}):
            import services.context
            importlib.reload(services.context)
            assert services.context.HISTORY_DEPTH == 20
        importlib.reload(services.context)

    def test_msg_truncate_length_default(self):
        """MSG_TRUNCATE_LENGTH defaults to 500 when env var is absent."""
        import os
        import importlib
        env_backup = os.environ.pop("MSG_TRUNCATE_LENGTH", None)
        try:
            import services.context
            importlib.reload(services.context)
            assert services.context.MSG_TRUNCATE_LENGTH == 500
        finally:
            if env_backup is not None:
                os.environ["MSG_TRUNCATE_LENGTH"] = env_backup
            importlib.reload(services.context)

    def test_msg_truncate_length_from_env(self):
        """MSG_TRUNCATE_LENGTH is overridden by MSG_TRUNCATE_LENGTH env var."""
        import importlib
        with patch.dict("os.environ", {"MSG_TRUNCATE_LENGTH": "200"}):
            import services.context
            importlib.reload(services.context)
            assert services.context.MSG_TRUNCATE_LENGTH == 200
        importlib.reload(services.context)


class TestResolveUids:
    """Tests for resolve_uids()."""

    def _make_user_response(self, display_name="", real_name=""):
        """Build a mock client.users_info response."""
        resp = MagicMock()
        resp.__getitem__ = lambda self, key: {
            "user": {
                "profile": {"display_name": display_name},
                "real_name": real_name,
            }
        }[key]
        return resp

    def test_no_uids_unchanged(self):
        """resolve_uids returns unchanged string when no UID tags present."""
        from services.context import resolve_uids
        client = MagicMock()
        result = resolve_uids("Hello world", client)
        assert result == "Hello world"
        client.users_info.assert_not_called()

    def test_single_uid_resolved(self):
        """resolve_uids replaces <@UID> with display_name from Slack API."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import resolve_uids

        client = MagicMock()
        client.users_info.return_value = {
            "user": {
                "profile": {"display_name": "Robert Li"},
                "real_name": "Robert Li Real",
            }
        }

        result = resolve_uids("Hello <@U123>", client)
        assert result == "Hello Robert Li"

    def test_multiple_uids_resolved(self):
        """resolve_uids replaces multiple <@UID> tags in a single string."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import resolve_uids

        client = MagicMock()

        def users_info_side_effect(user):
            if user == "U123":
                return {
                    "user": {
                        "profile": {"display_name": "Robert Li"},
                        "real_name": "Robert Li Real",
                    }
                }
            elif user == "U456":
                return {
                    "user": {
                        "profile": {"display_name": "Jane Doe"},
                        "real_name": "Jane Doe Real",
                    }
                }

        client.users_info.side_effect = users_info_side_effect

        result = resolve_uids("Hello <@U123> and <@U456>", client)
        assert result == "Hello Robert Li and Jane Doe"

    def test_fallback_to_real_name_when_display_empty(self):
        """resolve_uids falls back to real_name when display_name is empty string."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import resolve_uids

        client = MagicMock()
        client.users_info.return_value = {
            "user": {
                "profile": {"display_name": ""},
                "real_name": "Robert Li Real",
            }
        }

        result = resolve_uids("Hello <@U999>", client)
        assert result == "Hello Robert Li Real"

    def test_unknown_uid_keeps_raw_tag(self):
        """resolve_uids leaves <@UBAD> as-is when API raises an exception."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import resolve_uids

        client = MagicMock()
        client.users_info.side_effect = Exception("User not found")

        result = resolve_uids("Hello <@UBAD>", client)
        assert result == "Hello <@UBAD>"

    def test_uid_cache_prevents_duplicate_calls(self):
        """resolve_uids does NOT call users_info a second time for the same UID."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import resolve_uids

        client = MagicMock()
        client.users_info.return_value = {
            "user": {
                "profile": {"display_name": "Cached User"},
                "real_name": "Cached User Real",
            }
        }

        resolve_uids("First call <@UCACHE>", client)
        resolve_uids("Second call <@UCACHE>", client)

        # users_info must have been called exactly once total for UCACHE
        assert client.users_info.call_count == 1


class TestFetchThreadHistory:
    """Tests for fetch_thread_history()."""

    def _make_msg(self, ts, user="UOTHER", text="Hello", bot_id=None):
        msg = {"ts": ts, "text": text, "user": user}
        if bot_id:
            msg["bot_id"] = bot_id
        return msg

    def test_returns_structured_dicts(self):
        """fetch_thread_history returns list of {role, content, type} dicts."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import fetch_thread_history

        client = MagicMock()
        client.conversations_replies.return_value = {
            "messages": [
                {"ts": "1000.0", "text": "First", "user": "UOTHER"},
                {"ts": "2000.0", "text": "Current", "user": "UOTHER"},
            ]
        }

        result = fetch_thread_history(client, "C123", "1000.0", "2000.0", "UBOT")
        assert isinstance(result, list)
        for item in result:
            assert "role" in item
            assert "content" in item
            assert "type" in item
            assert item["type"] == "message"

    def test_excludes_current_message(self):
        """fetch_thread_history excludes the message with ts == current_ts."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import fetch_thread_history

        client = MagicMock()
        client.conversations_replies.return_value = {
            "messages": [
                {"ts": "1000.0", "text": "Prior message", "user": "UOTHER"},
                {"ts": "2000.0", "text": "Current trigger", "user": "UOTHER"},
            ]
        }

        result = fetch_thread_history(client, "C123", "1000.0", "2000.0", "UBOT")
        texts = [m["content"] for m in result]
        assert "Current trigger" not in texts
        assert "Prior message" in texts

    def test_bot_messages_are_assistant_role(self):
        """fetch_thread_history assigns role='assistant' to messages from bot_user_id."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import fetch_thread_history

        client = MagicMock()
        client.conversations_replies.return_value = {
            "messages": [
                {"ts": "1000.0", "text": "Bot reply", "user": "UBOT"},
                {"ts": "2000.0", "text": "Current", "user": "UOTHER"},
            ]
        }

        result = fetch_thread_history(client, "C123", "1000.0", "2000.0", "UBOT")
        assert result[0]["role"] == "assistant"

    def test_user_messages_are_user_role(self):
        """fetch_thread_history assigns role='user' to non-bot messages."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import fetch_thread_history

        client = MagicMock()
        client.conversations_replies.return_value = {
            "messages": [
                {"ts": "1000.0", "text": "User message", "user": "UOTHER"},
                {"ts": "2000.0", "text": "Current", "user": "UOTHER"},
            ]
        }

        result = fetch_thread_history(client, "C123", "1000.0", "2000.0", "UBOT")
        assert result[0]["role"] == "user"

    def test_truncates_long_messages(self):
        """fetch_thread_history truncates messages longer than MSG_TRUNCATE_LENGTH."""
        import importlib
        import services.context
        importlib.reload(services.context)

        long_text = "x" * 600
        from services.context import fetch_thread_history

        client = MagicMock()
        client.conversations_replies.return_value = {
            "messages": [
                {"ts": "1000.0", "text": long_text, "user": "UOTHER"},
                {"ts": "2000.0", "text": "Current", "user": "UOTHER"},
            ]
        }

        result = fetch_thread_history(client, "C123", "1000.0", "2000.0", "UBOT")
        assert result[0]["content"].endswith("...")
        assert len(result[0]["content"]) == services.context.MSG_TRUNCATE_LENGTH + 3

    def test_returns_empty_on_api_failure(self):
        """fetch_thread_history returns [] when API call raises an exception."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import fetch_thread_history

        client = MagicMock()
        client.conversations_replies.side_effect = Exception("API error")

        result = fetch_thread_history(client, "C123", "1000.0", "2000.0", "UBOT")
        assert result == []


class TestFetchChannelHistory:
    """Tests for fetch_channel_history()."""

    def test_returns_structured_dicts(self):
        """fetch_channel_history returns list of {role, content, type} dicts."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import fetch_channel_history

        client = MagicMock()
        client.conversations_history.return_value = {
            "messages": [
                {"ts": "1000.0", "text": "Message A", "user": "UOTHER"},
                {"ts": "2000.0", "text": "Message B", "user": "UOTHER"},
            ]
        }

        result = fetch_channel_history(client, "C123", "UBOT")
        assert isinstance(result, list)
        for item in result:
            assert "role" in item
            assert "content" in item
            assert item["type"] == "message"

    def test_returns_chronological_order(self):
        """fetch_channel_history reverses newest-first API response to oldest-first."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import fetch_channel_history

        client = MagicMock()
        # API returns newest first
        client.conversations_history.return_value = {
            "messages": [
                {"ts": "3000.0", "text": "Newest", "user": "UOTHER"},
                {"ts": "2000.0", "text": "Middle", "user": "UOTHER"},
                {"ts": "1000.0", "text": "Oldest", "user": "UOTHER"},
            ]
        }

        result = fetch_channel_history(client, "C123", "UBOT")
        texts = [m["content"] for m in result]
        assert texts == ["Oldest", "Middle", "Newest"]

    def test_respects_history_depth_limit(self):
        """fetch_channel_history requests at most HISTORY_DEPTH messages."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import fetch_channel_history

        client = MagicMock()
        client.conversations_history.return_value = {"messages": []}

        fetch_channel_history(client, "C123", "UBOT")

        client.conversations_history.assert_called_once_with(
            channel="C123", limit=services.context.HISTORY_DEPTH
        )

    def test_returns_empty_on_api_failure(self):
        """fetch_channel_history returns [] when API call raises an exception."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import fetch_channel_history

        client = MagicMock()
        client.conversations_history.side_effect = Exception("Network error")

        result = fetch_channel_history(client, "C123", "UBOT")
        assert result == []

    def test_bot_messages_are_assistant_role(self):
        """fetch_channel_history assigns role='assistant' to bot messages."""
        import importlib
        import services.context
        importlib.reload(services.context)
        from services.context import fetch_channel_history

        client = MagicMock()
        client.conversations_history.return_value = {
            "messages": [
                {"ts": "1000.0", "text": "Bot response", "user": "UBOT"},
            ]
        }

        result = fetch_channel_history(client, "C123", "UBOT")
        assert result[0]["role"] == "assistant"
