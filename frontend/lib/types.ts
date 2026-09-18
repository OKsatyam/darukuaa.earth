// Mirrors backend/app/models/schemas.py — keep these two in sync by hand
// (small enough surface that a codegen step isn't worth it for this build).

export interface LandData {
  soil_organic_carbon_pct?: number;
  soil_ph?: number;
  soil_moisture?: "low" | "medium" | "high" | "";
  rainfall?: "low" | "medium" | "high" | "";
  land_use?: string;
  region?: string;
  latitude?: number;
  longitude?: number;
}

export interface ChainStep {
  cause: string;
  effect: string;
  mechanism: string;
  magnitude: string;
  mechanism_source: string;
  regional_source: string;
}

export interface SourceRef {
  source_file: string;
  excerpt: string;
}

export interface Recommendation {
  action: string;
  explanation: string;
  impacted_metrics: string[];
  time_horizon: string;
  confidence: "high" | "medium" | "low";
  reasoning_chain: ChainStep[];
  retrieved_sources: SourceRef[];
}

export interface ChatResponse {
  session_id: string;
  reply_text: string;
  clarifying_question?: string | null;
  recommendation?: Recommendation | null;
  guardrail_notice?: string | null;
}

export interface ChatRequest {
  session_id: string;
  message?: string;
  structured_data?: LandData;
}

export type ChatRole = "user" | "assistant";

export interface ChatMessageData {
  role: ChatRole;
  text: string;
  recommendation?: Recommendation | null;
  isGuardrail?: boolean;
}
