from core.llm import client
from models.job import JobAnalysis
from tools.search import search_web


SYSTEM_PROMPT = """You are a research analyst helping a job candidate prepare for an application.
Given web search results about a company, write a concise, factual company brief.
Only include information present in the search results — do not invent or assume anything.
Be direct and useful. The candidate wants to know things that actually matter for their application.
Return only the brief, no preamble abd NO MARKDOWN."""


async def run_company_intel(job: JobAnalysis) -> str:
    """
    Search the web for intel on the company and return a concise brief.
    """
    results = await _search_company(job.company_name)
    return await _synthesise_brief(job, results)


async def _search_company(company_name: str) -> list[dict]:
    """
    Run multiple targeted searches to build a complete picture.
    """
    queries = [
        f"{company_name} company overview funding growth 2024 2025",
        f"{company_name} layoffs problems challenges news 2024 2025",
        f"{company_name} engineering culture tech stack",
        f"{company_name} reddit employees culture experience",     
        f"{company_name} glassdoor reviews rating 2024 2025",
    ]

    all_results = []
    for query in queries:
        results = await search_web(query, max_results=2)
        all_results.extend(results)

    return all_results


def _format_search_results(results: list[dict]) -> str:
    """Format search results into readable context for the LLM."""
    formatted = []
    for r in results:
        if r.get("content"):
            formatted.append(
                f"Source: {r['title']}\n{r['content'][:500]}"
            )
    return "\n\n".join(formatted)


async def _synthesise_brief(job: JobAnalysis, results: list[dict]) -> str:
    """
    Synthesise search results into a concise company brief.
    """
    search_context = _format_search_results(results)

    if not search_context:
        return f"No web results found for {job.company_name}."

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Write a company brief for a candidate applying to {job.company_name} 
for the role of {job.role_title}.

Search results:
{search_context}

Cover these points if the information is available:
- What the company does and who their customers are
- Stage, size, or funding (if relevant)
- Any recent news — growth, layoffs, pivots, acquisitions
- Engineering or team culture signals
- Anything a candidate should know before applying or interviewing
- Employee sentiment from Reddit or Glassdoor if present in results — 
  be specific about what people say, positive or negative
- Anything a candidate should know before applying or interviewing

Keep it under 250 words in plain prose no markdown. Be factual and direct.  
If Reddit or Glassdoor results are present, give them their own sentence or two"""
            }
        ]
    )

    return response.content[0].text.strip()