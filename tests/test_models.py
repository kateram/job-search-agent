from models.job import JobAnalysis
from models.application import ApplicationPackage
from datetime import datetime

def test_job_analysis_valid():
    job = JobAnalysis(
        company_name="Acme Corp",
        role_title="AI Engineer",
        location="Remote",
        required_skills=["Python", "LangChain"],
        nice_to_have_skills=["CrewAI"],
        responsibilities=["Build agents"],
        culture_signals=["async-first"],
        red_flags=[],
        raw_text="Full job posting text here..."
    )
    assert job.company_name == "Acme Corp"
    assert isinstance(job.required_skills, list)

def test_fit_score_bounds():
    # fit_score must be 0–10
    import pytest
    with pytest.raises(Exception):
        ApplicationPackage(
            job=...,        # fill with a valid JobAnalysis
            fit_score=11,   # should fail validation
            cv_notes=[],
            cover_letter="",
            company_brief=""
        )