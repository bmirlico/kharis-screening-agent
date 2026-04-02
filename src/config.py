from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    anthropic_api_key: str
    brave_search_api_key: str
    slack_bot_token: str
    slack_app_token: str
    slack_channel_id: str
    claude_model: str = "claude-sonnet-4-20250514"
    max_agent_iterations: int = 10

    model_config = {"env_file": ".env"}


settings = Settings()
