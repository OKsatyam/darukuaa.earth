"""
/api/chat — accepts free text and/or structured land data, returns a
structured recommendation (see app/models for the response shape).

Implementation lands in Task 5/6 (LangGraph flow + this endpoint wiring).
Left as a stub during scaffolding so the project structure is complete
and importable from step 1.
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
async def chat_stub():
    return {"status": "not_implemented_yet"}
