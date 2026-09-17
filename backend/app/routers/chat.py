"""
/api/chat — accepts free text and/or structured land data, returns a
structured recommendation (see app/models/schemas.py for the exact shape).

Wiring:
  1. Load prior session (land_data accumulated so far + message history)
     from MongoDB, if any.
  2. Merge this turn's structured_data over the stored land_data — later
     turns can add/override fields without repeating everything already
     given (this is what makes multi-turn memory actually useful instead
     of the user re-typing their land's stats every message).
  3. Run the LangGraph reasoning flow (app/services/graph.py) against the
     merged structured data + this turn's free text.
  4. Persist the turn (best-effort — see app/db.py) and return the result.
"""
from datetime import datetime, timezone

from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.services import graph as graph_service
from app import db

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session = await db.get_session(request.session_id)
    stored_land_data = (session or {}).get("land_data", {}) or {}

    incoming = (
        request.structured_data.model_dump(exclude_none=True)
        if request.structured_data
        else {}
    )
    merged_land_data = {**stored_land_data, **incoming}

    result = graph_service.run_chat(
        session_id=request.session_id,
        message=request.message or "",
        structured=merged_land_data,
    )

    response = ChatResponse(
        session_id=request.session_id,
        reply_text=result.get("reply_text", ""),
        clarifying_question=result.get("clarifying_question"),
        recommendation=result.get("recommendation"),
        guardrail_notice=result.get("guardrail_notice"),
    )

    now = datetime.now(timezone.utc).isoformat()
    new_messages = [{"role": "user", "content": request.message or "", "timestamp": now}]
    if response.reply_text:
        new_messages.append({"role": "assistant", "content": response.reply_text, "timestamp": now})

    await db.upsert_session(request.session_id, merged_land_data, new_messages)

    return response
