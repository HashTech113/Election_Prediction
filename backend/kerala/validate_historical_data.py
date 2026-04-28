"""Audit Kerala historical / trend / swing datasets for internal consistency.

Run from the repo root:

    python backend/kerala/validate_historical_data.py

This script does NOT validate facts against external authorities (ECI, opencity,
Trivedi Centre). It surfaces:

  1. Row counts per file
  2. Schema shape (required columns present)
  3. State-level totals match the official party-totals CSVs
  4. Per-AC files cover all 140 constituencies with no duplicates
  5. Per-AC alliance distributions agree with state seat totals
  6. Cross-table winner agreement (comparison_table vs per-year files)
  7. Columns that are constant across all 140 ACs (likely state-level broadcast)
  8. Constituency-name consistency across files

Exit code is non-zero when any **structural** check fails. Factual mismatches
emit warnings — they require human review against an authoritative source.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_DIR = ROOT / "data" / "csv"

# Per-year state-level files: must each have 4 rows (LDF/UDF/NDA/OTHERS)
# and seats summing to total_seats.
STATE_FILES = {
    "kerala_assembly_election_2016.csv":   {"total_seats": 140, "winner": "LDF"},
    "kerala_assembly_election_2021.csv":   {"total_seats": 140, "winner": "LDF"},
    "kerala_lok_sabha_election_2014.csv":  {"total_seats": 20,  "winner": "UDF"},
    "kerala_lok_sabha_election_2019.csv":  {"total_seats": 20,  "winner": "UDF"},
    "kerala_lok_sabha_election_2024.csv":  {"total_seats": 20,  "winner": "UDF"},
}

REQUIRED_PARTIES = ("LDF", "UDF", "NDA", "OTHERS")


# --------------------------------------------------------------------- helpers
def read_csv(name: str) -> list[dict]:
    path = CSV_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    with open(path) as f:
        return list(csv.DictReader(f))


def normalize_party(value: str) -> str:
    return value.strip().upper()


# --------------------------------------------------------------------- checks
class Audit:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)
        print(f"  ✗ {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        print(f"  ⚠ {msg}")

    def ok(self, msg: str) -> None:
        self.info.append(msg)
        print(f"  ✓ {msg}")


def check_state_files(audit: Audit) -> None:
    print("\n[1] State-level per-year files — schema, totals, parties")
    for fname, spec in STATE_FILES.items():
        try:
            rows = read_csv(fname)
        except FileNotFoundError:
            audit.err(f"{fname} is missing")
            continue
        cols = set((rows[0].keys() if rows else []))
        required = {"party", "seats_won", "vote_share"}
        if not required.issubset(cols):
            audit.err(f"{fname}: missing columns {required - cols}")
            continue

        parties = [normalize_party(r["party"]) for r in rows]
        missing = set(REQUIRED_PARTIES) - set(parties)
        if missing:
            audit.warn(
                f"{fname}: missing party row(s) {missing} — alliance won 0 seats but row "
                f"should still exist for schema completeness and accurate vote-share swing math"
            )

        try:
            sum_seats = sum(int(r["seats_won"]) for r in rows)
        except (KeyError, ValueError):
            audit.err(f"{fname}: seats_won column is non-integer or missing")
            continue
        if sum_seats != spec["total_seats"]:
            audit.err(
                f"{fname}: seats_won sums to {sum_seats}, expected {spec['total_seats']}"
            )
        else:
            audit.ok(f"{fname}: {sum_seats}/{spec['total_seats']} seats summed")

        try:
            top_party = max(rows, key=lambda r: int(r["seats_won"]))
            top = normalize_party(top_party["party"])
            if top != spec["winner"]:
                audit.err(
                    f"{fname}: top-party = {top}, comparison-table says {spec['winner']}"
                )
        except Exception as exc:  # pragma: no cover - schema already covered
            audit.err(f"{fname}: failed to determine winner — {exc}")


def check_constituency_spine(audit: Audit) -> set[str]:
    print("\n[2] Constituency spine + per-AC file coverage")
    try:
        master = read_csv("kerala_constituency_master_2026.csv")
    except FileNotFoundError:
        audit.err("kerala_constituency_master_2026.csv missing — cannot validate spine")
        return set()
    if len(master) != 140:
        audit.err(f"master spine has {len(master)} rows, expected 140")
    spine = {r["ac_name"] for r in master}
    if len(spine) != len(master):
        dups = [n for n, c in Counter(r["ac_name"] for r in master).items() if c > 1]
        audit.err(f"master spine has duplicate ac_name: {dups}")
    else:
        audit.ok(f"master spine: 140 unique ac_name values")

    for fname, key in [
        ("kerala_assembly_2026.csv", "constituency"),
        ("kerala_actual_historical_trend_swing_constituencies.csv", "constituency"),
        ("kerala_2026_long_term_trend_sheet.csv", "constituency"),
        ("kerala_2026_recent_swing_sheet.csv", "constituency"),
        ("kerala_2026_live_intelligence_score_sheet.csv", "constituency"),
        ("kerala_2026_final_prediction_score.csv", "constituency"),
    ]:
        try:
            rows = read_csv(fname)
        except FileNotFoundError:
            audit.err(f"{fname} missing")
            continue
        names = {r[key] for r in rows}
        diff = spine ^ names
        if len(rows) != 140 or len(names) != 140 or diff:
            audit.err(
                f"{fname}: rows={len(rows)}, unique={len(names)}, "
                f"diff_with_spine={len(diff)} {sorted(diff)[:5]}"
            )
        else:
            audit.ok(f"{fname}: 140 rows, all constituencies match spine")
    return spine


def check_per_ac_alliance_distribution(audit: Audit) -> None:
    print("\n[3] Per-AC alliance distributions vs state totals")
    asm = read_csv("kerala_assembly_2026.csv")

    distribs = {
        "winner_2016": Counter(r["winner_2016"] for r in asm),
        "winner_2021": Counter(r["winner_2021"] for r in asm),
        "ls2024_winner": Counter(r["ls2024_winner"] for r in asm),
    }

    def positive(d):  # drop zero-seat parties so comparison is apples-to-apples
        return {k: v for k, v in d.items() if v > 0}

    state_2016 = positive({normalize_party(r["party"]): int(r["seats_won"])
                           for r in read_csv("kerala_assembly_election_2016.csv")})
    state_2021 = positive({normalize_party(r["party"]): int(r["seats_won"])
                           for r in read_csv("kerala_assembly_election_2021.csv")})

    print(f"  state 2016 totals (winners only): {state_2016}")
    print(f"  per-AC winner_2016 distribution:  {dict(distribs['winner_2016'])}")
    if dict(distribs["winner_2016"]) != state_2016:
        audit.err(
            "winner_2016 per-AC distribution disagrees with kerala_assembly_election_2016.csv. "
            "Either the per-AC labels are wrong or the state-level file is. "
            "Resolve by cross-referencing ECI archive 2016 result PDFs / opencity AC-wise extract."
        )
    else:
        audit.ok("winner_2016 distribution matches state totals")

    print(f"  state 2021 totals (winners only): {state_2021}")
    print(f"  per-AC winner_2021 distribution:  {dict(distribs['winner_2021'])}")
    if dict(distribs["winner_2021"]) != state_2021:
        audit.err("winner_2021 per-AC distribution disagrees with state totals")
    else:
        audit.ok("winner_2021 distribution matches state totals")

    state_ls24 = positive({normalize_party(r["party"]): int(r["seats_won"])
                           for r in read_csv("kerala_lok_sabha_election_2024.csv")})
    print(f"  state 2024 LS totals (winners only): {state_ls24}")
    print(f"  per-AC ls2024_winner distribution:   {dict(distribs['ls2024_winner'])}")
    expected = {p: c * 7 for p, c in state_ls24.items()}
    actual = dict(distribs["ls2024_winner"])
    if actual != expected:
        audit.warn(
            f"ls2024_winner distribution {actual} doesn't match expected {expected} "
            f"(each LS covers exactly 7 ACs in Kerala). May indicate AC-LS mapping drift."
        )
    else:
        audit.ok("ls2024_winner per-AC distribution matches LS-segment math (×7 ACs each)")


def check_constant_columns(audit: Audit) -> None:
    print("\n[4] Per-AC columns that are constant across all 140 rows (state-level broadcast)")
    files_to_check = [
        ("kerala_assembly_2026.csv", {
            "constituency", "district", "region_5way", "is_reserved",
            "winner_name_2021",  # candidate names trivially unique, skip
            "fin_crisis_impact", "wildlife_conflict_impact",
        }),
        ("kerala_actual_historical_trend_swing_constituencies.csv", {
            "ac_no", "constituency", "district", "region_5way", "reservation",
        }),
    ]
    for fname, skip in files_to_check:
        rows = read_csv(fname)
        for col in rows[0].keys():
            if col in skip:
                continue
            uniq = {r[col] for r in rows}
            if len(uniq) == 1:
                value = next(iter(uniq))
                if "Not available" in value or "Cannot calculate" in value:
                    print(f"    ⓘ {fname}::{col} = {value!r} (acknowledged data gap)")
                else:
                    audit.warn(
                        f"{fname}::{col} is constant ({value!r}) — likely a state-level "
                        f"value broadcast; per-AC analysis derived from this column will be "
                        f"a constant function of the state total"
                    )


def check_cross_tables(audit: Audit) -> None:
    print("\n[5] Cross-table winner agreement")
    try:
        cmp_rows = read_csv("kerala_election_comparison_table.csv")
    except FileNotFoundError:
        audit.err("kerala_election_comparison_table.csv missing")
        return
    for r in cmp_rows:
        year = r["year"]
        etype = r["election"]
        expected = normalize_party(r["winner"])
        fname = (
            f"kerala_assembly_election_{year}.csv" if etype == "Assembly"
            else f"kerala_lok_sabha_election_{year}.csv"
        )
        try:
            per_year = read_csv(fname)
        except FileNotFoundError:
            audit.warn(f"{year} {etype}: cross-table refers to missing file {fname}")
            continue
        actual = normalize_party(max(per_year, key=lambda x: int(x["seats_won"]))["party"])
        if expected != actual:
            audit.err(
                f"{year} {etype}: comparison_table says {expected}, per-year says {actual}"
            )
        else:
            audit.ok(f"{year} {etype}: {expected} (consistent across files)")


def check_data_gaps(audit: Audit) -> None:
    print("\n[6] Acknowledged data gaps")
    rows = read_csv("kerala_actual_historical_trend_swing_constituencies.csv")
    for col in rows[0].keys():
        values = {r[col] for r in rows}
        if len(values) == 1:
            v = next(iter(values))
            if "Not available" in v or "Cannot calculate" in v:
                print(f"    ⓘ Column {col!r}: all 140 rows = {v!r}")
                print(f"       — fill from authoritative AC-wise source to enable this lens")


# --------------------------------------------------------------------- main
def main() -> int:
    audit = Audit()
    print("=" * 72)
    print(" Kerala historical-data audit")
    print(f" CSV dir: {CSV_DIR}")
    print("=" * 72)

    check_state_files(audit)
    check_constituency_spine(audit)
    check_per_ac_alliance_distribution(audit)
    check_constant_columns(audit)
    check_cross_tables(audit)
    check_data_gaps(audit)

    print("\n" + "=" * 72)
    print(f" Errors:   {len(audit.errors)}")
    print(f" Warnings: {len(audit.warnings)}")
    print("=" * 72)

    return 1 if audit.errors else 0


if __name__ == "__main__":
    sys.exit(main())
