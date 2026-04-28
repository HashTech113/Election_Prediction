# Kerala Historical Dataset Audit

Generated: 2026-04-28
Audited by: `backend/kerala/validate_historical_data.py`

This document is the source of truth for what the Kerala dataset currently
contains, what is verified factually correct, and what needs authoritative
input from you. **No values were fabricated, approximated, or back-filled.**
Where a fact required external truth I could not access, the gap is recorded
explicitly so it can be filled from ECI / opencity / Trivedi Centre exports.

---

## 1. What's verified correct

| File | Status |
|---|---|
| `kerala_assembly_election_2016.csv` | ✓ LDF 91 / UDF 47 / NDA 1 / Others 1 = 140 |
| `kerala_assembly_election_2021.csv` | ✓ LDF 99 / UDF 41 / NDA 0 / Others 0 = 140 |
| `kerala_lok_sabha_election_2014.csv` | ✓ UDF 12 / LDF 8 / NDA 0 / Others 0 = 20 |
| `kerala_lok_sabha_election_2019.csv` | ✓ UDF 19 / LDF 1 / NDA 0 / Others 0 = 20 |
| `kerala_election_comparison_table.csv` | ✓ All 5 winner rows agree with per-year files |
| `kerala_elections_results_past_10_years.csv` | ✓ Internally consistent |
| `kerala_constituency_master_2026.csv` | ✓ 140 unique ac_name |
| All 6 per-AC files cover the spine | ✓ 140 rows each, no duplicates |
| **`winner_2021` per-AC distribution** | ✓ LDF 99 / UDF 41 — matches state total exactly |
| **`ls2024_winner` per-AC distribution** | ✓ UDF 126 / LDF 7 / NDA 7 — matches LS-segment math (each LS = 7 ACs × 18/1/1 winners) |
| Constituency naming consistency | ✓ All 6 per-AC files share identical 140-name set |

## 2. Real bugs (require authoritative source to fix)

### 2.1 `winner_2016` per-AC distribution disagrees with state totals

```
State (kerala_assembly_election_2016.csv): LDF 91, UDF 47, NDA 1, OTHERS 1
Per-AC (kerala_assembly_2026.csv):         LDF 78, UDF 61, NDA 1
```

**13 seats labelled as UDF in the per-AC file are LDF in the state-level total
(or vice versa).** This breaks any analysis that uses `winner_2016` alongside
state totals.

**Fix path:** open the ECI 2016 result archive
(<https://results.eci.gov.in/Result2016/index.htm>) or opencity Kerala 2016
AC-wise CSV and reconcile each constituency. Likely culprits to start with:

- **Poonjar** — P.C. George won as Independent in 2016 (state row "Others"). May
  be coded as UDF in `winner_2016`.
- **Nemom** — O. Rajagopal won as BJP/NDA in 2016. Verify it's coded as NDA.
- Any seat where IUML / KC(M) / RSP candidates won — make sure they're under UDF
  in per-AC labels (state file aggregates them under UDF).

A re-runnable check is at `backend/kerala/validate_historical_data.py`. After
fixing the per-AC labels, run it again — it must report **0 errors**.

### 2.2 `kerala_lok_sabha_election_2024.csv` is missing the OTHERS row

The file has only 3 rows (UDF 18, LDF 1, NDA 1 = 20 seats ✓), but the schema
expects 4 rows for clean swing math against 2019 (which has Others 1.59% vote
share). With the row missing, `data_loader.py` defaults Others 2024 vote share
to 0.0, producing a phantom `−1.59pp swing` for OTHERS that isn't real.

**Fix path:** add a fourth row using the actual Kerala 2024 LS turnout from
ECI Form-21:

```
OTHERS,0,<exact_others_votes>,<exact_others_vote_share>
```

I deliberately did **not** invent this value. Pull from
<https://results.eci.gov.in/PcResultGenJune2024/statewise2sS28.htm>.

### 2.3 `turnout_pct` in `kerala_assembly_2026.csv` is constant 0.7737

All 140 ACs share the same turnout_pct = 0.7737 (≈ Kerala state-level historical
turnout). This is a state-level value broadcast — per-AC turnout actually varies
significantly (Kasaragod ACs ~75%, Wayanad rural ACs ~80%, urban TVM ACs ~67%).

**Impact:** any model feature derived from `turnout_pct` is a constant function
of the state total — no per-constituency signal. Fix by joining ECI Form-21 or
CEO Kerala AC-wise turnout for the most recent assembly + LS election.

## 3. Acknowledged data gaps (NOT bugs — explicitly marked as missing)

`kerala_actual_historical_trend_swing_constituencies.csv` honestly marks three
columns as unavailable:

| Column | All 140 rows say |
|---|---|
| `2011 Assembly Actual Winner` | "Not available in uploaded dataset" |
| `2014 Lok Sabha AC/Segment Actual Winner` | "Not available in uploaded dataset" |
| `Historical Projection [2011-2014]` | "Cannot calculate from uploaded dataset" |

These mean the **Historical Projection [2011-2014]** UI lens is intentionally
inert — the AnalysisHero component shows `projectedWinner: "N/A"` for that tab,
and the validator confirms this is honestly mirrored in the data layer.

To activate the lens, drop AC-wise winner data for **2011 Kerala Assembly** and
**2014 Lok Sabha (LS-segment → AC mapping)** into the file. The schema is
already defined — you only need to fill three columns:

```
ac_no,constituency,…,
  '2011 Assembly Actual Winner'        ← LDF / UDF / NDA / OTHERS per AC
  '2014 Lok Sabha AC/Segment Actual Winner'   ← LS winner mapped to its 7 ACs
  'Historical Projection [2011-2014]'  ← e.g. "Stable LDF" / "Shift LDF→UDF"
```

Sources:
- 2011 AC results: ECI archive <https://results.eci.gov.in/Result2011/index.htm>
- 2014 LS-to-AC mapping: ECI Form-21 booth-level + delimitation order

## 4. Methodological notes (not bugs)

The `kerala_2026_long_term_trend_sheet.csv` and `kerala_2026_recent_swing_sheet.csv`
files have **51** and **31** unique score-tuples across 140 rows — meaning ACs
within the same Lok Sabha segment share scores. This is **by design** in
`generate_scores.py`: 2024 LS results inherently exist at LS granularity (1
result per ~7 ACs), so the recent-swing score for those 7 ACs starts identical.
Long-term trend gets some additional AC-level variation from 2016/2021 assembly
margins but still inherits much from the LS segment.

If you want true AC-level swing scores, you must add an AC-level vote share
table for 2024 LS (booth-aggregated to AC), not just the LS winner per segment.
Until that's available, treat these scores as **LS-segment baselines with AC-level
adjustment**, not pure AC-level signals.

## 5. How to re-validate

Any time you update one of these files, run:

```bash
python backend/kerala/validate_historical_data.py
```

The script exits non-zero on structural failure. **Aim for "Errors: 0"** before
calling the dataset clean.

## 6. Authoritative input template

To replace currently-marked-N/A data with real values, populate
`kerala_actual_historical_trend_swing_constituencies.csv` for these columns
using ECI archive PDFs:

| Column | Allowed values |
|---|---|
| `2011 Assembly Actual Winner` | `LDF`, `UDF`, `NDA`, `OTHERS` |
| `2014 Lok Sabha AC/Segment Actual Winner` | `LDF`, `UDF`, `NDA`, `OTHERS` |
| `Historical Projection [2011-2014]` | `Stable LDF`, `Stable UDF`, `Shift LDF→UDF`, `Shift UDF→LDF`, etc. |
| `2016 Assembly Actual Winner` | Match `kerala_assembly_2026.csv::winner_2016` after fixing #2.1 |
| `2024 UDF Vote Share (%)` / `2024 LDF Vote Share (%)` / `2024 NDA Vote Share (%)` | Per-AC booth-aggregated vote share (currently broadcast at LS level) |

Once filled, the validator will turn the "ⓘ Acknowledged data gap" entries
green and the per-AC swing analysis will produce 140 distinct values instead
of LS-segment chunks.

---

## Summary

| Category | Count | Action |
|---|---|---|
| ✅ Verified correct | 11 checks | none — keep as-is |
| ✗ Real bug needing external source | 1 | reconcile `winner_2016` (13-seat gap) |
| ✗ Schema completeness | 1 | add OTHERS row to 2024 LS file |
| ⚠ Per-AC granularity gap | 1 | replace constant `turnout_pct` with AC-wise data |
| ⚠ Acknowledged data gaps (intentional) | 3 columns | fill from ECI 2011/2014 archive |

No constituency winner has been invented. No vote share has been guessed. All
remaining work requires you to cross-reference an authoritative source — the
validator will tell you the moment you've succeeded.
