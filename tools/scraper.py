import httpx
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Sites that block scraping 
BLOCKED_DOMAINS = ["linkedin.com", "indeed.com", "glassdoor.com"]


def is_blocked_domain(url: str) -> bool:
    return any(domain in url for domain in BLOCKED_DOMAINS)


async def scrape_job_posting(url: str) -> str:
    """
    Fetch and extract text from a job posting URL.
    Returns the cleaned text content of the page.
    Raises ValueError if the site is known to block scraping.
    Raises RuntimeError if the request fails.
    """
    if is_blocked_domain(url):
        raise ValueError(
            f"Direct scraping not supported for this site. "
            f"Use Tavily search instead or paste the job text manually."
        )

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
        except httpx.TimeoutException:
            raise RuntimeError(f"Request timed out for URL: {url}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"HTTP {e.response.status_code} error fetching URL: {url}"
            )

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove noise — scripts, styles, nav, footer
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Clean up excessive whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = "\n".join(lines)

    if len(cleaned) < 200:
        raise RuntimeError(
            f"Page content too short — likely a login wall or empty page: {url}"
        )

    return cleaned