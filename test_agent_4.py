# test_agent4.py
import asyncio
from agents.job_analyst import run_job_analyst
from agents.company_intel import run_company_intel

URL = "https://careers.cookunity.com/jobs/7718683003"

async def main():
    print("Running Job Analyst...")
    job = await run_job_analyst(url=URL)
    print(f"Company: {job.company_name} | Role: {job.role_title}")

    print("\nRunning Company Intel...")
    brief = await run_company_intel(job)
    print("\nCompany Brief:")
    print(brief)

asyncio.run(main())