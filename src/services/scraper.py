import httpx
import trafilatura
import logging

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 4000


async def fetch_webpage(url: str) -> str:
    """Fetch a webpage and extract its main text content.

    Returns clean text truncated to MAX_CONTENT_LENGTH chars.
    Falls back to a descriptive error string on failure.
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            html = response.text

        text = trafilatura.extract(html, include_comments=False, include_tables=True)

        if not text:
            return f"Could not extract meaningful text from {url}"

        if len(text) > MAX_CONTENT_LENGTH:
            text = text[:MAX_CONTENT_LENGTH] + "\n... [truncated]"

        return text

    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return f"Error fetching {url}: {e}"
    except Exception as e:
        logger.error(f"Unexpected error processing {url}: {e}")
        return f"Error processing {url}: {e}"
