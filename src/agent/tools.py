import json
import logging

from src.services.search import search_web
from src.services.scraper import fetch_webpage

logger = logging.getLogger(__name__)

TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Search the web for information. Use specific, targeted queries like "
            "'Vinted Series F funding 2024' or 'Back Market revenue ARR'. "
            "Returns a list of results with title, URL, and snippet."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query — be specific and targeted.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_webpage",
        "description": (
            "Fetch and extract the main text content of a webpage. "
            "Use this to read full articles, company about pages, Crunchbase profiles, "
            "or press releases found via web_search."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to fetch.",
                }
            },
            "required": ["url"],
        },
    },
]


async def handle_tool_call(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call to the appropriate service and return the result as a string."""
    try:
        if tool_name == "web_search":
            results = await search_web(tool_input["query"])
            return json.dumps(results, ensure_ascii=False)
        elif tool_name == "get_webpage":
            return await fetch_webpage(tool_input["url"])
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        logger.error(f"Tool call '{tool_name}' failed: {e}")
        return f"Tool error: {e}"
