import asyncio
from models.application import ApplicationPackage
from agents.job_analyst import run_job_analyst
from agents.cv_advisor import run_cv_advisor
from agents.cover_letter import run_cover_letter
from agents.company_intel import run_company_intel
from agents.critic import run_critic
from tools.sheets import write_application


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

    # Agent 1 — sequential, everything depends on this
    job = await run_job_analyst(url=url, raw_text=raw_text)

    # Agents 2, 3, 4 — parallel, independent of each other
    cv_notes, cover_letter, company_brief = await asyncio.gather(
        run_cv_advisor(job),
        run_cover_letter(job),
        run_company_intel(job),
    )

    # Agent 5 — sequential, depends on all three above
    package = await run_critic(job, cv_notes, cover_letter, company_brief)

    # Write to Google Sheets
    await write_application({
        "Company": package.job.company_name,
        "Role": package.job.role_title,
        "Fit Score": package.fit_score,
        "Cover Letter": package.cover_letter,
        "CV Notes": package.cv_notes,
        "Company Brief": package.company_brief,
        "Status": package.status,
        "Created At": package.created_at.isoformat(),
    })

    return package