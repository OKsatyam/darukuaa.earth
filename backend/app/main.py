import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat
from app import db
from app.services import rag

logger = logging.getLogger("darukaa")

app = FastAPI(
    title="Darukaa Biodiversity Intelligence API",
    description="AI system for India-focused biodiversity, soil, land-use and climate reasoning.",
    version="0.1.0",
)

# ALLOWED_ORIGINS is a comma-separated list (e.g. the deployed Vercel URL).
# Defaults to "*" so local dev / early demo links keep working without any
# env var set; set it once a real frontend URL exists.
_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = ["*"] if _origins_env.strip() == "*" else [o.strip() for o in _origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.on_event("startup")
async def startup_event():
    # Build the RAG index eagerly on cold start (Render/Railway free tiers
    # sleep and lose local disk between deploys) so the FIRST /api/chat call
    # doesn't pay the embedding-model-download + indexing cost. Never let a
    # startup hiccup here (e.g. no network yet) crash the whole app — retrieve()
    # already falls back to building the index lazily on first use.
    try:
        rag.build_index()
        logger.info("RAG index ready at startup.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Startup RAG index build skipped/failed: %s", exc)


@app.on_event("shutdown")
async def shutdown_event():
    await db.close_client()


@app.get("/health")
def health():
    return {"status": "ok"}
