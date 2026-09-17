"""Pydantic models for the /api/chat request and response shapes."""
from typing import Optional, List
from pydantic import BaseModel, Field


class LandData(BaseModel):
    """Structured input (JSON) — the brief's 'structured input' requirement.
    Every field optional: users may supply only some of these, in any turn."""
    soil_organic_carbon_pct: Optional[float] = Field(None, description="e.g. 0.3 for 0.3%")
    soil_ph: Optional[float] = None
    soil_moisture: Optional[str] = None  # "low" | "medium" | "high"
    rainfall: Optional[str] = None       # "low" | "medium" | "high"
    land_use: Optional[str] = None       # e.g. "monoculture_wheat", "mixed_forest"
    region: Optional[str] = None         # e.g. "semi-arid", "Odisha"
    latitude: Optional[float] = None     # bonus: geo-coordinates
    longitude: Optional[float] = None


class ChatRequest(BaseModel):
    session_id: str
    message: Optional[str] = None
    structured_data: Optional[LandData] = None


class SourceRef(BaseModel):
    source_file: str
    excerpt: str


class ChainStep(BaseModel):
    cause: str
    effect: str
    mechanism: str
    magnitude: str
    mechanism_source: str
    regional_source: str


class Recommendation(BaseModel):
    action: str
    explanation: str
    impacted_metrics: List[str]
    time_horizon: str  # short_term | medium_term | long_term
    confidence: str    # high | medium | low
    reasoning_chain: List[ChainStep]
    retrieved_sources: List[SourceRef]


class ChatResponse(BaseModel):
    session_id: str
    reply_text: str
    clarifying_question: Optional[str] = None
    recommendation: Optional[Recommendation] = None
    guardrail_notice: Optional[str] = None
