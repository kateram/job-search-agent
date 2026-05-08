# test_agents23.py
import asyncio
from agents.job_analyst import run_job_analyst
from agents.cv_advisor import run_cv_advisor
from agents.cover_letter import run_cover_letter

URL = "https://careers.cookunity.com/jobs/7718683003"

async def main():
    print("Running Job Analyst...")
    job = await run_job_analyst(url=URL)
    print(f"Company: {job.company_name} | Role: {job.role_title}")

    print("\nRunning CV Advisor...")
    cv_notes = await run_cv_advisor(job)
    print("\nCV Suggestions:")
    for note in cv_notes:
        print(f"  - {note}")

    print("\nRunning Cover Letter...")
    letter = await run_cover_letter(job)
    print("\nCover Letter:")
    print(letter)

asyncio.run(main())