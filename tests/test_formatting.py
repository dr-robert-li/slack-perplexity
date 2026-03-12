"""Tests for utils/formatting.py — citation formatter and message splitter."""
import pytest


class TestFormatAnswer:
    """Tests for the format_answer function."""

    def test_format_with_citations(self):
        """Single citation renders as numbered Slack mrkdwn link."""
        from utils.formatting import format_answer

        result = format_answer(
            answer="Hello",
            citations=[{"title": "Page", "url": "https://example.com"}],
        )
        assert result == "Hello\n───\n[1] <https://example.com|Page>"

    def test_format_no_citations(self):
        """Empty citations list appends the 'No web sources' disclaimer."""
        from utils.formatting import format_answer

        result = format_answer(answer="Hello", citations=[])
        assert result == "Hello\n\n_No web sources found for this query_"

    def test_format_multiple_citations(self):
        """Three citations produce [1], [2], [3] numbered entries."""
        from utils.formatting import format_answer

        citations = [
            {"title": "Alpha", "url": "https://alpha.com"},
            {"title": "Beta", "url": "https://beta.com"},
            {"title": "Gamma", "url": "https://gamma.com"},
        ]
        result = format_answer(answer="Multi answer", citations=citations)

        assert "[1] <https://alpha.com|Alpha>" in result
        assert "[2] <https://beta.com|Beta>" in result
        assert "[3] <https://gamma.com|Gamma>" in result
        assert result.startswith("Multi answer\n───\n")


class TestSplitMessage:
    """Tests for the split_message function."""

    def test_split_short_message(self):
        """Message under 3800 chars returns a single-element list."""
        from utils.formatting import split_message

        short = "Hello world"
        result = split_message(short)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == short

    def test_split_long_message(self):
        """Message of 7700 chars returns 3 chunks, each <= 3800 chars."""
        from utils.formatting import split_message

        # 7700 chars — needs 3 chunks (3800 + 3800 + 100)
        long_text = "A" * 7700
        result = split_message(long_text)

        assert len(result) == 3
        for chunk in result:
            assert len(chunk) <= 3800
        # Verify all content is preserved
        assert "".join(result) == long_text
