"""Tests for services/perplexity.py — Perplexity service layer."""
from unittest.mock import MagicMock, patch
import pytest


class TestQueryPerplexity:
    """Tests for the query_perplexity function."""

    def test_uses_pro_search(self, mock_perplexity_response):
        """query_perplexity must call responses.create with preset='pro-search'."""
        with patch("services.perplexity.pplx_client") as mock_client:
            mock_client.responses.create.return_value = mock_perplexity_response

            from services.perplexity import query_perplexity
            query_perplexity("test question")

            mock_client.responses.create.assert_called_once_with(
                preset="pro-search", input="test question"
            )

    def test_returns_answer_and_citations(self, mock_perplexity_response):
        """Returns dict with 'answer' string and 'citations' list of {title, url}."""
        with patch("services.perplexity.pplx_client") as mock_client:
            mock_client.responses.create.return_value = mock_perplexity_response

            from services.perplexity import query_perplexity
            result = query_perplexity("test question")

            assert isinstance(result, dict)
            assert "answer" in result
            assert "citations" in result
            assert result["answer"] == "Answer"
            assert isinstance(result["citations"], list)
            assert len(result["citations"]) == 3
            assert result["citations"][0] == {
                "title": "Source One",
                "url": "https://example.com/one",
            }

    def test_max_five_citations(self):
        """When response has 8 search results, only first 5 are returned."""
        # Build a mock response with 8 search results
        response = MagicMock()
        response.output_text = "Big answer"

        results = []
        for i in range(8):
            r = MagicMock()
            r.title = f"Source {i + 1}"
            r.url = f"https://example.com/{i + 1}"
            results.append(r)

        search_results_item = MagicMock()
        search_results_item.type = "search_results"
        search_results_item.results = results
        response.output = [search_results_item]

        with patch("services.perplexity.pplx_client") as mock_client:
            mock_client.responses.create.return_value = response

            from services.perplexity import query_perplexity
            result = query_perplexity("long question")

            assert len(result["citations"]) == 5

    def test_no_search_results(self):
        """When response has no search_results item, citations list is empty."""
        response = MagicMock()
        response.output_text = "Answer without sources"

        # output contains only non-search_results items
        other_item = MagicMock()
        other_item.type = "text"
        response.output = [other_item]

        with patch("services.perplexity.pplx_client") as mock_client:
            mock_client.responses.create.return_value = response

            from services.perplexity import query_perplexity
            result = query_perplexity("question with no sources")

            assert result["citations"] == []

    def test_api_error_raises(self):
        """API errors propagate to caller — function does NOT catch them."""
        with patch("services.perplexity.pplx_client") as mock_client:
            mock_client.responses.create.side_effect = Exception("Connection failed")

            from services.perplexity import query_perplexity
            with pytest.raises(Exception, match="Connection failed"):
                query_perplexity("broken question")

    def test_string_only_passes_string_to_create(self, mock_perplexity_response):
        """query_perplexity('question') passes string input (backward compatible)."""
        with patch("services.perplexity.pplx_client") as mock_client:
            mock_client.responses.create.return_value = mock_perplexity_response

            from services.perplexity import query_perplexity
            query_perplexity("simple question")

            mock_client.responses.create.assert_called_once_with(
                preset="pro-search", input="simple question"
            )

    def test_structured_messages_sent_as_list(self, mock_perplexity_response):
        """query_perplexity with messages sends list input to responses.create."""
        prior_messages = [
            {"type": "message", "role": "user", "content": "prior question"}
        ]
        with patch("services.perplexity.pplx_client") as mock_client:
            mock_client.responses.create.return_value = mock_perplexity_response

            from services.perplexity import query_perplexity
            query_perplexity("follow-up", messages=prior_messages)

            call_kwargs = mock_client.responses.create.call_args
            sent_input = call_kwargs.kwargs["input"]
            assert isinstance(sent_input, list)
            assert sent_input[0] == {"type": "message", "role": "user", "content": "prior question"}
            assert sent_input[-1] == {"type": "message", "role": "user", "content": "follow-up"}

    def test_question_appended_as_final_user_message(self, mock_perplexity_response):
        """When messages provided, question is appended as final user message."""
        prior = [
            {"type": "message", "role": "user", "content": "first"},
            {"type": "message", "role": "assistant", "content": "answer"},
        ]
        with patch("services.perplexity.pplx_client") as mock_client:
            mock_client.responses.create.return_value = mock_perplexity_response

            from services.perplexity import query_perplexity
            query_perplexity("new question", messages=prior)

            call_kwargs = mock_client.responses.create.call_args
            sent_input = call_kwargs.kwargs["input"]
            assert len(sent_input) == 3
            assert sent_input[-1]["role"] == "user"
            assert sent_input[-1]["content"] == "new question"

    def test_none_messages_uses_string_input(self, mock_perplexity_response):
        """query_perplexity with messages=None passes string to responses.create."""
        with patch("services.perplexity.pplx_client") as mock_client:
            mock_client.responses.create.return_value = mock_perplexity_response

            from services.perplexity import query_perplexity
            query_perplexity("question", messages=None)

            call_kwargs = mock_client.responses.create.call_args
            assert call_kwargs.kwargs["input"] == "question"

    def test_empty_messages_uses_string_input(self, mock_perplexity_response):
        """query_perplexity with messages=[] passes string to responses.create."""
        with patch("services.perplexity.pplx_client") as mock_client:
            mock_client.responses.create.return_value = mock_perplexity_response

            from services.perplexity import query_perplexity
            query_perplexity("question", messages=[])

            call_kwargs = mock_client.responses.create.call_args
            assert call_kwargs.kwargs["input"] == "question"

    def test_preset_pro_search_with_structured_input(self, mock_perplexity_response):
        """pro-search preset is used even when messages list is provided."""
        prior = [{"type": "message", "role": "user", "content": "prior"}]
        with patch("services.perplexity.pplx_client") as mock_client:
            mock_client.responses.create.return_value = mock_perplexity_response

            from services.perplexity import query_perplexity
            query_perplexity("question", messages=prior)

            call_kwargs = mock_client.responses.create.call_args
            assert call_kwargs.kwargs["preset"] == "pro-search"
