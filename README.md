# Kharis Screening Agent

AI-powered company screening tool for investment analysts. Submit a company name and Slack handle — the agent researches the company using web search, generates a structured screening note via Claude, and delivers it to Slack.

## Architecture

```
POST /screen { company_name, slack_handle }
         │
         ▼
    FastAPI ──► BackgroundTask
                     │
                     ▼
             ┌──────────────┐
             │ Claude Agent  │ ← system prompt (PE analyst persona)
             │ (tool use)    │
             └──────┬───────┘
                    │  agentic loop: Claude decides what to search
                    ▼
           ┌─────────────────┐
           │ Tools:          │
           │ • web_search    │ → Brave Search API
           │ • get_webpage   │ → httpx + trafilatura
           └─────────────────┘
                    │
                    ▼  structured JSON output
            ┌──────────────┐
            │ Slack SDK    │ → #deal-screening channel
            │ (Block Kit)  │
            └──────────────┘
```

## Key Design Choices

- **Agentic tool use** — Claude autonomously decides what to search, when to fetch a page, and when it has enough data.
- **BackgroundTasks** for async processing — the API responds immediately, and multiple requests can run concurrently.
- **Brave Search** — free tier (2,000 queries/month), clean API, high-quality results.
- **Trafilatura** — best Python library for extracting clean text from web pages.

## Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com)
- [Brave Search API key](https://brave.com/search/api/) (free tier)
- Slack Bot Token (see setup below)

## Slack App Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → From Scratch
2. Under **OAuth & Permissions**, add Bot Token Scopes: `chat:write`, `chat:write.public`
3. Click **Install to Workspace** and authorize
4. Copy the **Bot User OAuth Token** (`xoxb-...`) → this is your `SLACK_BOT_TOKEN`
5. In Slack, right-click your target channel → **View channel details** → copy the Channel ID → this is your `SLACK_CHANNEL_ID`
6. Invite the bot to the channel: `/invite @BotName`

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/kharis-screening-agent.git
cd kharis-screening-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Start the server

```bash
uvicorn src.main:app --reload
```

### Submit a screening request

```bash
curl -X POST http://localhost:8000/screen \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Vinted", "slack_handle": "@bastien"}'
```

The API responds immediately with a confirmation. The screening note will appear in your Slack channel within 15-30 seconds.

### API Docs

FastAPI auto-generates interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## Running Tests

```bash
pytest tests/ -v
```

## Design Decisions

See [ANSWERS.md](./ANSWERS.md) for a detailed discussion of architecture choices, prompt engineering, and trade-offs.
