# Darukaa Biodiversity Intelligence Chatbot

AI system that reasons about India-specific soil, land-use, climate and
biodiversity data and returns evidence-backed, multi-metric recommendations
— built for the Darukaa.Earth AI Biodiversity Intelligence Chatbot
Challenge.

Given a free-text description of a piece of land (and/or structured land
data), the system traces a deterministic, source-cited cause → effect chain
(e.g. `land_use_change → forest_cover`, or `agroforestry_adoption →
water_availability → species_survival → biodiversity`) and returns a
concrete action, its confidence, time horizon, and the exact regional
sources behind every number it cites.

## Why it's built this way

The core design bet: reasoning correctness and evidence-grounding matter
more than fluent prose, so the two are deliberately kept apart.

- **What is said** is decided entirely by `connections.json` (a hand-curated
  graph of cause → effect edges, each with a mechanism, a regional magnitude,
  and a citation) plus a small set of guardrails. No LLM ever picks a fact,
  a chain, or a number — the traversal is path-locked (a step is only
  followed when the next entry's `cause` exactly matches the current
  entry's `effect`), so reasoning can't wander into unrelated variables.
- **How it's said** is the only place an LLM (Groq, optional) touches the
  system: it rephrases the already-decided explanation into more natural
  conversational prose for the chat bubble. It's not allowed to add a fact,
  number or source that isn't already in the text it's given, and if it's
  unavailable, misconfigured, or fails for any reason, the app falls back
  to the deterministic template — the chat never breaks because of it.

This split means every recommendation is auditable end to end: you can
always see exactly which rule and which source produced it, regardless of
whether the LLM narration layer is on.

## Architecture

```
frontend (Next.js 14)  ──HTTP──▶  backend (FastAPI)
                                        │
                                        ▼
                              LangGraph state machine
                        (app/services/graph.py)
                                        │
        ┌─────────────┬───────────────┼───────────────┬──────────────┐
        ▼              ▼               ▼                ▼              ▼
   guardrails    connections.json   ChromaDB RAG    Groq (optional)   MongoDB
  (domain lock,   (cause→effect      (retrieves       (rephrases      (session +
   input sanity,   chain, path-      supporting        the decided     land-data
   no-match-no-    locked walk)      source excerpts)  text only)      memory)
   claim, prompt-
   injection,
   confidence
   gating)
```

**Backend flow** (`app/services/graph.py`), one LangGraph node per stage:

1. `validate` — domain lock + input-sanity guardrails; off-topic or
   physically-impossible input stops here.
2. `detect_and_check` — maps the message + structured data to a cause.
   Free-text keyword triggers are checked first (the user's own words take
   priority), then the structured `land_use` field against the same
   triggers, then narrower structured-only shortcuts (a numeric soil-carbon
   %, a categorical rainfall level) as a last resort. If nothing matches
   but required categories (soil / land use / climate) are missing, the
   bot asks a clarifying question instead of guessing.
3. `reason` — walks `connections.json` from the detected cause as far as
   verified edges allow (max 4 hops, loop-safe).
4. `retrieve` — pulls the top-2 most relevant source excerpts from ChromaDB
   for the resolved chain.
5. `compose` — builds the structured `recommendation` (action, confidence,
   time horizon, full reasoning chain, retrieved sources) and, only for the
   chat bubble text, optionally asks Groq to rephrase the explanation.

Every session's land data and message history persist to MongoDB
(`app/db.py`) so later turns can add to or override earlier structured data
without repeating it — and if MongoDB isn't configured, the app fails soft
and still answers every message, just without cross-session memory.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | FastAPI, LangGraph (explicit state machine, not one big prompt) |
| Reasoning source of truth | Hand-curated `connections.json` graph |
| Retrieval | ChromaDB + sentence-transformers (local embeddings, no API needed) |
| Optional narration | Groq (OpenAI-compatible API), `openai/gpt-oss-20b` |
| Session persistence | MongoDB Atlas via Motor (async), fails soft if unset |
| Frontend | Next.js 14 (App Router), React, TypeScript — no CSS framework, inline styles |

## API

One route does the real work:

### `POST /api/chat`

```jsonc
// request
{
  "session_id": "abc123",
  "message": "We cleared forest land last year to expand farming...",
  "structured_data": {                 // all fields optional
    "soil_organic_carbon_pct": 0.6,
    "soil_ph": 7.8,
    "soil_moisture": "low",
    "rainfall": "low",
    "land_use": "deforestation",
    "region": "Western Ghats, Maharashtra",
    "latitude": 19.5,
    "longitude": 73.8
  }
}
```

```jsonc
// response
{
  "session_id": "abc123",
  "reply_text": "**Halt further land-use conversion...**\n\n...",
  "clarifying_question": null,
  "recommendation": {
    "action": "Halt further land-use conversion and prioritize restoration of natural cover",
    "explanation": "...deterministic, source-cited text (never touched by the LLM)...",
    "impacted_metrics": ["land_use_change", "forest_cover"],
    "time_horizon": "long_term",
    "confidence": "high",
    "reasoning_chain": [ { "cause": "...", "effect": "...", "mechanism": "...", "magnitude": "...", "regional_source": "..." } ],
    "retrieved_sources": [ { "source_file": "...", "excerpt": "..." } ]
  },
  "guardrail_notice": null
}
```

If the message is off-topic, `guardrail_notice` explains why and
`recommendation` is `null`. If required land-data categories are missing,
`clarifying_question` asks for them instead of guessing.

### `GET /health`

Liveness check — `{"status": "ok"}`.

## Guardrails

1. **Domain lock** — refuses/redirects queries with no soil, land, climate,
   biodiversity or human-impact keywords, deliberately permissive (a false
   "yes it's on topic" is safer for a demo than wrongly refusing a real
   question).
2. **No-match-no-claim** — if no `connections.json` rule and no relevant
   retrieval exist for a detected cause, the bot says so explicitly rather
   than inventing a plausible-sounding answer.
3. **Input sanity** — rejects physically impossible structured values
   (soil pH outside 0–14, latitude outside ±90, etc.) before they reach
   reasoning.
4. **Prompt-injection resistance** — user text is always wrapped as
   `<user_provided_data>` before ever reaching narration, so text like
   "ignore previous instructions" is just a string to describe.
5. **Confidence gating** — a chain's confidence is only as strong as its
   weakest verified link (never averaged up), and low-confidence chains
   come with an explicit notice telling the user to verify with a local
   expert.

## Local development

```bash
# backend
cd backend
cp .env.example .env        # fill in MONGODB_URI / GROQ_API_KEY if you have them
pip install -r requirements.txt
python -m app.services.rag  # builds the ChromaDB index once
uvicorn app.main:app --reload

# frontend
cd frontend
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

Both `MONGODB_URI` and `GROQ_API_KEY` are optional — the app runs and
answers every message without either, just without cross-session memory
and with the deterministic template instead of LLM-rephrased prose.

## Deployment

See [`DEPLOYMENT.md`](./DEPLOYMENT.md) — MongoDB Atlas, Render/Railway
(backend), Vercel (frontend), step by step.

## Project structure

```
backend/
  app/
    main.py            # FastAPI app, CORS, startup RAG-index build, /health
    config.py           # env-driven settings (pydantic-settings)
    db.py                # MongoDB session persistence, fails soft
    models/schemas.py    # request/response Pydantic models
    routers/chat.py       # POST /api/chat
    services/
      connections.py       # cause-detection + path-locked chain walk
      guardrails.py          # the 5 guardrails
      graph.py                 # LangGraph state machine wiring it together
      rag.py                     # ChromaDB indexing + retrieval
      narration.py                 # optional Groq rephrasing layer
    data/
      connections.json           # the reasoning graph — sole source of truth
      sources/                   # raw source documents RAG is built from
frontend/
  app/page.tsx            # main chat page
  components/               # ChatInput, ChatMessage, RecommendationCard, StructuredPanel
  lib/api.ts, lib/types.ts    # API client + shared types
```
