"""Shared pytest fixtures for the Kahm-pew-terr Slack bot tests."""
from unittest.mock import MagicMock
import pytest


@pytest.fixture
def mock_perplexity_response():
    """Mock Perplexity API response with output_text and search results."""
    response = MagicMock()
    response.output_text = "Answer"

    # Create 3 mock search result entries
    result_1 = MagicMock()
    result_1.title = "Source One"
    result_1.url = "https://example.com/one"

    result_2 = MagicMock()
    result_2.title = "Source Two"
    result_2.url = "https://example.com/two"

    result_3 = MagicMock()
    result_3.title = "Source Three"
    result_3.url = "https://example.com/three"

    # Create a mock search_results output item
    search_results_item = MagicMock()
    search_results_item.type = "search_results"
    search_results_item.results = [result_1, result_2, result_3]

    response.output = [search_results_item]
    return response


@pytest.fixture
def mock_slack_client():
    """Mock Slack WebClient with common methods."""
    client = MagicMock()
    client.chat_postMessage.return_value = {"ts": "1234.5678"}
    client.chat_update.return_value = {"ok": True}
    return client
