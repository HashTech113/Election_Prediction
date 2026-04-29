export type Party = "LDF" | "UDF" | "NDA" | "OTHERS";

export type PredictionRow = {
  ac_no?: number;
  constituency: string;
  district: string;
  predicted: Party;
  confidence: number;
  LDF: number;
  UDF: number;
  NDA: number;
  OTHERS: number;
};

export type SeatCounts = Record<Party, number>;

export type PredictionsMeta = {
  api_version?: string;
  source_file: string;
  source_path?: string;
  source_last_modified_utc?: string | null;
  source_sha256?: string | null;
  fallback_in_use: boolean;
  allow_assembly_fallback?: boolean;
  total_constituencies: number;
  seat_counts: SeatCounts;
  projected_winner: Party | "-";
};

export type HealthResponse = {
  status: "ok" | "error";
  api_version?: string;
  meta?: PredictionsMeta;
  error?: string;
};

// ---- Scenario projections -------------------------------------------------

export type ScenarioName =
  | "base_model"
  | "votevibe"
  | "cvoter"
  | "final_weighted";

export type PredictionLevel =
  | "long_term_trend"
  | "recent_swing"
  | "live_intelligence_score";

export type ScenarioConstituency = {
  constituency: string;
  district: string;
  winner: Party;
  confidence: number;
  LDF: number;
  UDF: number;
  NDA: number;
  OTHERS: number;
  base_model_winner: Party;
  changed_from_base: boolean;
  scenario_source?: string | null;
  scenario_notes?: string | null;
};

export type KeralaScenarioResponse = {
  scenario: ScenarioName;
  scenario_name: string;
  prediction_level: PredictionLevel;
  result_status: string;
  counting_date: string;
  seat_counts: SeatCounts;
  vote_share_estimate: SeatCounts;
  confidence_level: number;
  constituencies: ScenarioConstituency[];
  changed_seats: ScenarioConstituency[];
  notes: string;
};

export const SCENARIO_LABELS: Record<ScenarioName, string> = {
  base_model: "Base Model",
  votevibe: "VoteVibe Scenario",
  cvoter: "C-Voter Scenario",
  final_weighted: "Final Weighted Scenario",
};

export const PREDICTION_LEVEL_LABELS: Record<PredictionLevel, string> = {
  long_term_trend: "Long-Term Trend",
  recent_swing: "Recent Swing",
  live_intelligence_score: "Live Intelligence Score",
};

// ---- Per-lens summary (sent by GET /api/predictions/lens) ----------------

export type LensName =
  | "historical_projection"
  | "long_term_trend"
  | "recent_swing"
  | "final_prediction";

export type LensSummary = {
  lens: LensName;
  label: string;
  total_constituencies: number;
  valid_winner_rows: number;
  seat_counts: SeatCounts;
  projected_winner: Party | "N/A";
  average_score: number | null;
  data_reference: string;
  source_file: string;
  rejected_winner_rows: number;
  rejected_winner_sample: string[];
  rows: PredictionRow[];
};

// ---- Projection summary tabs (UI-only; not sent to backend) --------------

export type ProjectionTab =
  | "historical_projection"
  | "long_term_trend"
  | "recent_swing"
  | "live_intelligence_score";

export type ProjectionSummary = {
  tab: ProjectionTab;
  label: string;
  totalConstituencies: number;
  dataReference: string;
  /** "LDF" / "UDF" / "NDA" / "OTHERS" / "N/A". */
  projectedWinner: string;
  /** Fraction in [0, 1], or null when the lens has no available data. */
  averageWinningScore: number | null;
  interpretation: string;
};

export const PROJECTION_TAB_LABELS: Record<ProjectionTab, string> = {
  historical_projection: "Historical Projection",
  long_term_trend: "Long-Term Trend",
  recent_swing: "Recent Swing",
  live_intelligence_score: "Live Intelligence Score",
};

// Values come from backend/data_files/kerala_past_election_projection_summary.csv,
// produced by `python backend/generate_scores.py`. Re-bake when that file changes.
//
// First three lenses use REAL historical aggregate data (no 2026 blend).
// Live Intelligence is the only projection-based row.
//
// dataReference is a short year-range label for display. The full source file
// list is documented inside the projection-summary CSV's `source_files` column.
export const PROJECTION_SUMMARIES: Record<ProjectionTab, ProjectionSummary> = {
  historical_projection: {
    tab: "historical_projection",
    label: "Historical Projection",
    totalConstituencies: 140,
    dataReference: "2011 – 2026",
    projectedWinner: "N/A — Data under validation",
    averageWinningScore: null,
    interpretation:
      "2011 Assembly and 2014 Lok Sabha AC-segment data are not present in the " +
      "uploaded dataset, and 2016 constituency-level labels are currently under " +
      "validation. This lens cannot be computed until those gaps are filled. " +
      "Pre-result intelligence, not official election result.",
  },
  long_term_trend: {
    tab: "long_term_trend",
    label: "Long-Term Trend",
    totalConstituencies: 140,
    dataReference: "2014 – 2026",
    projectedWinner: "N/A — Data under validation",
    averageWinningScore: null,
    interpretation:
      "Long-Term Trend depends on 2016 constituency-level results, which are " +
      "currently under validation (state total = 91 LDF / 47 UDF / 1 NDA / 1 OTHERS, " +
      "but the per-constituency labels in kerala_assembly_2026.csv currently sum to " +
      "78 LDF / 61 UDF / 1 NDA — a 13-seat gap). This lens is intentionally suppressed " +
      "until the per-AC labels are reconciled against the ECI 2016 archive. " +
      "Pre-result intelligence, not official election result.",
  },
  recent_swing: {
    tab: "recent_swing",
    label: "Recent Swing",
    totalConstituencies: 140,
    dataReference: "2021 – 2026",
    projectedWinner: "LDF",
    averageWinningScore: 0.4033,
    interpretation:
      "Reflects 2021 Assembly actual result baseline (LDF 99, UDF 41). Pre-result intelligence, not official election result.",
  },
  live_intelligence_score: {
    tab: "live_intelligence_score",
    label: "Live Intelligence Score",
    totalConstituencies: 140,
    dataReference: "LIVE DATA",
    projectedWinner: "UDF",
    averageWinningScore: 0.4353,
    interpretation:
      "Based on projected 2026 vote share data. Pre-result intelligence, not official election result.",
  },
};
