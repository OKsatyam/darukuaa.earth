import { ChatMessageData } from "@/lib/types";
import RecommendationCard from "./RecommendationCard";

export default function ChatMessage({ msg }: { msg: ChatMessageData }) {
  const isUser = msg.role === "user";

  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start" }}>
      <div style={{ maxWidth: "80%" }}>
        <div
          style={{
            padding: "10px 14px",
            borderRadius: 14,
            fontSize: 14,
            lineHeight: 1.5,
            background: isUser ? "var(--forest)" : msg.isGuardrail ? "var(--terracotta-soft)" : "#fff",
            color: isUser ? "#fff" : msg.isGuardrail ? "var(--terracotta)" : "var(--ink)",
            border: isUser ? "none" : "1px solid var(--border)",
            whiteSpace: "pre-wrap",
          }}
        >
          {msg.text}
        </div>
        {msg.recommendation && <RecommendationCard rec={msg.recommendation} />}
      </div>
    </div>
  );
}
