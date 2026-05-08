import pytest
from unittest.mock import patch, MagicMock
from models.job import JobAnalysis
from agents.critic import run_critic


@pytest.fixture
def sample_job():
    return JobAnalysis(
        company_name="CookUnity",
        role_title="AI Native Engineer",
        location="Toronto, ON",
        required_skills=["Python", "LLMs", "API integration"],
        nice_to_have_skills=["TypeScript"],
        responsibilities=["Build AI growth tools"],
        culture_signals=["fast-paced", "builder mentality"],
        red_flags=["aggressive timeline"],
        raw_text="Full job posting text"
    )


@pytest.mark.asyncio
async def test_run_critic_returns_application_package(sample_job):
    from models.application import ApplicationPackage

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='''{
        "fit_score": 7,
        "fit_score_reasoning": "Strong Python and LLM experience, missing TypeScript",
        "refined_cv_notes": ["Move Zafin AI Observer to top", "Add RAG to skills section"],
        "refined_cover_letter": "Refined cover letter text here",
        "quality_flags": []
    }''')]

    with patch("agents.critic.client.messages.create", return_value=mock_response):
        result = await run_critic(
            job=sample_job,
            cv_notes=["Move Zafin bullet up", "Add LLM agents to skills"],
            cover_letter="Original cover letter text",
            company_brief="CookUnity is a meal delivery platform..."
        )

        assert isinstance(result, ApplicationPackage)
        assert result.fit_score == 7
        assert isinstance(result.cv_notes, list)
        assert isinstance(result.cover_letter, str)
        assert result.status == "To Apply"


@pytest.mark.asyncio
async def test_run_critic_fit_score_within_bounds(sample_job):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='''{
        "fit_score": 9,
        "fit_score_reasoning": "Exceptional match across all requirements",
        "refined_cv_notes": ["Highlight LLM project first"],
        "refined_cover_letter": "Strong cover letter",
        "quality_flags": ["Consider addressing TypeScript gap"]
    }''')]

    with patch("agents.critic.client.messages.create", return_value=mock_response):
        result = await run_critic(
            job=sample_job,
            cv_notes=["Highlight LLM project"],
            cover_letter="Cover letter text",
            company_brief="Company brief text"
        )

        assert 0 <= result.fit_score <= 10


@pytest.mark.asyncio
async def test_run_critic_handles_markdown_wrapped_json(sample_job):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='''```json
{
    "fit_score": 6,
    "fit_score_reasoning": "Partial match",
    "refined_cv_notes": ["Add Python projects"],
    "refined_cover_letter": "Cover letter",
    "quality_flags": ["Missing TypeScript experience"]
}
```''')]

    with patch("agents.critic.client.messages.create", return_value=mock_response):
        result = await run_critic(
            job=sample_job,
            cv_notes=["Add Python projects"],
            cover_letter="Cover letter",
            company_brief="Brief"
        )
        assert result.fit_score == 6
