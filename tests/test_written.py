import pytest
from unittest.mock import patch, MagicMock
from models.job import JobAnalysis
from agents.written_sections import generate_section, regenerate_section


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


@pytest.fixture
def sample_chunks():
    return [
        "Built AI Observer at Zafin using OpenAI API",
        "Led team of 50 staff at CNE",
    ]


@pytest.mark.asyncio
async def test_generate_section_returns_string(sample_job, sample_chunks):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(
        text="At Zafin I built an AI evaluation system that analysed conversation history..."
    )]

    with patch("agents.written_sections.client.messages.create", return_value=mock_response):
        result = await generate_section(
            question="Describe a time you built an AI system to solve a business problem.",
            job=sample_job,
            cv_chunks=sample_chunks,
        )
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.asyncio
async def test_regenerate_section_returns_string(sample_job, sample_chunks):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Revised answer here...")]

    with patch("agents.written_sections.client.messages.create", return_value=mock_response):
        result = await regenerate_section(
            question="Describe a time you built an AI system.",
            current_answer="Original answer text.",
            feedback="Be more specific about the technical implementation.",
            job=sample_job,
            cv_chunks=sample_chunks,
        )
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_section_uses_job_context(sample_job, sample_chunks):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Answer text")]

    with patch("agents.written_sections.client.messages.create", return_value=mock_response) as mock_create:
        await generate_section(
            question="Why do you want to work at this company?",
            job=sample_job,
            cv_chunks=sample_chunks,
        )
        call_args = mock_create.call_args
        prompt = call_args[1]["messages"][0]["content"]
        assert "CookUnity" in prompt
        assert "AI Native Engineer" in prompt