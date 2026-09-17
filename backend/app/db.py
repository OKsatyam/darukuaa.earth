"""
MongoDB Atlas persistence for conversation sessions.

Schema (collection: "sessions"):
  {
    session_id: str,
    land_data: dict,        # accumulated structured fields across turns
    messages: [ {role, content, timestamp} ],
    created_at: datetime,
    updated_at: datetime,
  }

Why Mongo over an in-memory dict: this API can restart (free-tier hosts like
Render sleep/redeploy) and an in-memory dict loses every open conversation
on restart. Why Mongo over SQLite: conversation shape varies turn to turn
(land_data grows incrementally, messages is a variable-length list) which
maps naturally onto a document, without a migration every time a new
LandData field is added.

Deliberately fault-tolerant: if MONGODB_URI isn't configured yet (or Atlas
is briefly unreachable), the chat endpoint should keep working for that one
turn rather than 500 — it just won't remember earlier turns. This matters
during the build-out, before real Atlas credentials are wired into .env.
"""
from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
    return _client


def get_db():
    return get_client()[settings.mongodb_db_name]


async def get_session(session_id: str) -> Optional[dict]:
    """Returns the stored session doc, or None if it doesn't exist yet or
    the DB is unreachable (caller treats both the same way: fresh session)."""
    try:
        db = get_db()
        return await db.sessions.find_one({"session_id": session_id})
    except Exception:
        return None


async def upsert_session(session_id: str, land_data: dict, new_messages: list[dict]) -> None:
    """Appends new_messages and merges land_data into the session doc,
    creating it if it doesn't exist. Best-effort: a DB hiccup here should
    never break the chat response the user already received."""
    try:
        db = get_db()
        now = datetime.now(timezone.utc)
        await db.sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {"land_data": land_data, "updated_at": now},
                "$setOnInsert": {"created_at": now},
                "$push": {"messages": {"$each": new_messages}},
            },
            upsert=True,
        )
    except Exception:
        pass


async def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
