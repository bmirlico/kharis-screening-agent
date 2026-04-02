from pydantic import BaseModel, Field


class ScreeningRequest(BaseModel):
    """Incoming request to screen a company."""

    company_name: str = Field(..., min_length=1, description="Name of the company to screen")
    slack_handle: str = Field(
        ..., min_length=1, description="Slack handle of the requesting analyst, e.g. @bastien"
    )


class ScreeningNote(BaseModel):
    """Structured screening note produced by the agent."""

    company_name: str
    business_summary: str
    business_model: str
    market: str
    traction_signals: str
    fit_assessment: str


class ScreeningResponse(BaseModel):
    """Immediate API response confirming the screening request was accepted."""

    status: str
    message: str
