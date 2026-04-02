import asyncio
import logging
import re

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from src.config import settings
from src.agent.screener import run_screening
from src.services.slack import post_screening_note

logger = logging.getLogger(__name__)

bolt_app = AsyncApp(token=settings.slack_bot_token)


@bolt_app.event("app_mention")
async def handle_mention(event, say, client):
    """Handle @bot mentions — extract company name and trigger screening."""
    text = event.get("text", "")
    company_name = re.sub(r"<@[\w]+>\s*", "", text).strip()

    if not company_name:
        await say("Usage: `@Kharis Screener <company name>` — e.g. `@Kharis Screener Vinted`")
        return

    # Resolve analyst display name
    try:
        user_info = await client.users_info(user=event["user"])
        profile = user_info["user"]["profile"]
        display_name = profile.get("display_name") or user_info["user"].get("real_name", "Unknown")
        slack_handle = f"@{display_name}"
    except Exception:
        slack_handle = f"@{event['user']}"

    channel = event["channel"]
    await say(f"Screening *{company_name}*... I'll post the note here when it's ready.")

    async def _run_and_post():
        try:
            note = await run_screening(company_name)
            await post_screening_note(note, slack_handle, channel=channel)
        except Exception as e:
            logger.error(f"Screening failed for '{company_name}': {e}", exc_info=True)
            await client.chat_postMessage(
                channel=channel,
                text=f"Screening failed for '{company_name}': {e}",
            )

    asyncio.create_task(_run_and_post())


async def start_bolt() -> AsyncSocketModeHandler:
    """Start the Socket Mode handler as a background task (non-blocking)."""
    handler = AsyncSocketModeHandler(bolt_app, settings.slack_app_token)
    await handler.connect_async()
    logger.info("Slack Socket Mode handler started")
    return handler


async def stop_bolt(handler: AsyncSocketModeHandler) -> None:
    """Stop the Socket Mode handler."""
    await handler.close_async()
    logger.info("Slack Socket Mode handler stopped")
