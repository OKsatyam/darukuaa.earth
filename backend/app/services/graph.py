"""
LangGraph flow for /api/chat. Deliberately built as an explicit state machine
rather than a single "do everything" LLM call — this is what makes
conversational intelligence, multi-metric reasoning and the guardrails
independently visible/testable rather than baked invisibly into one prompt.

Flow:
  validate -> (invalid) -> END
           -> detect_and_check -> (missing info, no cause found) -> END (clarifying question)
                                -> reason -> (no chain found) -> END (no-match-no-claim)
                                          -> retrieve -> compose -> END
"""
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END

from app.services import connections as conn
from app.services import guardrails as gr
from app.services import rag


class ChatState(TypedDict, total=False):
    session_id: str
    message: str
    structured: dict
    valid: bool
    guardrail_notice: Optional[str]
    detected_cause: Optional[str]
    missing: List[str]
    chain: List[dict]
    rag_hits: List[dict]
    reply_text: str
    clarifying_question: Optional[str]
    recommendation: Optional[dict]


def validate_node(state: ChatState) -> ChatState:
    message = state.get("message", "") or ""
    structured = state.get("structured", {}) or {}

    if not gr.is_in_domain(message) and not structured:
        state["valid"] = False
        state["guardrail_notice"] = (
            "That's outside what I can help with — I only reason about soil, land use, "
            "biodiversity, climate and human-impact questions for a piece of land."
        )
        state["reply_text"] = state["guardrail_notice"]
        return state

    problems = gr.validate_land_data(structured)
    if problems:
        state["valid"] = False
        state["guardrail_notice"] = "I can't use this input as given:\n- " + "\n- ".join(problems)
        state["reply_text"] = state["guardrail_notice"]
        return state

    state["valid"] = True
    return state


def detect_and_check_node(state: ChatState) -> ChatState:
    message = gr.sanitize_user_text(state.get("message", ""))
    structured = state.get("structured", {}) or {}

    cause = conn.detect_cause(state.get("message", ""), structured)
    missing = conn.missing_categories(structured, state.get("message", ""))

    state["detected_cause"] = cause
    state["missing"] = missing

    if not cause and missing:
        state["clarifying_question"] = (
            "Can you tell me more about your " + ", ".join(missing) + "? "
            "That's what I need to give you a grounded recommendation rather than a generic one."
        )
        state["reply_text"] = state["clarifying_question"]

    return state


def reason_node(state: ChatState) -> ChatState:
    cause = state.get("detected_cause")
    chain = conn.walk_chain(cause) if cause else []
    state["chain"] = chain

    if not chain:
        state["reply_text"] = gr.no_match_message()

    return state


def retrieve_node(state: ChatState) -> ChatState:
    chain = state.get("chain", [])
    query = " ".join(f"{step['cause']} {step['effect']}" for step in chain) or state.get("message", "")
    hits = rag.retrieve(query, top_k=2)
    state["rag_hits"] = hits
    return state


def compose_node(state: ChatState) -> ChatState:
    chain = state.get("chain", [])
    hits = state.get("rag_hits", [])

    confidence = gr.confidence_label(chain)
    notice = gr.confidence_notice(confidence)

    first_step = chain[0]
    last_effect = chain[-1]["effect"]
    impacted_metrics = list({step["cause"] for step in chain} | {step["effect"] for step in chain})

    action_map = {
        "soil_organic_carbon": "Introduce agroforestry / intercropping",
        "land_use_monoculture": "Diversify away from monoculture toward mixed cropping or agroforestry",
        "land_use_change": "Halt further land-use conversion and prioritize restoration of natural cover",
        "water_availability": "Restore/protect wetland and groundwater recharge areas",
        "agroforestry_adoption": "Continue and expand the agroforestry system already in place",
        "pollinator_presence": "Reduce pesticide use and add pollinator-friendly flowering borders",
    }
    action = action_map.get(first_step["cause"], f"Address {first_step['cause']}")

    chain_text = " → ".join([chain[0]["cause"]] + [s["effect"] for s in chain])
    explanation = (
        f"{first_step['mechanism']} Regionally: {first_step['magnitude']} "
        f"({first_step['region_context']}). This connects through: {chain_text}."
    )

    time_horizons = [s["time_horizon"] for s in chain]
    time_horizon = max(set(time_horizons), key=time_horizons.count)

    recommendation = {
        "action": action,
        "explanation": explanation,
        "impacted_metrics": impacted_metrics,
        "time_horizon": time_horizon,
        "confidence": confidence,
        "reasoning_chain": [
            {
                "cause": s["cause"],
                "effect": s["effect"],
                "mechanism": s["mechanism"],
                "magnitude": s["magnitude"],
                "mechanism_source": s["mechanism_source"],
                "regional_source": s["regional_source"],
            }
            for s in chain
        ],
        "retrieved_sources": [
            {"source_file": h["source_file"], "excerpt": h["text"][:280]} for h in hits
        ],
    }

    reply_lines = [f"**{action}**", "", explanation]
    if notice:
        reply_lines.append("")
        reply_lines.append(f"_{notice}_")

    state["recommendation"] = recommendation
    state["reply_text"] = "\n".join(reply_lines)
    return state


def route_after_validate(state: ChatState) -> str:
    return "detect_and_check" if state.get("valid") else END


def route_after_detect(state: ChatState) -> str:
    return "reason" if state.get("detected_cause") else END


def route_after_reason(state: ChatState) -> str:
    return "retrieve" if state.get("chain") else END


def build_graph():
    graph = StateGraph(ChatState)
    graph.add_node("validate", validate_node)
    graph.add_node("detect_and_check", detect_and_check_node)
    graph.add_node("reason", reason_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("compose", compose_node)

    graph.set_entry_point("validate")
    graph.add_conditional_edges("validate", route_after_validate, {"detect_and_check": "detect_and_check", END: END})
    graph.add_conditional_edges("detect_and_check", route_after_detect, {"reason": "reason", END: END})
    graph.add_conditional_edges("reason", route_after_reason, {"retrieve": "retrieve", END: END})
    graph.add_edge("retrieve", "compose")
    graph.add_edge("compose", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_chat(session_id: str, message: str = "", structured: dict | None = None) -> ChatState:
    app_graph = get_graph()
    initial_state: ChatState = {
        "session_id": session_id,
        "message": message or "",
        "structured": structured or {},
    }
    return app_graph.invoke(initial_state)
