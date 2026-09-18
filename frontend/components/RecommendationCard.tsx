"use client";

import { useState } from "react";
import { Recommendation } from "@/lib/types";

const CONFIDENCE_COLOR: Record<string, string> = {
  high: "var(--chip-green)",
  medium: "var(--chip-brown)",
  low: "var(--chip-rust)",
};

const METRIC_COLORS = ["var(--chip-brown)", "var(--chip-green)", "var(--chip-rust)"];

// The output-clarity requirement made concrete: the structured recommendation
// up top (action, confidence, time horizon, metrics) is scannable in 3
// seconds; "Sources & reasoning" is collapsed by default so the retrieval
// transparency value-add doesn't bury the answer for someone in a hurry.
export default function RecommendationCard({ rec }: { rec: Recommendation }) {
  const [open, setOpen] = useState(false);

  return (
    <div
      style={{
        border: "1px solid var(--border)",
        borderRadius: 14,
        background: "#fff",
        marginTop: 8,
        overflow: "hidden",
      }}
    >
      <div style={{ padding: "16px 18px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
          <h3 className="font-display" style={{ margin: 0, fontSize: 18, color: "var(--forest-dark)" }}>
            {rec.action}
          </h3>
          <span
            style={{
              flexShrink: 0,
              fontSize: 11,
              fontWeight: 600,
              padding: "4px 10px",
              borderRadius: 999,
              color: "#fff",
              background: CONFIDENCE_COLOR[rec.confidence] || "var(--ink-soft)",
              textTransform: "uppercase",
              letterSpacing: 0.4,
            }}
          >
            {rec.confidence} confidence
          </span>
        </div>

        <p style={{ fontSize: 14, lineHeight: 1.55, color: "var(--ink)", marginTop: 10 }}>{rec.explanation}</p>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
          {rec.impacted_metrics.map((m, i) => (
            <span
              key={m}
              style={{
                fontSize: 11,
                padding: "3px 9px",
                borderRadius: 999,
                background: "var(--forest-soft)",
                color: METRIC_COLORS[i % METRIC_COLORS.length],
                fontWeight: 600,
              }}
            >
              {m.replace(/_/g, " ")}
            </span>
          ))}
          <span
            style={{
              fontSize: 11,
              padding: "3px 9px",
              borderRadius: 999,
              background: "var(--terracotta-soft)",
              color: "var(--terracotta)",
              fontWeight: 600,
            }}
          >
            {rec.time_horizon.replace(/_/g, " ")}
          </span>
        </div>
      </div>

      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          width: "100%",
          textAlign: "left",
          padding: "10px 18px",
          background: "var(--forest-soft)",
          border: "none",
          borderTop: "1px solid var(--border)",
          fontSize: 13,
          fontWeight: 600,
          color: "var(--forest-dark)",
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        <span>Sources & reasoning ({rec.reasoning_chain.length} hop{rec.reasoning_chain.length === 1 ? "" : "s"})</span>
        <span>{open ? "−" : "+"}</span>
      </button>

      {open && (
        <div style={{ padding: "14px 18px", background: "var(--forest-soft)" }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--forest-dark)", marginBottom: 8 }}>
            Reasoning chain (path-locked — each step's effect exactly matches the next step's cause)
          </div>
          <ol style={{ margin: 0, paddingLeft: 18, display: "flex", flexDirection: "column", gap: 10 }}>
            {rec.reasoning_chain.map((step, i) => (
              <li key={i} style={{ fontSize: 13, lineHeight: 1.5 }}>
                <strong>
                  {step.cause.replace(/_/g, " ")} → {step.effect.replace(/_/g, " ")}
                </strong>
                <div style={{ color: "var(--ink-soft)" }}>{step.mechanism}</div>
                <div style={{ color: "var(--rust)", marginTop: 2 }}>
                  {step.magnitude} — <em>{step.regional_source}</em>
                </div>
              </li>
            ))}
          </ol>

          {rec.retrieved_sources.length > 0 && (
            <>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--forest-dark)", margin: "14px 0 8px" }}>
                Retrieved sources
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {rec.retrieved_sources.map((s, i) => (
                  <div
                    key={i}
                    style={{
                      background: "#fff",
                      border: "1px solid var(--border)",
                      borderRadius: 8,
                      padding: "8px 10px",
                      fontSize: 12,
                    }}
                  >
                    <div style={{ fontWeight: 600, color: "var(--forest)" }}>{s.source_file}</div>
                    <div style={{ color: "var(--ink-soft)", marginTop: 2 }}>{s.excerpt}</div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
