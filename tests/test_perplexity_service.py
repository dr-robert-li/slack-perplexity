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
