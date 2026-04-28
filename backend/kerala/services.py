"""Data-loading and meta-building helpers shared by the FastAPI routers.

Two CSVs are read here, neither of which this module ever writes:

* ``predictions_2026.csv`` — trained model output, 140 rows, columns
  ``constituency, district, predicted, confidence, LDF, UDF, NDA, OTHERS``.
* ``kerala_prediction_scenarios_2026.csv`` — scenario overlay produced by
  ``build_scenarios.py``, 140 rows, columns ``base_model_winner``,
  ``base_model_<party>_pct``, ``votevibe_winner``, ``votevibe_<party>_pct``,
  plus ``region_5way``, ``scenario_source``, ``scenario_notes``.

The active dashboard scenario is selected via the ``ACTIVE_PREDICTION_SCENARIO``
env variable (default ``votevibe``). All ``/api/predictions*`` responses route
through ``load_active_predictions()`` so the dashboard always sees the active
scenario, while the per-scenario endpoint can still serve any scenario by name.
"""
from __future__ import annotations

import csv
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA_CSV_DIR = ROOT / "data" / "csv"
PREDICTIONS_FILE = DATA_CSV_DIR / "predictions_2026.csv"
SCENARIOS_FILE = DATA_CSV_DIR / "kerala_prediction_scenarios_2026.csv"
ASSEMBLY_FALLBACK_FILE = DATA_CSV_DIR / "kerala_assembly_2026.csv"
PARTIES = ("LDF", "UDF", "NDA", "OTHERS")
API_VERSION = "2026-04-12.1"

SCENARIO_KEYS = ("base_model", "votevibe")
PREDICTION_LEVELS = ("long_term_trend", "recent_swing", "live_intelligence_score")

# ---- Per-lens summary endpoint -------------------------------------------
# Each lens reads its own pre-built CSV (produced by build_historical_trend_swing.py
# and generate_scores.py). The dashboard's AnalysisHero uses these to surface
# real per-lens variation (different seat counts per tab) without recomputing
# anything on the fly.
LENS_NAMES = (
    "historical_projection",
    "long_term_trend",
    "recent_swing",
    "final_prediction",
)

LENS_SOURCES: dict[str, dict] = {
    "historical_projection": {
        "file": "kerala_actual_historical_trend_swing_constituencies.csv",
        "winner_col": "2016 Assembly Actual Winner",
        "score_col": None,  # historical lens has no continuous score column
        "data_reference": "2011 – 2026",
        "label": "Historical Projection",
    },
    "long_term_trend": {
        "file": "kerala_2026_long_term_trend_sheet.csv",
        "winner_col": "analysis_predicted",
        "score_col": "long_term_trend_score",
        "data_reference": "2014 – 2026",
        "label": "Long-Term Trend",
    },
    "recent_swing": {
        "file": "kerala_2026_recent_swing_sheet.csv",
        "winner_col": "analysis_predicted",
        "score_col": "recent_swing_score",
        "data_reference": "2024 – 2026",
        "label": "Recent Swing",
    },
    "final_prediction": {
        "file": "kerala_2026_final_prediction_score.csv",
        "winner_col": "final_predicted",
        "score_col": "final_prediction_score",
        "data_reference": "Live Data",
        "label": "Live Intelligence Score",
    },
}

SCENARIO_LABELS: dict[str, str] = {
    "base_model": "Base Model",
    "votevibe": "VoteVibe Scenario",
}

SCENARIO_NOTES: dict[str, str] = {
    "base_model": (
        "Trained constituency-level model output (predictions_2026.csv). "
        "No survey overlay applied."
    ),
    "votevibe": (
        "Adjusted toward the VoteVibe / CNN-News18 survey midpoint "
        "(LDF 68-74, UDF 64-70, NDA 1-3). Active dashboard scenario."
    ),
}

# Documented expected aggregate seat counts per scenario. Used by
# ``validate_scenario_seats``. Keep in sync with build_scenarios.py.
EXPECTED_SEAT_COUNTS: dict[str, dict[str, int]] = {
    "base_model": {"LDF": 69, "UDF": 60, "NDA": 7, "OTHERS": 4},
    "votevibe": {"LDF": 74, "UDF": 65, "NDA": 1, "OTHERS": 0},
}

NO_STORE_CACHE_HEADER = "no-store, no-cache, must-revalidate, max-age=0"
NO_STORE_HEADERS: dict[str, str] = {
    "Cache-Control": NO_STORE_CACHE_HEADER,
    "Pragma": "no-cache",
    "Expires": "0",
}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    raw = raw.strip()
    return raw or default


ALLOW_ASSEMBLY_FALLBACK = _env_flag("ALLOW_ASSEMBLY_FALLBACK", default=False)
ACTIVE_PREDICTION_SCENARIO = _env_str("ACTIVE_PREDICTION_SCENARIO", "votevibe")
if ACTIVE_PREDICTION_SCENARIO not in SCENARIO_KEYS:
    raise RuntimeError(
        f"ACTIVE_PREDICTION_SCENARIO={ACTIVE_PREDICTION_SCENARIO!r} is not a known "
        f"scenario. Expected one of {list(SCENARIO_KEYS)}."
    )


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---- Base / fallback loaders --------------------------------------------

def _load_rows_from_predictions_file() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with PREDICTIONS_FILE.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            rows.append(
                {
                    "constituency": row.get("constituency", ""),
                    "district": row.get("district", ""),
                    "predicted": row.get("predicted", ""),
                    "confidence": _to_float(row.get("confidence", 0)),
                    "LDF": _to_float(row.get("LDF", 0)),
                    "UDF": _to_float(row.get("UDF", 0)),
                    "NDA": _to_float(row.get("NDA", 0)),
                    "OTHERS": _to_float(row.get("OTHERS", 0)),
                }
            )
    return rows


def _load_rows_from_assembly_fallback() -> list[dict[str, Any]]:
    if not ASSEMBLY_FALLBACK_FILE.exists():
        raise FileNotFoundError(
            f"Neither {PREDICTIONS_FILE.name} nor {ASSEMBLY_FALLBACK_FILE} was found. "
            "Run create_dataset.py and train.py before starting the server."
        )

    rows: list[dict[str, Any]] = []
    with ASSEMBLY_FALLBACK_FILE.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            shares = {
                "LDF": _to_float(row.get("proj_2026_ldf_pct", 0)),
                "UDF": _to_float(row.get("proj_2026_udf_pct", 0)),
                "NDA": _to_float(row.get("proj_2026_nda_pct", 0)),
                "OTHERS": _to_float(row.get("proj_2026_others_pct", 0)),
            }
            predicted = row.get("proj_2026_winner", "")
            if predicted not in shares:
                predicted = max(shares, key=shares.get)
            confidence = shares.get(predicted, 0.0)

            rows.append(
                {
                    "constituency": row.get("constituency", ""),
                    "district": row.get("district", ""),
                    "predicted": predicted,
                    "confidence": confidence,
                    "LDF": shares["LDF"],
                    "UDF": shares["UDF"],
                    "NDA": shares["NDA"],
                    "OTHERS": shares["OTHERS"],
                }
            )
    return rows


def iso_mtime_utc(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except FileNotFoundError:
        return None


def file_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as fp:
            for chunk in iter(lambda: fp.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except FileNotFoundError:
        return None


def load_predictions() -> tuple[list[dict[str, Any]], Path, bool]:
    """Return ``(rows, source_file, fallback_in_use)`` for the *base model* file.

    Always reads ``predictions_2026.csv`` (or the assembly fallback when
    explicitly enabled). Used by introspection endpoints that need the raw
    trained-model output. The dashboard does NOT call this directly — it
    calls ``load_active_predictions`` instead, which respects the active
    scenario flag.
    """
    if PREDICTIONS_FILE.exists():
        return _load_rows_from_predictions_file(), PREDICTIONS_FILE, False

    if ALLOW_ASSEMBLY_FALLBACK:
        return _load_rows_from_assembly_fallback(), ASSEMBLY_FALLBACK_FILE, True

    raise FileNotFoundError(
        f"{PREDICTIONS_FILE.name} not found. Generate and deploy it with "
        "`python backend/train.py`. To intentionally use heuristic fallback "
        "data, set ALLOW_ASSEMBLY_FALLBACK=1."
    )


def seat_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {party: 0 for party in PARTIES}
    for row in rows:
        predicted = row.get("predicted")
        if predicted in counts:
            counts[predicted] += 1
    return counts


def build_predictions_meta(
    rows: list[dict[str, Any]], source_file: Path, fallback_in_use: bool
) -> dict[str, Any]:
    counts = seat_counts(rows)
    projected_winner = "-"
    if rows:
        projected_winner = max(PARTIES, key=lambda party: counts[party])
    return {
        "api_version": API_VERSION,
        "source_file": source_file.name,
        "source_path": str(source_file),
        "source_last_modified_utc": iso_mtime_utc(source_file),
        "source_sha256": file_sha256(source_file),
        "fallback_in_use": fallback_in_use,
        "allow_assembly_fallback": ALLOW_ASSEMBLY_FALLBACK,
        "active_scenario": ACTIVE_PREDICTION_SCENARIO,
        "total_constituencies": len(rows),
        "seat_counts": counts,
        "projected_winner": projected_winner,
    }


# ---- Scenario loading -----------------------------------------------------

class ScenarioFileMissing(FileNotFoundError):
    """Raised when ``kerala_prediction_scenarios_2026.csv`` has not been built."""


def _load_scenario_rows() -> list[dict[str, Any]]:
    if not SCENARIOS_FILE.exists():
        raise ScenarioFileMissing(
            f"{SCENARIOS_FILE.name} not found. Run "
            "`python backend/build_scenarios.py` to generate it."
        )
    with SCENARIOS_FILE.open("r", encoding="utf-8", newline="") as fp:
        return list(csv.DictReader(fp))


def _scenario_winner_field(scenario: str) -> str:
    return {
        "base_model": "base_model_winner",
        "votevibe": "votevibe_winner",
    }[scenario]


def _scenario_share_field(scenario: str, party: str) -> str:
    party_key = party.lower()
    if scenario == "base_model":
        return f"base_model_{party_key}_pct"
    if scenario == "votevibe":
        return f"votevibe_{party_key}_pct"
    raise ValueError(f"Unknown scenario {scenario!r}")


def _scenario_to_prediction_row(
    raw: dict[str, Any], scenario: str
) -> dict[str, Any]:
    """Convert a scenarios-CSV row into the ``PredictionRow`` shape used by
    the existing ``/api/predictions`` consumers."""
    winner = raw[_scenario_winner_field(scenario)]
    shares = {p: _to_float(raw[_scenario_share_field(scenario, p)]) for p in PARTIES}
    confidence = shares.get(winner, 0.0)
    return {
        "constituency": raw.get("constituency", ""),
        "district": raw.get("district", ""),
        "predicted": winner,
        "confidence": confidence,
        "LDF": shares["LDF"],
        "UDF": shares["UDF"],
        "NDA": shares["NDA"],
        "OTHERS": shares["OTHERS"],
    }


def load_active_predictions() -> tuple[list[dict[str, Any]], Path, bool, str]:
    """Return rows for the *currently active* scenario.

    When ``ACTIVE_PREDICTION_SCENARIO`` is ``"base_model"`` this is the same
    rows ``load_predictions`` returns. For any other scenario, it reads from
    the scenarios CSV and re-projects each row to the ``PredictionRow`` shape.

    Returns ``(rows, source_file, fallback_in_use, active_scenario)``.
    """
    if ACTIVE_PREDICTION_SCENARIO == "base_model":
        rows, source_file, fb = load_predictions()
        return rows, source_file, fb, "base_model"

    raw_rows = _load_scenario_rows()
    rows = [_scenario_to_prediction_row(r, ACTIVE_PREDICTION_SCENARIO) for r in raw_rows]
    validate_scenario_seats(ACTIVE_PREDICTION_SCENARIO, rows)
    return rows, SCENARIOS_FILE, False, ACTIVE_PREDICTION_SCENARIO


# ---- Validation -----------------------------------------------------------

class ScenarioSeatValidationError(ValueError):
    """Raised when an active scenario does not match its expected aggregate."""


def validate_scenario_seats(
    scenario: str, rows: list[dict[str, Any]]
) -> dict[str, int]:
    """Assert seat counts equal documented expectations and total 140.

    Returns the seat-counts dict on success; raises on mismatch."""
    counts = seat_counts(rows)
    total = sum(counts.values())
    if total != 140:
        raise ScenarioSeatValidationError(
            f"{scenario}: total seats {total} != 140 (counts={counts})"
        )
    expected = EXPECTED_SEAT_COUNTS.get(scenario)
    if expected is not None and counts != expected:
        raise ScenarioSeatValidationError(
            f"{scenario}: seat counts {counts} != expected {expected}"
        )
    return counts


# ---- Per-scenario response payloads --------------------------------------

def _vote_share_estimate(
    rows: list[dict[str, Any]], scenario: str
) -> dict[str, float]:
    if not rows:
        return {p: 0.0 for p in PARTIES}
    totals = {p: 0.0 for p in PARTIES}
    for row in rows:
        for party in PARTIES:
            totals[party] += _to_float(row.get(_scenario_share_field(scenario, party)))
    n = float(len(rows))
    return {p: round(totals[p] / n, 4) for p in PARTIES}


def build_kerala_scenario(scenario: str, level: str) -> dict[str, Any]:
    if scenario not in SCENARIO_KEYS:
        raise ValueError(
            f"Unknown scenario {scenario!r}. Expected one of {list(SCENARIO_KEYS)}."
        )
    if level not in PREDICTION_LEVELS:
        raise ValueError(
            f"Unknown prediction level {level!r}. Expected one of "
            f"{list(PREDICTION_LEVELS)}."
        )

    rows = _load_scenario_rows()
    winner_field = _scenario_winner_field(scenario)

    constituencies: list[dict[str, Any]] = []
    seat_counts_map = {p: 0 for p in PARTIES}
    confidence_total = 0.0

    for row in rows:
        winner = row[winner_field]
        shares = {p: _to_float(row[_scenario_share_field(scenario, p)]) for p in PARTIES}
        confidence = shares.get(winner, 0.0)
        confidence_total += confidence
        if winner in seat_counts_map:
            seat_counts_map[winner] += 1

        constituencies.append(
            {
                "constituency": row["constituency"],
                "district": row["district"],
                "region_5way": row.get("region_5way", ""),
                "winner": winner,
                "confidence": round(confidence, 4),
                "LDF": shares["LDF"],
                "UDF": shares["UDF"],
                "NDA": shares["NDA"],
                "OTHERS": shares["OTHERS"],
                "base_model_winner": row["base_model_winner"],
                "changed_from_base": winner != row["base_model_winner"],
                "scenario_source": row.get("scenario_source"),
                "scenario_notes": (
                    row.get("scenario_notes")
                    if winner != row["base_model_winner"]
                    else None
                ),
            }
        )

    # Validate aggregate against documented expectations.
    expected = EXPECTED_SEAT_COUNTS.get(scenario)
    total = sum(seat_counts_map.values())
    seat_validation = {
        "expected": expected,
        "actual": seat_counts_map,
        "total": total,
        "ok": total == 140 and (expected is None or seat_counts_map == expected),
    }

    changed = [c for c in constituencies if c["changed_from_base"]]
    n = len(constituencies) or 1

    return {
        "scenario": scenario,
        "scenario_name": SCENARIO_LABELS[scenario],
        "prediction_level": level,
        "result_status": "Prediction, not final result",
        "counting_date": "2026-05-04",
        "seat_counts": seat_counts_map,
        "vote_share_estimate": _vote_share_estimate(rows, scenario),
        "confidence_level": round(confidence_total / n, 4),
        "constituencies": constituencies,
        "changed_seats": changed,
        "notes": SCENARIO_NOTES[scenario],
        "seat_validation": seat_validation,
    }


def build_kerala_summary(scenario: str) -> dict[str, Any]:
    """Compact summary payload matching the user-spec output."""
    if scenario not in SCENARIO_KEYS:
        raise ValueError(
            f"Unknown scenario {scenario!r}. Expected one of {list(SCENARIO_KEYS)}."
        )
    rows = _load_scenario_rows()
    winner_field = _scenario_winner_field(scenario)
    counts = {p: 0 for p in PARTIES}
    for row in rows:
        winner = row[winner_field]
        if winner in counts:
            counts[winner] += 1

    total = sum(counts.values())
    if total != 140:
        raise ScenarioSeatValidationError(
            f"{scenario}: total seats {total} != 140 (counts={counts})"
        )

    # Hide OTHERS when zero, per spec.
    seats_for_display = {p: v for p, v in counts.items() if v > 0}

    return {
        "scenario": SCENARIO_LABELS[scenario],
        "scenario_key": scenario,
        "result_status": "Prediction, not final result",
        "counting_date": "2026-05-04",
        "seats": seats_for_display,
        "total_seats": total,
        "all_seat_counts": counts,
        "active_scenario": ACTIVE_PREDICTION_SCENARIO,
    }


def list_scenarios() -> list[dict[str, str]]:
    return [
        {"key": key, "label": SCENARIO_LABELS[key], "notes": SCENARIO_NOTES[key]}
        for key in SCENARIO_KEYS
    ]


# --- Per-lens summary ------------------------------------------------------

def _load_district_map() -> dict[str, str]:
    """constituency → district from the master spine. Lens CSVs that lack
    a district column are joined to this so the table can still group by district."""
    path = DATA_CSV_DIR / "kerala_constituency_master_2026.csv"
    if not path.exists():
        return {}
    with path.open(newline="") as f:
        return {row["ac_name"]: row["district"] for row in csv.DictReader(f)}


def _to_pct(raw: str | None) -> float:
    """Parse 'ldf_score'/'_pct' values that may be 0–1 or 0–100."""
    if raw is None or raw == "":
        return 0.0
    try:
        v = float(raw)
    except ValueError:
        return 0.0
    return v / 100.0 if v > 1.0 else v


def build_lens_summary(lens: str) -> dict[str, Any]:
    """Aggregate seat counts + per-row predictions from a per-lens CSV.

    The lens CSVs are pre-built artefacts (see build_historical_trend_swing.py
    and generate_scores.py). Each one carries an opinion of who wins each
    constituency under that specific lens — so aggregating the winner column
    yields a per-lens seat distribution that can differ markedly from the
    live VoteVibe scenario.

    Aggregation rule: count of constituencies whose winner column matches each
    party. NEVER sum probabilities, average raw scores, or invent values.

    Returns a payload that includes BOTH the summary (for the KPI tile) and
    `rows` shaped like /api/predictions PredictionRow so the dashboard's
    constituency table and seat-distribution bar list can swap per tab too.
    """
    if lens not in LENS_SOURCES:
        raise ValueError(
            f"Unknown lens {lens!r}. Expected one of {list(LENS_SOURCES)}."
        )
    spec = LENS_SOURCES[lens]
    path = DATA_CSV_DIR / spec["file"]
    if not path.exists():
        raise FileNotFoundError(f"Lens source file not found: {path}")

    with path.open(newline="") as f:
        raw_rows = list(csv.DictReader(f))

    if not raw_rows:
        raise ValueError(f"Lens source file is empty: {path}")

    winner_col = spec["winner_col"]
    score_col = spec.get("score_col")
    district_map = _load_district_map()

    seat_counts = {p: 0 for p in PARTIES}
    score_values: list[float] = []
    rejected_winners: list[str] = []
    out_rows: list[dict[str, Any]] = []

    for row in raw_rows:
        raw_winner = (row.get(winner_col) or "").strip()
        winner_upper = raw_winner.upper()
        # OTHERS / "Not available" / blank → predicted = "OTHERS" so the row
        # is still rendered but doesn't pollute the seat count for a real party.
        if winner_upper in seat_counts:
            seat_counts[winner_upper] += 1
            predicted = winner_upper
        else:
            rejected_winners.append(raw_winner)
            predicted = "OTHERS"

        score_val = 0.0
        if score_col:
            try:
                score_val = float(row[score_col])
            except (KeyError, TypeError, ValueError):
                score_val = 0.0
            score_values.append(score_val)

        # Per-party shares — present in score sheets, absent in the historical CSV.
        ldf = _to_pct(row.get("ldf_score"))
        udf = _to_pct(row.get("udf_score"))
        nda = _to_pct(row.get("nda_score"))
        others = _to_pct(row.get("others_score"))
        # Historical CSV: derive a 1-hot share from the actual winner so the
        # bar visualisation still has signal.
        if (ldf + udf + nda + others) == 0.0 and predicted in PARTIES:
            shares = {p: 0.0 for p in PARTIES}
            shares[predicted] = 1.0
            ldf, udf, nda, others = shares["LDF"], shares["UDF"], shares["NDA"], shares["OTHERS"]

        constituency = row.get("constituency") or row.get("ac_name") or ""
        district = (
            row.get("district")
            or district_map.get(constituency, "")
        )

        out_rows.append(
            {
                "constituency": constituency,
                "district": district,
                "predicted": predicted,
                "confidence": round(score_val, 4) if score_col else (1.0 if predicted in PARTIES else 0.0),
                "LDF": round(ldf, 4),
                "UDF": round(udf, 4),
                "NDA": round(nda, 4),
                "OTHERS": round(others, 4),
            }
        )

    total = sum(seat_counts.values())
    projected_winner = (
        max(seat_counts, key=seat_counts.get) if total > 0 else "N/A"
    )
    average_score = (
        round(sum(score_values) / len(score_values), 4) if score_values else None
    )

    return {
        "lens": lens,
        "label": spec["label"],
        "total_constituencies": len(raw_rows),
        "valid_winner_rows": total,
        "seat_counts": seat_counts,
        "projected_winner": projected_winner,
        "average_score": average_score,
        "data_reference": spec["data_reference"],
        "source_file": spec["file"],
        "rejected_winner_rows": len(rejected_winners),
        "rejected_winner_sample": list({rw for rw in rejected_winners[:5]}),
        "rows": out_rows,
    }
