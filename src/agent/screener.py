import asyncio
import json
import logging
import re

import anthropic

from src.config import settings
from src.models.schemas import ScreeningNote
from src.agent.prompts import SCREENING_SYSTEM_PROMPT
from src.agent.tools import TOOLS, handle_tool_call

logger = logging.getLogger(__name__)


async def run_screening(company_name: str) -> ScreeningNote:
    """Run the AI screening agent for a given company.

    The agent uses Claude's native tool use to autonomously research the company,
    then produces a structured screening note.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    system_prompt = SCREENING_SYSTEM_PROMPT.format(max_iterations=settings.max_agent_iterations)

    messages = [
        {
            "role": "user",
            "content": (
                f"Research and produce a screening note for: {company_name}\n\n"
                "Use your tools to gather comprehensive information before writing the note."
            ),
        }
    ]

    for iteration in range(settings.max_agent_iterations):
        logger.info(f"Agent iteration {iteration + 1} for '{company_name}'")

        response = await client.messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        # If Claude wants to use tools, execute them and continue the loop
        if response.stop_reason == "tool_use":
            # Append Claude's response (includes both text and tool_use blocks)
            messages.append({"role": "assistant", "content": response.content})

            # Execute tool calls in parallel for speed
            tool_blocks = [b for b in response.content if b.type == "tool_use"]
            for b in tool_blocks:
                logger.info(f"  Tool call: {b.name}({b.input})")

            results = await asyncio.gather(
                *(handle_tool_call(b.name, b.input) for b in tool_blocks)
            )

            tool_results = [
                {"type": "tool_result", "tool_use_id": b.id, "content": r}
                for b, r in zip(tool_blocks, results)
            ]

            # Feed tool results back to Claude
            messages.append({"role": "user", "content": tool_results})

        elif response.stop_reason == "end_turn":
            # Claude is done researching — extract the screening note from its response
            text_content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text_content += block.text

            try:
                cleaned = text_content.strip()

                # Extract JSON from markdown fencing (```json ... ``` or ``` ... ```)
                fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", cleaned, re.DOTALL)
                if fence_match:
                    cleaned = fence_match.group(1).strip()

                # If still not valid JSON, try to find the JSON object in the text
                if not cleaned.startswith("{"):
                    brace_start = cleaned.find("{")
                    brace_end = cleaned.rfind("}") + 1
                    if brace_start != -1 and brace_end > brace_start:
                        cleaned = cleaned[brace_start:brace_end]

                note_data = json.loads(cleaned)
                note = ScreeningNote(**note_data)
                logger.info(f"Screening note generated for '{company_name}'")
                return note

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse screening note: {e}\nRaw output: {text_content}")
                raise ValueError(f"Agent produced invalid output: {e}") from e
        else:
            logger.warning(f"Unexpected stop reason: {response.stop_reason}")
            break

    raise RuntimeError(
        f"Agent exceeded maximum iterations ({settings.max_agent_iterations}) "
        f"for '{company_name}'"
    )
