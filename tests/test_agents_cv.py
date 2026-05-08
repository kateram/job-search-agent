import pytest
from unittest.mock import patch, MagicMock
from models.job import JobAnalysis


@pytest.fixture
def sample_job():
    return JobAnalysis(
        company_name="Acme Corp",
        role_title="AI Engineer",
        location="Toronto, ON",
        required_skills=["Python", "LLMs", "RAG"],
        nice_to_have_skills=["CrewAI"],
        responsibilities=["Build agents", "Deploy pipelines"],
        culture_signals=["fast-paced", "async-first"],
        red_flags=[],
        raw_text="Full job posting text here"
    )


@pytest.mark.asyncio
async def test_cv_advisor_returns_list(sample_job):
    from agents.cv_advisor import run_cv_advisor

    with patch("agents.cv_advisor.retrieve", return_value=["CV chunk 1", "CV chunk 2"]), \
         patch("agents.cv_advisor.client.messages.create") as mock_llm:
        mock_llm.return_value.content = [MagicMock(text='["Move RAG experience higher", "Add LLM agents to skills"]')]
        result = await run_cv_advisor(sample_job)
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(s, str) for s in result)


@pytest.mark.asyncio
async def test_cover_letter_returns_string(sample_job):
    from agents.cover_letter import run_cover_letter

    with patch("agents.cover_letter.retrieve", return_value=["CV chunk 1"]), \
         patch("agents.cover_letter.client.messages.create") as mock_llm:
        mock_llm.return_value.content = [MagicMock(text="Dear Hiring Manager, I am excited...")]
        result = await run_cover_letter(sample_job)
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.asyncio
async def test_cover_letter_handles_missing_cover_letter_collection(sample_job):
    from agents.cover_letter import run_cover_letter

    def mock_retrieve(query, collection_name, n_results):
        if collection_name == "cover_letters":
            raise RuntimeError("Collection not found")
        return ["CV chunk 1"]

    with patch("agents.cover_letter.retrieve", side_effect=mock_retrieve), \
         patch("agents.cover_letter.client.messages.create") as mock_llm:
        mock_llm.return_value.content = [MagicMock(text="Dear Hiring Manager...")]
        result = await run_cover_letter(sample_job)
        assert isinstance(result, str)