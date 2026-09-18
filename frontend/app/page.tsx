"use client";

import { useEffect, useRef, useState } from "react";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import StructuredPanel from "@/components/StructuredPanel";
import { getOrCreateSessionId, sendChatMessage, startNewSession } from "@/lib/api";
import { ChatMessageData, LandData } from "@/lib/types";

const WELCOME: ChatMessageData = {
  role: "assistant",
  text:
    "Tell me about a piece of land — soil, crops, rainfall, region — and I'll trace what that means for biodiversity, carbon and water, with sources. You can also fill in the land data panel above the message box.",
};

export default function Home() {
  const [sessionId, setSessionId] = useState<string>("");
  const [landData, setLandData] = useState<LandData>({});
  const [messages, setMessages] = useState<ChatMessageData[]>([WELCOME]);
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSessionId(getOrCreateSessionId());
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleNewChat = () => {
    const id = startNewSession();
    setSessionId(id);
    setMessages([WELCOME]);
    setLandData({});
  };

  const handleSend = async (text: string) => {
    if (!sessionId) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setSending(true);

    try {
      const cleanedLandData = Object.fromEntries(
        Object.entries(landData).filter(([, v]) => v !== undefined && v !== "")
      ) as LandData;

      const res = await sendChatMessage({
        session_id: sessionId,
        message: text,
        structured_data: Object.keys(cleanedLandData).length ? cleanedLandData : undefined,
      });

      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: res.reply_text,
          recommendation: res.recommendation,
          isGuardrail: !!res.guardrail_notice,
        },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: "Couldn't reach the backend. Is the FastAPI server running (uvicorn app.main:app)?",
          isGuardrail: true,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <main
      style={{
        maxWidth: 720,
        margin: "0 auto",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        padding: "24px 16px",
      }}
    >
      <header
        style={{
          marginBottom: 16,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 12,
        }}
      >
        <div>
          <h1 className="font-display" style={{ margin: 0, fontSize: 26, color: "var(--forest-dark)" }}>
            Darukaa Biodiversity Intelligence
          </h1>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "var(--ink-soft)" }}>
            Evidence-backed soil, land-use, climate and biodiversity reasoning for India.
          </p>
        </div>
        <button
          onClick={handleNewChat}
          style={{
            flexShrink: 0,
            padding: "8px 14px",
            borderRadius: 10,
            border: "1px solid var(--border)",
            background: "#fff",
            color: "var(--forest-dark)",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          + New chat
        </button>
      </header>

      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: 12,
          overflowY: "auto",
          paddingBottom: 12,
        }}
      >
        {messages.map((m, i) => (
          <ChatMessage key={i} msg={m} />
        ))}
        {sending && (
          <div style={{ fontSize: 13, color: "var(--ink-soft)", fontStyle: "italic" }}>Reasoning…</div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10, position: "sticky", bottom: 0, background: "var(--paper)", paddingTop: 8 }}>
        <StructuredPanel value={landData} onChange={setLandData} />
        <ChatInput onSend={handleSend} disabled={sending || !sessionId} />
      </div>
    </main>
  );
}
