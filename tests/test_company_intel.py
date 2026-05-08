import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from models.job import JobAnalysis
from agents.company_intel import run_company_intel, _search_company, _format_search_results


@pytest.fixture
def sample_job():
    return JobAnalysis(
        company_name="CookUnity",
        role_title="AI Native Engineer",
        location="Toronto, ON",
        required_skills=["Python", "LLMs"],
        nice_to_have_skills=[],
        responsibilities=["Build AI tools"],
        culture_signals=["fast-paced"],
        red_flags=[],
        raw_text="Full job posting text"
    )


@pytest.mark.asyncio
async def test_run_company_intel_returns_string(sample_job):
    mock_results = [
        {"title": "CookUnity Overview", "content": "CookUnity is a meal delivery platform..."},
        {"title": "CookUnity Funding", "content": "CookUnity raised $100M in Series C..."},
    ]

    with patch("agents.company_intel.search_web", new_callable=AsyncMock) as mock_search, \
         patch("agents.company_intel.client.messages.create") as mock_llm:
        mock_search.return_value = mock_results
        mock_llm.return_value.content = [MagicMock(text="CookUnity is a meal delivery platform connecting chefs with customers.")]

        result = await run_company_intel(sample_job)
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.asyncio
async def test_run_company_intel_handles_empty_results(sample_job):
    with patch("agents.company_intel.search_web", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = []
        result = await run_company_intel(sample_job)
        assert "No web results found" in result


def test_format_search_results_filters_empty_content():
    results = [
        {"title": "Good result", "content": "Some content here"},
        {"title": "Empty result", "content": ""},
        {"title": "Another good one", "content": "More content"},
    ]
    formatted = _format_search_results(results)
    assert "Good result" in formatted
    assert "Empty result" not in formatted
    assert "Another good one" in formatted