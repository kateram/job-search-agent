from anthropic import APIError
from core.llm import client
from core.config import settings
from models.job import JobAnalysis
from tools.scraper import scrape_job_posting, is_blocked_domain
from tools.search import fetch_job_posting_text
import json


SYSTEM_PROMPT = """You are an expert job posting analyst. 
When given a job posting, extract structured information accurately.
Always respond with valid JSON matching the requested schema exactly.
Do not include any text outside the JSON object."""


async def run_job_analyst(url: str) -> JobAnalysis:
    """
    Scrape a job posting URL and extract structured data.
    Returns a JobAnalysis model.
    """
    raw_text = await _fetch_posting(url)
    return await _extract_structure(raw_text)


async def _fetch_posting(url: str) -> str:
    """
    Fetch job posting text from URL.
    Falls back to Tavily if direct scraping fails.
    """
    if is_blocked_domain(url):
        return await fetch_job_posting_text(url)

    try:
        return await scrape_job_posting(url)
    except RuntimeError:
        return await fetch_job_posting_text(url)
    
def _clean_json(raw: str) -> str:         
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


async def _extract_structure(raw_text: str) -> JobAnalysis:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Extract the following from this job posting and return as JSON:

{{
    "company_name": "string",
    "role_title": "string",
    "location": "string",
    "required_skills": ["list of strings"],
    "nice_to_have_skills": ["list of strings"],
    "responsibilities": ["list of strings, max 5"],
    "culture_signals": ["list of strings"],
    "red_flags": ["list of strings"],
}}

Job posting:
{raw_text}"""
            }
        ]
    )

    raw_json = _clean_json(response.content[0].text)

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Claude returned invalid JSON: {raw_json[:200]}"
        )

    data["raw_text"] = raw_text
    return JobAnalysis(**data)