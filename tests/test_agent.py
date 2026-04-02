import json
import pytest
from unittest.mock import patch

from src.agent.tools import handle_tool_call


@pytest.mark.asyncio
class TestToolHandler:
    """Test the tool call dispatcher."""

    @patch("src.agent.tools.search_web")
    async def test_web_search_dispatches_correctly(self, mock_search):
        mock_search.return_value = [
            {"title": "Result", "url": "https://example.com", "snippet": "A snippet"}
        ]
        result = await handle_tool_call("web_search", {"query": "test"})
        parsed = json.loads(result)

        mock_search.assert_called_once_with("test")
        assert len(parsed) == 1
        assert parsed[0]["title"] == "Result"

    @patch("src.agent.tools.fetch_webpage")
    async def test_get_webpage_dispatches_correctly(self, mock_fetch):
        mock_fetch.return_value = "Page content here"
        result = await handle_tool_call("get_webpage", {"url": "https://example.com"})

        mock_fetch.assert_called_once_with("https://example.com")
        assert result == "Page content here"

    async def test_unknown_tool_returns_error(self):
        result = await handle_tool_call("nonexistent_tool", {})
        assert "Unknown tool" in result
