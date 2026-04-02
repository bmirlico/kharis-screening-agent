# Written Answers

## 1. Architecture Walkthrough

The system has four layers:

**Input Layer** — Two entry points: (1) A Slack bot using slack-bolt Socket Mode — analysts type `@Kharis Screener Vinted` directly in Slack, and the bot acknowledges immediately before running the screening in the background. (2) A REST API (`POST /screen`) as a programmatic fallback, accepting a company name and Slack handle via JSON. Both paths feed into the same screening pipeline.

**Agent Layer** — The core of the system. A Claude-powered agent (using `claude-sonnet-4-20250514`) runs an agentic tool-use loop. The agent receives a system prompt that defines its role as a PE analyst and its research strategy, then autonomously decides which tools to call, in what order, and how many times. The loop works as follows:
1. Send the initial message ("Research {company}") to Claude with the tool definitions.
2. If Claude responds with `tool_use` blocks, execute each tool, collect results, and feed them back.
3. Repeat until Claude responds with `end_turn` and a structured JSON screening note.
4. Safety: a hard cap on iterations prevents runaway loops.

This design lets Claude act as the orchestrator — it decides the research plan based on what it finds, rather than following a rigid pipeline.

**Services Layer** — Two data-gathering services (Brave Search for web search, httpx + trafilatura for webpage content extraction) and two Slack services: slack-bolt for receiving mentions via Socket Mode, and Slack SDK for posting formatted Block Kit notes back to the channel.

**What breaks first at scale:**
- `BackgroundTasks` runs in the same process as FastAPI — under heavy concurrent load, this starves the event loop. The fix is a proper task queue (Celery + Redis or similar).
- No deduplication — the same company can be screened simultaneously by multiple analysts, wasting API calls.
- Brave Search free tier (2,000 queries/month) would be exhausted quickly with 5 daily analysts.
- No persistent state — if the server crashes mid-screening, the job is silently lost with no retry.
- Claude API rate limits could throttle concurrent screenings.

## 2. Prompt Engineering Choices

The system prompt (`src/agent/prompts.py`) was designed with several deliberate choices:

**PE analyst persona** — Grounding the prompt in a specific professional role ("senior investment analyst at a European PE firm focused on consumer/consumer-tech") shapes Claude's analytical lens. It prioritizes business model clarity, unit economics, and competitive positioning — the things a real analyst would care about.

**Structured research strategy** — The prompt includes a 6-step research playbook (broad search → funding → revenue → team → news → company website). This guides Claude toward comprehensive coverage without being prescriptive about exact queries. Claude still decides what to search based on what it finds.

**Strict JSON output format** — Requiring a specific JSON schema with exactly 6 named fields enables reliable parsing without regex hacks or post-processing. The field descriptions are detailed enough that Claude understands what each section expects.

**"Opinionated" instruction** — The fit assessment is explicitly instructed to "take a clear stance" because a wishy-washy assessment is useless to an analyst. This was an intentional design choice — in PE screening, an uncertain "maybe" is worse than a wrong but clear "no."

**Quality guardrails** — The prompt requires Claude to cite sources ("per Crunchbase"), distinguish facts from inferences, and explicitly flag missing data rather than fabricating. In an investment context, accuracy and intellectual honesty are non-negotiable.

**What I iterated on:** I initially had a simpler prompt without the research strategy steps — Claude would often do only 1-2 searches and produce thin notes. Adding the step-by-step research guide significantly improved coverage without removing Claude's autonomy in choosing queries.

## 3. What I Would Do With More Time

If this were a daily tool for 5 analysts at Kharis:

- **Task queue + persistence**: Replace `BackgroundTasks` with Celery + Redis. Add a PostgreSQL-backed job table so screening requests survive server restarts, can be retried on failure, and have status tracking.
- **Progress updates**: The bot already posts an acknowledgment ("Screening *{company}*..."), but with more time I would edit that message in-place as the agent progresses (e.g., "Searching funding data..." → "Writing note...") using `chat_update`.
- **Structured data sources**: Add the Crunchbase API for reliable funding/revenue data and LinkedIn API for team composition. Web search is good for breadth but weak on structured financials.
- **Caching**: Cache search results and screening notes in Redis (keyed by company name + date). If two analysts screen the same company the same week, reuse the note.
- **Feedback loop**: Add thumbs up/down buttons on the Slack message (Slack interactivity). Store feedback in a database and use it to iterate on the system prompt and evaluate quality over time.
- **Evaluation suite**: Build a benchmark of 20+ known companies with expected outputs. Run this on every prompt change to catch quality regressions.
- **Error handling and observability**: Structured logging with request IDs, Claude token usage tracking, latency percentiles, alerting on failure rates.
- **Rate limiting**: Per-analyst rate limits to prevent accidental spam, and graceful queuing when API limits are approached.
- **Latency optimization**: Screening currently takes ~40 seconds end-to-end (5-6 Claude API roundtrips + tool execution). Two levers to improve this: (1) optimize the prompt so Claude makes fewer, more targeted searches instead of broad exploratory ones; (2) lower `max_agent_iterations` from 10 to 6-7 to cap tail latency while still allowing enough research depth. Switching to a faster model (Haiku) would hurt note quality since the agent needs strong reasoning at every step — query formulation, result analysis, and synthesis.

## 4. LangChain / LangGraph: No

I did not use LangChain or LangGraph. The core agentic loop — send message to Claude, handle tool use, feed results back, repeat — is approximately 50 lines of straightforward Python using the Anthropic SDK directly.

LangChain would add a dependency and abstraction layer without reducing code complexity or improving quality at this scale. The Anthropic SDK's tool use API is clean and well-documented; wrapping it in LangChain's abstractions would obscure the control flow and make debugging harder.

I would reach for LangGraph specifically if:
- The system required **multi-agent coordination** (e.g., one agent researches, another writes, a third reviews/edits) with complex handoff logic.
- There was **branching or routing logic** where different company types require fundamentally different research strategies.
- I needed **built-in checkpointing** to resume interrupted workflows across sessions.
- The system grew to include **human-in-the-loop** approval steps mid-pipeline.

For a single-agent, linear tool-use loop like this screening agent, the Anthropic SDK alone is the right tool. Simplicity is a feature.

## 5. A System I Have Shipped

**[Elderly Companion](https://github.com/bmirlico/elderly-companion)** — an AI phone companion for seniors that won #1 at the 2026 {Tech: Europe} Paris AI Hackathon. The system makes daily phone calls to elderly residents, holds warm conversations, analyzes their well-being, and alerts families when something seems off.

**Problem:** Isolated seniors — especially those in care homes or living alone — often go days without meaningful human interaction. Families worry but can't call every day. Existing check-in solutions are either robotic IVR systems or require the senior to use an app, which most won't.

**What I built:** A real-time voice agent using FastAPI + WebSockets as the backbone, Twilio for outbound calls and bidirectional audio streaming, Gradium for speech-to-text (with VAD for natural turn detection) and text-to-speech, and OpenAI GPT-4o-mini for conversational responses. After each call, a Dust AI agent analyzes the transcript and produces a structured assessment (mood score, alert level: green/yellow/red, family message). If the alert level is yellow or red, Twilio sends an SMS to the family immediately. The family dashboard (React + TypeScript) shows daily pulse cards, a week-long mood strip, and AI-generated nudges. Supabase (PostgreSQL) stores residents, calls, transcripts, and analyses.

**What broke:**
- **Audio format conversion was latency-sensitive.** Twilio streams mulaw at 8kHz, but Gradium expects PCM at 24kHz. The real-time resampling had to stay under 200ms round-trip or the conversation felt laggy. We solved it with streaming chunk processing rather than buffering full utterances.
- **STT false positives from background noise.** Care home environments are noisy — TV, other residents, staff. Gradium's VAD would trigger on ambient sound. We tuned the inactivity probability threshold to >80% and added a 4-second fallback timeout, plus echo suppression that mutes STT while the AI is speaking.
- **Post-call analysis reliability.** The Dust agent occasionally returned malformed JSON when transcripts were very short (e.g., the senior hung up after 10 seconds). We added validation with sensible defaults and a minimum transcript length check before triggering analysis.
