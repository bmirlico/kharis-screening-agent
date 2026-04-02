import httpx
import logging

from src.config import settings

logger = logging.getLogger(__name__)

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


async def search_web(query: str, count: int = 5) -> list[dict]:
    """Search the web using Brave Search API.

    Returns a list of {title, url, snippet} dicts.
    """
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": settings.brave_search_api_key,
    }
    params = {"q": query, "count": count}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                BRAVE_SEARCH_URL, headers=headers, params=params, timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("web", {}).get("results", []):
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("description", ""),
                    }
                )
            return results

        except httpx.HTTPError as e:
            logger.error(f"Brave Search API error: {e}")
            return [{"title": "Search error", "url": "", "snippet": str(e)}]
