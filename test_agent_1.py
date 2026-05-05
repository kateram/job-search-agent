# test_agent1.py
import asyncio
from agents.job_analyst import run_job_analyst

async def main():
    url = "https://careers.cookunity.com/jobs/7718683003"
    result = await run_job_analyst(url)
    print(f"Company: {result.company_name}")
    print(f"Role: {result.role_title}")
    print(f"Location: {result.location}")
    print(f"\nRequired skills:")
    for skill in result.required_skills:
        print(f"  - {skill}")
    print(f"\nRed flags:")
    for flag in result.red_flags:
        print(f"  - {flag}")
    print(f"\nCulture signals:")
    for signal in result.culture_signals:
        print(f"  - {signal}")

asyncio.run(main())