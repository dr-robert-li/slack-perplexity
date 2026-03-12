"""Perplexity service layer — wraps the Perplexity SDK for pro-search queries."""
import os
from perplexity import Perplexity

# Module-level client — reads PERPLEXITY_API_KEY from environment automatically.
# api_key defaults to "placeholder" so imports don't crash in test environments
# where the env var is absent; patching pplx_client replaces this before any call.
pplx_client = Perplexity(api_key=os.environ.get("PERPLEXITY_API_KEY", "placeholder"))


def query_perplexity(question: str) -> dict:
    """Query Perplexity using the pro-search preset and extract citations.

    Args:
        question: The question to ask Perplexity.

    Returns:
        A dict with:
            - "answer": str — the response text
            - "citations": list[dict] — up to 5 sources, each with "title" and "url"

    Raises:
        Any Perplexity SDK exceptions propagate to the caller unchanged.
    """
    response = pplx_client.responses.create(preset="pro-search", input=question)

    answer = response.output_text

    citations = []
    for item in response.output:
        if item.type == "search_results":
            for result in item.results[:5]:
                citations.append({"title": result.title, "url": result.url})
            break  # Only process the first search_results block

    return {"answer": answer, "citations": citations}
