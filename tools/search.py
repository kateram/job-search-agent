from tavily import TavilyClient
from core.config import settings


client = TavilyClient(api_key=settings.tavily_api_key)


async def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web via Tavily.
    Returns a list of {url, title, content} dicts.
    """
    response = client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced"
    )

    return [
        {
            "url": result.get("url", ""),
            "title": result.get("title", ""),
            "content": result.get("content", ""),
        }
        for result in response.get("results", [])
    ]


async def fetch_job_posting_text(url: str) -> str:
    """
    Use Tavily to extract text from a URL directly.
    Fallback for sites that block direct scraping (LinkedIn, Indeed).
    """
    response = client.extract(urls=[url])

    results = response.get("results", [])
    if not results:
        raise RuntimeError(f"Tavily could not extract content from: {url}")

    return results[0].get("raw_content", "")