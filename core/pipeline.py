import asyncio
from models.application import ApplicationPackage
from agents.job_analyst import run_job_analyst
from agents.cv_advisor import run_cv_advisor
from agents.cover_letter import run_cover_letter
from agents.company_intel import run_company_intel
from agents.critic import run_critic
from tools.storage import save_application, init_db


async def run_pipeline(
    url: str = None,
    raw_text: str = None,
) -> ApplicationPackage:
    """
    Run the full five-agent job application pipeline.
    Accepts either a job posting URL or raw pasted text.
    Returns a completed ApplicationPackage.
    """
    if not url and not raw_text:
        raise ValueError("Must provide either a URL or raw_text")

    init_db()

    job = await run_job_analyst(url=url, raw_text=raw_text)

    cv_notes, cover_letter, company_brief = await asyncio.gather(
        run_cv_advisor(job),
        run_cover_letter(job),
        run_company_intel(job),
    )

    package = await run_critic(job, cv_notes, cover_letter, company_brief)

    save_application({
        "company_name": package.job.company_name,
        "role_title": package.job.role_title,
        "location": package.job.location,
        "fit_score": package.fit_score,
        "cover_letter": package.cover_letter,
        "cv_notes": package.cv_notes,
        "company_brief": package.company_brief,
        "quality_flags": package.quality_flags,
        "red_flags": package.job.red_flags,
        "required_skills": package.job.required_skills,
        "raw_text": package.job.raw_text,
        "status": package.status,
    })

    return package