import json
import logging

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

            # Execute each tool call and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"  Tool call: {block.name}({block.input})")
                    result = await handle_tool_call(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )

            # Feed tool results back to Claude
            messages.append({"role": "user", "content": tool_results})

        elif response.stop_reason == "end_turn":
            # Claude is done researching — extract the screening note from its response
            text_content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text_content += block.text

            try:
                # Strip potential markdown fencing if Claude wraps JSON in ```
                cleaned = text_content.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]
                if cleaned.endswith("```"):
                    cleaned = cleaned.rsplit("```", 1)[0]
                cleaned = cleaned.strip()

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
