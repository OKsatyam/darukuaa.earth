"""
Loads connections.json and walks it as a strict, path-locked chain.

Path-locking rule (per design decision): a chain step is only followed when
the NEXT entry's `cause` exactly matches the CURRENT entry's `effect`. No
fuzzy matching, no jumping to a "related-sounding" metric. This is what
keeps multi-hop reasoning from wandering off into unrelated variables.
"""
import json
import os

CONNECTIONS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "connections.json")

# Keyword triggers used to detect which cause metric(s) a user's input maps to.
# Kept simple and explicit on purpose: a guardrail should be easy to audit,
# not a black box.
CAUSE_TRIGGERS = {
    "soil_organic_carbon": ["soil organic carbon", "soc", "low soil carbon", "poor soil carbon"],
    "land_use_monoculture": ["monoculture", "single crop", "wheat only", "mono-crop"],
    "land_use_change": ["deforest", "land use change", "converted forest", "cleared land", "cleared forest"],
    "water_availability": ["low rainfall", "low water", "drought", "water scarce", "groundwater decline", "wetland loss"],
    "agroforestry_adoption": ["agroforestry", "intercropping", "tree crop mix"],
    "pollinator_presence": ["pollinat", "bees", "bee decline", "bee population"],
}

REQUIRED_CATEGORIES = {
    "soil": ["soil_organic_carbon_pct", "soil_ph", "soil_moisture"],
    "land_use": ["land_use"],
    "climate": ["rainfall"],
    "region": ["region"],
}


def load_connections() -> list[dict]:
    with open(CONNECTIONS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["connections"]


def detect_cause(text: str, structured: dict | None = None) -> str | None:
    """Very deliberately simple keyword match — this is a guardrail-critical
    function, not a place for a fuzzy ML classifier to introduce drift.

    Priority (deliberate, user-confirmed ordering):
      1. Free-text message triggers — the user chose those words on purpose.
      2. The structured `land_use` field, checked against the SAME triggers
         (it's free-ish text too, e.g. "deforestation" or "monoculture_wheat").
      3. Remaining structured shortcuts with no natural text form (a numeric
         soil-carbon %, or a categorical rainfall level).
    This order means filling in the land-data panel can no longer silently
    override what was actually typed — e.g. a deforestation story paired
    with rainfall=low now resolves to land_use_change, not water_availability."""
    text_l = (text or "").lower()
    structured = structured or {}
    land_use_l = (structured.get("land_use") or "").lower()

    for cause, triggers in CAUSE_TRIGGERS.items():
        for trig in triggers:
            if trig in text_l:
                return cause

    for cause, triggers in CAUSE_TRIGGERS.items():
        for trig in triggers:
            if trig in land_use_l:
                return cause

    soc = structured.get("soil_organic_carbon_pct")
    if soc is not None and soc < 0.5:
        return "soil_organic_carbon"
    if "mono" in land_use_l:
        return "land_use_monoculture"
    rainfall = (structured.get("rainfall") or "").lower()
    if rainfall == "low":
        return "water_availability"

    return None


def walk_chain(start_cause: str, max_hops: int = 4) -> list[dict]:
    """Deterministic traversal. Returns [] if start_cause has no entry at all
    (caller must treat that as 'no match' — see guardrails.no_match_no_claim)."""
    connections = load_connections()
    by_cause = {}
    for c in connections:
        by_cause.setdefault(c["cause"], []).append(c)

    chain = []
    current_cause = start_cause
    visited_effects = set()

    for _ in range(max_hops):
        candidates = by_cause.get(current_cause)
        if not candidates:
            break
        step = candidates[0]  # first verified entry for this cause; no branching
        if step["effect"] in visited_effects:
            break  # avoid loops
        chain.append(step)
        visited_effects.add(step["effect"])
        current_cause = step["effect"]  # exact-match hand-off, no deviation

    return chain


def missing_categories(structured: dict | None, text: str) -> list[str]:
    """Used by the clarifying-question step. A category counts as 'present'
    if either the structured field is set or the raw text plausibly mentions it."""
    structured = structured or {}
    text_l = (text or "").lower()
    missing = []

    if not any(structured.get(f) for f in REQUIRED_CATEGORIES["soil"]) and "soil" not in text_l and "carbon" not in text_l:
        missing.append("soil health (organic carbon %, pH, or moisture)")
    if not structured.get("land_use") and "crop" not in text_l and "land" not in text_l and "forest" not in text_l:
        missing.append("land use / land cover type")
    if not structured.get("rainfall") and "rain" not in text_l and "water" not in text_l and "drought" not in text_l:
        missing.append("climate (rainfall pattern)")
    if not structured.get("region") and "region" not in text_l and "india" not in text_l and any(
        state not in text_l for state in []
    ):
        # region is soft-required; don't block on it alone
        pass

    return missing
