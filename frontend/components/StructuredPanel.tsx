"use client";

import { useState } from "react";
import { LandData } from "@/lib/types";

interface Props {
  value: LandData;
  onChange: (data: LandData) => void;
}

// Collapsible structured-input form — the brief's "structured input"
// requirement made concrete. Kept separate from the chat box on purpose:
// a user can fill in what they know here, describe the rest in free text,
// and the backend merges both (see routers/chat.py).
export default function StructuredPanel({ value, onChange }: Props) {
  const [open, setOpen] = useState(false);

  const set = (patch: Partial<LandData>) => onChange({ ...value, ...patch });

  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: 12, background: "#fff" }}>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          width: "100%",
          textAlign: "left",
          padding: "12px 16px",
          background: "transparent",
          border: "none",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontWeight: 600,
          fontSize: 14,
          color: "var(--forest-dark)",
        }}
      >
        <span>Land data (optional — helps me skip the guesswork)</span>
        <span>{open ? "−" : "+"}</span>
      </button>

      {open && (
        <div
          style={{
            padding: "0 16px 16px",
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 10,
          }}
        >
          <Field label="Soil organic carbon (%)">
            <input
              type="number"
              step="0.1"
              value={value.soil_organic_carbon_pct ?? ""}
              onChange={(e) =>
                set({ soil_organic_carbon_pct: e.target.value === "" ? undefined : Number(e.target.value) })
              }
              style={inputStyle}
            />
          </Field>

          <Field label="Soil pH">
            <input
              type="number"
              step="0.1"
              value={value.soil_ph ?? ""}
              onChange={(e) => set({ soil_ph: e.target.value === "" ? undefined : Number(e.target.value) })}
              style={inputStyle}
            />
          </Field>

          <Field label="Soil moisture">
            <select
              value={value.soil_moisture ?? ""}
              onChange={(e) => set({ soil_moisture: e.target.value as LandData["soil_moisture"] })}
              style={inputStyle}
            >
              <option value="">—</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </Field>

          <Field label="Rainfall">
            <select
              value={value.rainfall ?? ""}
              onChange={(e) => set({ rainfall: e.target.value as LandData["rainfall"] })}
              style={inputStyle}
            >
              <option value="">—</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </Field>

          <Field label="Land use">
            <input
              type="text"
              placeholder="e.g. monoculture_wheat"
              value={value.land_use ?? ""}
              onChange={(e) => set({ land_use: e.target.value })}
              style={inputStyle}
            />
          </Field>

          <Field label="Region">
            <input
              type="text"
              placeholder="e.g. semi-arid, Odisha"
              value={value.region ?? ""}
              onChange={(e) => set({ region: e.target.value })}
              style={inputStyle}
            />
          </Field>
        </div>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 12, color: "var(--ink-soft)" }}>
      {label}
      {children}
    </label>
  );
}

const inputStyle: React.CSSProperties = {
  padding: "8px 10px",
  borderRadius: 8,
  border: "1px solid var(--border)",
  fontSize: 13,
  fontFamily: "inherit",
};
