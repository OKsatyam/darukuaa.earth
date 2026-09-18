"use client";

import { useEffect, useRef, useState, KeyboardEvent } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

const MAX_HEIGHT = 120;

export default function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize to fit content, capped at MAX_HEIGHT (it scrolls internally
  // past that instead of growing forever). Resetting to "auto" first is what
  // lets scrollHeight shrink back down when text is deleted, not just grow —
  // without it the box would only ever get taller.
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, MAX_HEIGHT) + "px";
  }, [text]);

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Describe your land — soil, crops, rainfall, region…"
        rows={1}
        style={{
          flex: 1,
          resize: "none",
          padding: "12px 14px",
          borderRadius: 12,
          border: "1px solid var(--border)",
          fontSize: 14,
          fontFamily: "inherit",
          lineHeight: 1.4,
          maxHeight: MAX_HEIGHT,
          overflowY: "auto",
        }}
      />
      <button
        onClick={submit}
        disabled={disabled}
        style={{
          padding: "12px 20px",
          borderRadius: 12,
          border: "none",
          background: "var(--forest)",
          color: "#fff",
          fontWeight: 600,
          fontSize: 14,
          opacity: disabled ? 0.6 : 1,
        }}
      >
        Send
      </button>
    </div>
  );
}
