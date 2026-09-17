"""
The 5 guardrails agreed on during design:
1. Domain lock       — refuse/redirect off-topic queries.
2. No-match-no-claim — no connections.json rule + no relevant retrieval = say so, don't invent.
3. Input sanity      — reject physically impossible values before they reach reasoning.
4. Prompt-injection resistance — user text is always treated as data, never instructions.
5. Confidence gating — surface low-confidence chains honestly instead of stating them as fact.
"""
from typing import Optional

DOMAIN_KEYWORDS = [
    "soil", "biodiversity", "land", "forest", "climate", "rainfall", "crop",
    "water", "pollinator", "species", "habitat", "ecosystem", "carbon",
    "deforestation", "agriculture", "farm", "region", "wetland", "pollution",
]


def is_in_domain(text: str) -> bool:
    """Guardrail 1: domain lock. Deliberately permissive (keyword OR) — false
    negatives (refusing a valid question) are worse for a demo than false
    positives, but a completely unrelated query still gets caught."""
    if not text:
        return True  # structured-only input has no text to check
    text_l = text.lower()
    return any(kw in text_l for kw in DOMAIN_KEYWORDS)


def no_match_message() -> str:
    """Guardrail 2: no-match-no-claim. Used verbatim when no connections.json
    entry and no relevant RAG chunk was found — never silently fall back to a
    generic LLM guess."""
    return (
        "I don't have a verified rule or source connecting the metrics you've "
        "described yet. Rather than guess, I'd rather you give me more detail "
        "(soil, land use, rainfall, region) so I can match this to something "
        "I can actually back with a source."
    )


def validate_land_data(data: dict) -> list[str]:
    """Guardrail 3: input sanity checks. Returns a list of human-readable
    problems; empty list = all good."""
    problems = []
    soc = data.get("soil_organic_carbon_pct")
    if soc is not None and not (0 <= soc <= 100):
        problems.append(f"Soil organic carbon % of {soc} is outside the physically possible 0-100% range.")

    ph = data.get("soil_ph")
    if ph is not None and not (0 <= ph <= 14):
        problems.append(f"Soil pH of {ph} is outside the possible 0-14 scale.")

    lat = data.get("latitude")
    if lat is not None and not (-90 <= lat <= 90):
        problems.append(f"Latitude {lat} is out of range (-90 to 90).")

    lon = data.get("longitude")
    if lon is not None and not (-180 <= lon <= 180):
        problems.append(f"Longitude {lon} is out of range (-180 to 180).")

    return problems


def sanitize_user_text(text: Optional[str]) -> str:
    """Guardrail 4: prompt-injection resistance. Wraps user-supplied text in
    explicit data markers before it's ever interpolated into an LLM prompt,
    so 'ignore previous instructions' typed into a land description is just
    a string to describe, never something the model treats as a command."""
    if not text:
        return ""
    return f"<user_provided_data>{text}</user_provided_data>"


def confidence_label(chain: list[dict]) -> str:
    """Guardrail 5: confidence gating. Chain confidence is only as strong as
    its weakest verified link — never averaged up."""
    if not chain:
        return "low"
    order = {"high": 3, "medium": 2, "low": 1}
    weakest = min(chain, key=lambda step: order.get(step.get("confidence", "low"), 1))
    return weakest.get("confidence", "low")


def confidence_notice(label: str) -> Optional[str]:
    if label == "low":
        return "Low confidence — the evidence behind this link is thinner than usual. Treat this as a lead worth checking with a local expert, not a settled answer."
    return None
