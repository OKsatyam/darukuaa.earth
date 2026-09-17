from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat
from app import db

app = FastAPI(
    title="Darukaa Biodiversity Intelligence API",
    description="AI system for India-focused biodiversity, soil, land-use and climate reasoning.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.on_event("shutdown")
async def shutdown_event():
    await db.close_client()


@app.get("/health")
def health():
    return {"status": "ok"}
