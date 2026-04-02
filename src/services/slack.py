import logging
from datetime import datetime, timezone

from slack_sdk.web.async_client import AsyncWebClient

from src.config import settings
from src.models.schemas import ScreeningNote

logger = logging.getLogger(__name__)


def _format_blocks(note: ScreeningNote, slack_handle: str) -> list[dict]:
    """Build Slack Block Kit blocks for a screening note."""
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Screening Note: {note.company_name}",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Business Summary*\n{note.business_summary}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Business Model*\n{note.business_model}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Market*\n{note.market}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Traction Signals*\n{note.traction_signals}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Initial Fit Assessment*\n{note.fit_assessment}",
            },
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        f"Requested by {slack_handle} · "
                        f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
                    ),
                }
            ],
        },
    ]


async def post_screening_note(note: ScreeningNote, slack_handle: str) -> None:
    """Post a formatted screening note to Slack."""
    client = AsyncWebClient(token=settings.slack_bot_token)
    blocks = _format_blocks(note, slack_handle)

    try:
        await client.chat_postMessage(
            channel=settings.slack_channel_id,
            text=f"Screening Note: {note.company_name}",  # fallback for notifications
            blocks=blocks,
        )
        logger.info(f"Screening note for '{note.company_name}' posted to Slack")
    except Exception as e:
        logger.error(f"Failed to post to Slack: {e}")
        raise
