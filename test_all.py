# test_pipeline.py
import asyncio
from agents.job_analyst import run_job_analyst
from agents.cv_advisor import run_cv_advisor
from agents.cover_letter import run_cover_letter
from agents.company_intel import run_company_intel
from agents.critic import run_critic

URL = "https://careers.cookunity.com/jobs/7718683003"

async def main():
    print("\n=== Agent 1: Job Analyst ===")
    job = await run_job_analyst(url=URL)
    print(f"Company: {job.company_name} | Role: {job.role_title}")

    print("\n=== Agents 2, 3, 4: Running in parallel ===")
    import asyncio
    cv_notes, cover_letter, company_brief = await asyncio.gather(
        run_cv_advisor(job),
        run_cover_letter(job),
        run_company_intel(job),
    )
    print("CV Advisor done")
    print("Cover Letter done")
    print("Company Intel done")

    print("\n=== Agent 5: Critic ===")
    package = await run_critic(job, cv_notes, cover_letter, company_brief)

    print(f"\nFit Score: {package.fit_score}/10")
    print(f"\nCV Notes:")
    for note in package.cv_notes:
        print(f"  - {note}")
    print(f"\nCover Letter:\n{package.cover_letter}")
    print(f"\nCompany Brief:\n{package.company_brief}")

asyncio.run(main())