import logging

from fastapi import FastAPI, BackgroundTasks
from src.models.schemas import ScreeningRequest, ScreeningResponse
from src.agent.screener import run_screening
from src.services.slack import post_screening_note

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kharis Screening Agent",
    description="AI-powered company screening tool for investment analysts.",
    version="0.1.0",
)


async def _process_screening(company_name: str, slack_handle: str) -> None:
    """Background task: run the screening agent and post results to Slack."""
    try:
        logger.info(f"Starting screening for '{company_name}' (requested by {slack_handle})")
        note = await run_screening(company_name)
        await post_screening_note(note, slack_handle)
    except Exception as e:
        logger.error(f"Screening failed for '{company_name}': {e}", exc_info=True)
        # In production: post an error message to Slack so the analyst knows it failed


@app.post("/screen", response_model=ScreeningResponse)
async def screen_company(
    request: ScreeningRequest, background_tasks: BackgroundTasks
) -> ScreeningResponse:
    """Submit a company for AI-powered screening.

    The screening runs asynchronously in the background. The analyst will receive
    the structured note in Slack when it's ready (typically 15-30 seconds).
    """
    background_tasks.add_task(
        _process_screening,
        request.company_name,
        request.slack_handle,
    )
    return ScreeningResponse(
        status="processing",
        message=(
            f"Screening for '{request.company_name}' started. "
            f"{request.slack_handle} will be notified in Slack."
        ),
    )


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
