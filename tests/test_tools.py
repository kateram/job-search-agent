import pytest
from tools.scraper import is_blocked_domain, scrape_job_posting
from unittest.mock import patch, MagicMock
from tools.search import search_web, fetch_job_posting_text
from tools.sheets import write_application, get_existing_applications


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


# TESTING GOOGLE SHEETS ACCESS

@pytest.mark.asyncio
async def test_write_application_returns_success():
    with patch("tools.sheets._get_worksheet") as mock_ws:
        mock_ws.return_value.append_row = MagicMock()
        result = await write_application({
            "company_name": "Acme",
            "role_title": "AI Engineer",
            "fit_score": 8,
            "cover_letter": "Dear hiring manager...",
            "cv_notes": ["Reorder bullet 2"],
            "company_brief": "Acme is a fast-growing startup...",
            "status": "To Apply",
            "created_at": "2026-01-01T00:00:00Z",
        })
        assert "success" in result.lower()


@pytest.mark.asyncio
async def test_get_existing_applications_returns_list():
    with patch("tools.sheets._get_worksheet") as mock_ws:
        mock_ws.return_value.get_all_records.return_value = [
            {"Company": "Acme", "Role": "AI Engineer"}
        ]
        results = await get_existing_applications("Acme")
        assert isinstance(results, list)
        assert results[0]["Company"] == "Acme"