import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from agents.job_analyst import run_job_analyst, _fetch_posting, _extract_structure


@pytest.mark.asyncio
async def test_fetch_posting_uses_tavily_for_blocked_domain():
    with patch("agents.job_analyst.fetch_job_posting_text", new_callable=AsyncMock) as mock_tavily:
        mock_tavily.return_value = "job posting text"
        result = await _fetch_posting("https://www.linkedin.com/jobs/123")
        mock_tavily.assert_called_once()
        assert result == "job posting text"


@pytest.mark.asyncio
async def test_fetch_posting_falls_back_to_tavily_on_scrape_failure():
    with patch("agents.job_analyst.scrape_job_posting", new_callable=AsyncMock) as mock_scrape, \
         patch("agents.job_analyst.fetch_job_posting_text", new_callable=AsyncMock) as mock_tavily:
        mock_scrape.side_effect = RuntimeError("403 error")
        mock_tavily.return_value = "job posting text"
        result = await _fetch_posting("https://somecompany.com/jobs/123")
        mock_tavily.assert_called_once()
        assert result == "job posting text"


@pytest.mark.asyncio
async def test_extract_structure_returns_job_analysis():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='''{
        "company_name": "Acme Corp",
        "role_title": "AI Engineer",
        "location": "Toronto, ON",
        "required_skills": ["Python", "LLMs"],
        "nice_to_have_skills": ["CrewAI"],
        "responsibilities": ["Build agents"],
        "culture_signals": ["fast-paced"],
        "red_flags": [],
        "raw_text": "full posting text"
    }''')]

    with patch("agents.job_analyst.client.messages.create", return_value=mock_response):
        from models.job import JobAnalysis
        result = await _extract_structure("some job posting text")
        assert isinstance(result, JobAnalysis)
        assert result.company_name == "Acme Corp"
        assert "Python" in result.required_skills