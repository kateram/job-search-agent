import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from core.pipeline import run_pipeline
from models.job import JobAnalysis
from models.application import ApplicationPackage
from datetime import datetime, timezone


@pytest.fixture
def sample_job():
    return JobAnalysis(
        company_name="Acme Corp",
        role_title="AI Engineer",
        location="Toronto, ON",
        required_skills=["Python", "LLMs"],
        nice_to_have_skills=[],
        responsibilities=["Build agents"],
        culture_signals=["fast-paced"],
        red_flags=[],
        raw_text="Full job posting text"
    )


@pytest.fixture
def sample_package(sample_job):
    return ApplicationPackage(
        job=sample_job,
        fit_score=7,
        cv_notes=["Move Zafin to top"],
        cover_letter="Cover letter text",
        company_brief="Company brief text",
        status="To Apply",
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_pipeline_raises_with_no_input():
    with pytest.raises(ValueError, match="Must provide either a URL or raw_text"):
        await run_pipeline()


@pytest.mark.asyncio
async def test_pipeline_returns_application_package(sample_job, sample_package):
    with patch("core.pipeline.run_job_analyst", new_callable=AsyncMock) as mock_analyst, \
         patch("core.pipeline.run_cv_advisor", new_callable=AsyncMock) as mock_cv, \
         patch("core.pipeline.run_cover_letter", new_callable=AsyncMock) as mock_letter, \
         patch("core.pipeline.run_company_intel", new_callable=AsyncMock) as mock_intel, \
         patch("core.pipeline.run_critic", new_callable=AsyncMock) as mock_critic, \
         patch("core.pipeline.write_application", new_callable=AsyncMock) as mock_sheets:

        mock_analyst.return_value = sample_job
        mock_cv.return_value = ["Move Zafin to top"]
        mock_letter.return_value = "Cover letter text"
        mock_intel.return_value = "Company brief text"
        mock_critic.return_value = sample_package
        mock_sheets.return_value = "Row appended successfully"

        result = await run_pipeline(raw_text="some job posting text")

        assert isinstance(result, ApplicationPackage)
        assert result.fit_score == 7
        mock_analyst.assert_called_once()
        mock_critic.assert_called_once()
        mock_sheets.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_agents_called_with_correct_inputs(sample_job, sample_package):
    with patch("core.pipeline.run_job_analyst", new_callable=AsyncMock) as mock_analyst, \
         patch("core.pipeline.run_cv_advisor", new_callable=AsyncMock) as mock_cv, \
         patch("core.pipeline.run_cover_letter", new_callable=AsyncMock) as mock_letter, \
         patch("core.pipeline.run_company_intel", new_callable=AsyncMock) as mock_intel, \
         patch("core.pipeline.run_critic", new_callable=AsyncMock) as mock_critic, \
         patch("core.pipeline.write_application", new_callable=AsyncMock):

        mock_analyst.return_value = sample_job
        mock_cv.return_value = ["note"]
        mock_letter.return_value = "letter"
        mock_intel.return_value = "brief"
        mock_critic.return_value = sample_package

        await run_pipeline(url="https://boards.greenhouse.io/test")

        # Agent 1 called with URL
        mock_analyst.assert_called_once_with(url="https://boards.greenhouse.io/test", raw_text=None)

        # Agents 2-4 called with the job object
        mock_cv.assert_called_once_with(sample_job)
        mock_letter.assert_called_once_with(sample_job)
        mock_intel.assert_called_once_with(sample_job)

        # Agent 5 called with all three outputs
        mock_critic.assert_called_once_with(sample_job, ["note"], "letter", "brief")