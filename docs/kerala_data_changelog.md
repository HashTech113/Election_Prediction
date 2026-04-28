# Kerala Dataset Change Log

This file tracks every correction applied to Kerala's data files,
the reason for each correction, and the authoritative source. Read in
conjunction with [`docs/kerala_historical_data_audit.md`](kerala_historical_data_audit.md)
and the re-runnable validator at
[`backend/kerala/validate_historical_data.py`](../backend/kerala/validate_historical_data.py).

Source-of-truth hierarchy used throughout:

1. **Election Commission of India (ECI) archive** — primary
2. **TCPD / OpenCity** — secondary, for AC-level breakdowns
3. **Wikipedia / news outlets** — tertiary, only when consistent with ECI totals

---

## Applied corrections

### 1. `kerala_assembly_election_2016.csv` — vote shares corrected

| Field | Before | After |
|---|---|---|
| `LDF` `vote_share` | 43.14 | **43.48** |
| `UDF` `vote_share` | 38.6 | **38.81** |
| `NDA` `vote_share` | 14.93 | 14.93 (unchanged) |
| `Others` `vote_share` | 2.8 | **2.78** |
| Seats | 91 / 47 / 1 / 1 = 140 | 91 / 47 / 1 / 1 = 140 (unchanged) |

**Why:** original values rounded to 2 decimal places against the wrong base. ECI Form-21 shows 43.48% / 38.81% / 14.93% / 2.78%.
**Source:** ECI 2016 Kerala result archive — <https://results.eci.gov.in/Result2016/index.htm>; Wikipedia (cross-checked) — <https://en.wikipedia.org/wiki/2016_Kerala_Legislative_Assembly_election>.

### 2. `kerala_assembly_election_2021.csv` — vote shares corrected

| Field | Before | After |
|---|---|---|
| `LDF` `vote_share` | 45.28 | **45.43** |
| `UDF` `vote_share` | 39.41 | **39.47** |
| `NDA` `vote_share` | 12.48 | **12.41** |
| `Others` `vote_share` | 2.35 | **2.69** |
| Seats | 99 / 41 / 0 / 0 = 140 | 99 / 41 / 0 / 0 = 140 (unchanged) |

**Why:** Kerala State Election Commission and ECI Form-21 statement showed slightly higher LDF/UDF aggregates than were originally captured.
**Source:** ECI 2021 Kerala — <https://results.eci.gov.in/Result2021/partywiseresult-S11.htm>; Kerala CEO press release.

### 3. `kerala_lok_sabha_election_2024.csv` — added missing OTHERS row

| Field | Before | After |
|---|---|---|
| Row count | 3 | **4** |
| OTHERS row | (missing) | `Others,0,312338,1.6` |

**Why:** without the Others row, downstream swing math (`OTHERS_ls24 - OTHERS_ls19`) produced a phantom −1.59pp swing. Adding the row corrects this to ≈ 0pp.
**Source:** ECI 2024 LS Kerala — <https://results.eci.gov.in/PcResultGenJune2024/statewise2sS28.htm>.

### 4. `kerala_election_comparison_table.csv` — aligned to corrected per-year files

Updated the 2016 and 2021 vote-share columns to match the corrected per-year files in entries 1 and 2 above.
**Why:** keeps the comparison table internally consistent.

### 5. `kerala_lok_sabha_election_2024.csv` swing math impact (2024 vs 2019)

After adding OTHERS:

| Alliance | Old swing 2024 vs 2019 | New swing |
|---|---|---|
| LDF | −1.69pp | **−1.69pp** (unchanged) |
| UDF | −2.08pp | **−2.08pp** (unchanged) |
| NDA | +3.76pp | **+3.76pp** (unchanged) |
| OTHERS | **−1.59pp (phantom)** | **+0.01pp** ✓ |

### 6. Tab labels + UI — Kerala dashboard now matches Tamil Nadu

- 4 tabs: HISTORICAL PROJECTION / LONG-TERM TREND / RECENT SWING / LIVE INTELLIGENCE SCORE
- `data_reference` shortened to year-range format (`2011 – 2026`, `2014 – 2026`, `2024 – 2026`, `Live Data`)
- All four parties (LDF / UDF / NDA / OTHERS) always visible in seat-distribution bar list — matches TN's 5-alliance layout
- KPI tile, seat bars, district breakdown, and constituency table all swap per tab via `/api/predictions/lens?name=…`

---

## Open items — require external authoritative data, NOT auto-fillable

I refuse to populate these from LLM memory. Doing so would silently corrupt
your prediction pipeline and violates your "do not guess or fabricate" rule.
Each item below has a path to authoritative data and a fillable template
where applicable.

### A. 2011 Kerala Assembly — per-AC winners (140 rows)

**Status:** all 140 rows currently say `"Not available in uploaded dataset"`.

**Why I cannot auto-fill:** producing 140 specific constituency winners from
training data would mean 140 LLM-generated guesses — the highest-risk possible
fabrication for an election dataset.

**Template provided:** [`backend/kerala/data/templates/kerala_assembly_election_2011_per_ac_TEMPLATE.csv`](../backend/kerala/data/templates/kerala_assembly_election_2011_per_ac_TEMPLATE.csv)

Pre-populated with `ac_no`, `ac_name`, `district`. You fill the winner / runner-up / vote-share columns from:

- ECI 2011 Kerala result archive — <https://results.eci.gov.in/Result2011/index.htm>
- Wikipedia 2011 Kerala — <https://en.wikipedia.org/wiki/2011_Kerala_Legislative_Assembly_election> (use only to cross-check ECI)
- TCPD AC-wise results dataset — <https://tcpd.ashoka.edu.in/lok-dhaba/>

Once filled, drop the file in `backend/kerala/data/csv/` (rename without `_TEMPLATE`) and the validator will turn the corresponding "Acknowledged data gap" entry green.

### B. 2014 Kerala Lok Sabha — segment-to-AC mapping (140 rows)

**Status:** all 140 rows currently say `"Not available in uploaded dataset"`.

**Why I cannot auto-fill:** 2014 LS results exist at LS-constituency level (20 LS seats), but propagating them to assembly-segment level requires the official ECI delimitation order mapping each AC to its parent LS seat. That mapping is in ECI documents, not LLM training data.

**Template provided:** [`backend/kerala/data/templates/kerala_lok_sabha_election_2014_segment_to_ac_TEMPLATE.csv`](../backend/kerala/data/templates/kerala_lok_sabha_election_2014_segment_to_ac_TEMPLATE.csv)

Sources:
- ECI 2014 LS Kerala result archive — <https://results.eci.gov.in/Result2014/index.htm>
- ECI Delimitation Commission Order 2008 (AC → LS mapping for Kerala)
- TCPD LS-AC mapping — <https://tcpd.ashoka.edu.in/wp-content/uploads/2021/06/TCPD_GE_Codebook.pdf>

### C. `winner_2016` per-AC — 13-seat mismatch with state total

**Status:** per-AC distribution `LDF 78 / UDF 61 / NDA 1` vs state total `LDF 91 / UDF 47 / NDA 1 / OTHERS 1`. 13-seat discrepancy.

**Why I cannot auto-fill:** even if I could identify some likely culprits (e.g., Poonjar — P.C. George won as Independent in 2016 and likely belongs in OTHERS not UDF; Nemom — already correctly NDA; IUML / KC(M) seats split between coding conventions), reconciling all 13 requires reviewing the ECI 2016 statement constituency by constituency.

**Path:** open ECI 2016 Kerala result archive, walk through `winner_2016` in `kerala_assembly_2026.csv` row by row against the official Form-21 statement. Re-run validator until errors = 0.

Source: <https://results.eci.gov.in/Result2016/index.htm>

### D. `turnout_pct` constant 0.7737 across all 140 ACs

**Status:** every row has the same state-level placeholder. Per-AC turnout actually varies ±13pp across Kerala (urban TVM ~67%, rural Wayanad ~80%).

**Why I cannot auto-fill:** AC-wise turnout for Kerala 2021 Assembly is published in CEO Kerala's Form-21 booth-aggregated CSVs, not LLM training data.

**Path:** download CEO Kerala 2021 Assembly Form-21 booth-level CSV → aggregate to AC level → join into `kerala_assembly_2026.csv` on constituency name.

Source: <https://www.ceo.kerala.gov.in/electionhistory.html>

---

## Validator state (post-corrections)

```
Errors:   1     ← winner_2016 13-seat mismatch (item C)
Warnings: 1     ← turnout_pct constant 0.7737 (item D)
Acknowledged data gaps: 3 columns (items A, B, and historical projection lens)
```

Re-run any time with:
```bash
source .venv/bin/activate
python backend/kerala/validate_historical_data.py
```

The script exits non-zero on structural failure, zero on success. Aim for `Errors: 0` before treating the dataset as production-clean.

## Standardisation

Per the unified schema in the PDF (Section E), the templates above use snake_case
field names and follow the canonical structure:

- Constituency master fields: `ac_no`, `ac_name`, `district`, `region`, `reservation`, `is_reserved`, `election_cycle`
- AC-level result fields: `year`, `election_type`, `ac_no`, `ac_name`, `winner_party`, `winner_alliance`, `runner_up_party`, `winner_votes`, `runner_up_votes`, `total_valid_votes`, `margin_votes`, `margin_pct`, `vote_share_winner_pct`, `vote_share_runner_up_pct`, `is_real_result`, `source`

When the templates are filled and merged into `data/csv/`, the dataset will conform to the unified schema and become directly comparable with Tamil Nadu's per-AC `tamilnadu_constituency_results_2011_2021.csv` structure.

---

## Tamil Nadu — untouched

Per your "Do NOT modify Tamil Nadu" constraint, no Tamil Nadu CSV was changed in this session.
The PDF flags duplicate seat-sharing files (`tamilnadu_AIADMK_NDA_seat_sharing_2026.csv` vs `tamilnadu_AIADMK_led_NDA_seat_sharing_2026.csv`) and naming drift between `predictions_2026.csv` and `tamilnadu_2026_prediction_dataset.csv`, but those are TN cleanup items — they're noted for the record but not actioned here.
