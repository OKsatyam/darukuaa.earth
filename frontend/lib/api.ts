import { ChatRequest, ChatResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Chat request failed (${res.status})`);
  }
  return res.json();
}

const SESSION_KEY = "darukaa_session_id";

export function getOrCreateSessionId(): string {
  if (typeof window === "undefined") return "server";
  let id = window.localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    window.localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

// Starts a fresh backend session — a genuinely new session_id, not just a
// cleared chat window. Without this, "New chat" in the UI would still send
// every message under the old session_id, so the backend would keep reusing
// land_data accumulated from before the reset (see routers/chat.py's merge
// logic) — the reset would look complete on screen but not actually be one.
export function startNewSession(): string {
  if (typeof window === "undefined") return "server";
  const id = crypto.randomUUID();
  window.localStorage.setItem(SESSION_KEY, id);
  return id;
}
