# 🔍 Kharis Screening Agent

AI-powered company screening tool for investment analysts. Mention the bot in Slack with a company name — the agent researches the company using web search, generates a structured screening note via Claude, and delivers it directly in the channel.

## 🎬 Demo

https://github.com/user-attachments/assets/be42a24d-6d6c-41f2-a71d-81ef692d695f

## 🏗️ Architecture

```
  @Kharis Screener Vinted (Slack mention)
         │
         ▼
    slack-bolt ──► Socket Mode (WebSocket)
         │
         │   OR
         │
  POST /screen ──► FastAPI BackgroundTask
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
 │ Slack SDK    │ → screening note in channel
 │ (Block Kit)  │
 └──────────────┘
```

## 💡 Key Design Choices

- **Slack-native interface** — analysts type `@Kharis Screener Vinted` directly in Slack. No curl, no external UI.
- **Socket Mode** — the bot connects to Slack via WebSocket, so no public URL or reverse proxy is needed.
- **Agentic tool use** — Claude autonomously decides what to search, when to fetch a page, and when it has enough data.
- **Dual input** — Slack mentions for daily use, REST API (`POST /screen`) as a programmatic fallback.
- **Brave Search** — free tier (2,000 queries/month), clean API, high-quality results.
- **Trafilatura** — best Python library for extracting clean text from web pages.

## 📋 Prerequisites

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com)
- [Brave Search API key](https://brave.com/search/api/) (free tier)
- Slack App with Socket Mode (see setup below)

## 🔧 Slack App Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → From Scratch
2. Under **Settings → Socket Mode**, toggle it on and generate an app-level token (`xapp-...`) → this is your `SLACK_APP_TOKEN`
3. Under **Event Subscriptions**, enable events and add `app_mention` to **Bot Events**
4. Under **OAuth & Permissions**, add Bot Token Scopes: `app_mentions:read`, `chat:write`, `chat:write.public`, `users:read`
5. Click **Install to Workspace** and authorize
6. Copy the **Bot User OAuth Token** (`xoxb-...`) → this is your `SLACK_BOT_TOKEN`
7. In Slack, right-click your target channel → **View channel details** → copy the Channel ID → this is your `SLACK_CHANNEL_ID`
8. Invite the bot to the channel: `/invite @BotName`

## 📦 Installation

```bash
git clone https://github.com/YOUR_USERNAME/kharis-screening-agent.git
cd kharis-screening-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

## 🚀 Usage

### Start the server

```bash
uvicorn src.main:app --reload
```

This starts both the FastAPI server and the Slack Socket Mode connection.

### Option 1: Slack (primary)

In any channel where the bot is invited, type:

```
@Kharis Screener Vinted
```

The bot acknowledges immediately, then posts the structured screening note in the same channel within 15-30 seconds.

### Option 2: REST API

```bash
curl -X POST http://localhost:8000/screen \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Vinted", "slack_handle": "@bastien"}'
```

The API responds immediately with a confirmation. The note is posted to the default Slack channel (`SLACK_CHANNEL_ID`).

### API Docs

FastAPI auto-generates interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## 🧪 Running Tests

```bash
pytest tests/ -v
```

## 📝 Design Decisions / Written questions

See [ANSWERS.md](./ANSWERS.md) for a detailed discussion of architecture choices, prompt engineering, and trade-offs.
