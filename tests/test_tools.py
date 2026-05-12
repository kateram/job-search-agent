import pytest
from tools.scraper import is_blocked_domain, scrape_job_posting
from unittest.mock import patch, MagicMock
from tools.search import search_web, fetch_job_posting_text


def test_blocked_domain_detection():
    assert is_blocked_domain("https://www.linkedin.com/jobs/view/123") is True
    assert is_blocked_domain("https://www.indeed.com/viewjob?jk=abc") is True
    assert is_blocked_domain("https://jobs.lever.co/acme/software-engineer") is False


@pytest.mark.asyncio
async def test_scrape_raises_on_blocked_domain():
    with pytest.raises(ValueError, match="Direct scraping not supported"):
        await scrape_job_posting("https://www.linkedin.com/jobs/view/123")

@pytest.mark.asyncio
async def test_search_web_returns_list():
    mock_response = {
        "results": [
            {"url": "https://example.com", "title": "Example", "content": "Some content"}
        ]
    }
    with patch("tools.search.client.search", return_value=mock_response):
        results = await search_web("test query")
        assert isinstance(results, list)
        assert results[0]["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_fetch_job_posting_raises_on_empty():
    with patch("tools.search.client.extract", return_value={"results": []}):
        with pytest.raises(RuntimeError, match="Tavily could not extract"):
            await fetch_job_posting_text("https://linkedin.com/jobs/123")
