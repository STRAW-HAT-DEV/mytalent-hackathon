# Synthetic Exhibit 1 data

Key format: `{student_id}.{module_number}.{test_character}.{question_identifier}`, for example `3.2.A.d`.

The grid is 5 students (1–5) × 3 modules (1–3) × 2 tests (A, B) × 10 questions (a–j), which makes 300 cells. Regenerate everything with `python generate.py`.

## Files

| File | Role |
|---|---|
| `marks_raw.csv` | **Pipeline input.** What the tutor typed: messy, shuffled, with duplicates and bad keys. |
| `syllabus_map.csv` | Module + question → syllabus point, topic, skill. |
| `timing_log.csv` | Student-entered exam log. The `expected_flag` column is the answer key; drop it before ingesting. |
| `marks_expected.csv` | Answer key for cleaning: `cleaned_outcome` (what code should output), `flag`, and `true_outcome` (what the tutor meant). |
| `expected_tests.csv` | Answer key for Exhibit 3: score and band per test. |
| `expected_heatmap.csv` | Answer key for Exhibit 2: status per student × syllabus point. |
| `expected_summary.csv` | Answer key for the Exhibit 2 summary percentages. |
| `expected_diagnosis.csv` | Answer key for the diagnosis, with evidence. |

## Students

| ID | Pattern | What should happen |
|---|---|---|
| 1 | Strong. Perfect tests, one C→DONE and one W→DONE recovery | `ON_TRACK`; single slips don't trigger a label |
| 2 | Careless. 11 C on points that are DONE in the other attempt; finishes in 31 min with 0 checks | `CARELESS` |
| 3 | Knowledge gap. Always W on chain rule (1.e, 2.d, 3.f) across all 3 modules, yet every score is 80–90% | `KNOWLEDGE_GAP`. The good scores hide the gap |
| 4 | Time. Trailing blanks, hits the 50-min limit, 0 checks; the same questions are DONE on other attempts | `TIME_ALLOCATION` |
| 5 | New. One test only (0%), everything else not submitted | `INSUFFICIENT_EVIDENCE`, no label |

## Edge cases

**Cleaning: silently fix.**
- `DONE ` with a trailing space
- `done`, `w`, and ` C` (lowercase or leading space)
- `Blank`, `\blank\`, `BLANK` alongside the standard `\Blank\`

**Cleaning: suggest a value, tutor confirms (`NON_STANDARD`).**
- `Wrong`
- `错` (Chinese for "wrong")
- `C 粗心` (C plus a "careless" note)

**Cleaning: never guess, tutor resolves.**
- `UNMARKED`: an empty cell inside a submitted test (4.2.A.e)
- `INVALID_VALUE`: `?` (5.1.A.c)
- `MISSING_ROW`: 4.3.B.j is absent
- `CONFLICT`: 2.1.A.c is entered as both `c` and `DONE`
- `DUPLICATE_SAME`: 1.2.A.b is entered twice with the same value; keep one

**Cleaning: reject (`INVALID_KEY`).**
- `6.1.A.a`: unknown student
- `1.4.A.a`: module 4
- `1.1.C.a`: test C
- `1.1.A.k`: question k
- `1-1-A-a`: malformed key
- `2.1.a.b`: lowercase test letter

**Not submitted, in two forms.**
- 5.1.B to 5.3.A: the rows exist but every cell is empty.
- 5.3.B: the rows are absent entirely.

Rule: if the whole test is empty, it's `NOT_SUBMITTED`. If only some cells are empty, they're `UNMARKED`.

**Row order.** `marks_raw.csv` is shuffled, so the pipeline mustn't rely on row order.

**Scoring and Exhibit 3.**
- 100% (student 1)
- 0% from W/C/BLANK with no DONE (student 5)
- Exactly 40%, the band boundary (4.2.A)

**Heat-map and Exhibit 2.**
- W → DONE (1.3)
- C → DONE (1.2)
- DONE → W regression (4.1.B.g); this is a single W and must not trigger a gap
- DONE → C (3.3.B.i)
- `NOT_COVERED` for modules 2–3 (student 5)

**Timing log.**
- `MISSING_TIMING`: 5.1.A has no row
- `END_BEFORE_START`: 2.2.B
- `MISSING_CHECKS`: 1.3.B
- `SCORE_MISMATCH`: 3.1.A, where the student logged 100 but the marks say 90

## Assumptions (state them in the pitch)

- Score = DONE ÷ 10. C and BLANK score 0.
- Bands: Low <40, Mid 40 to <75, High ≥75. With 10 questions a score of 75% is impossible.
- Heat-map: the latest submitted attempt wins. DONE → mastered, C → partial, W/BLANK → not understood, never tested → not covered.
- A and B are parallel forms of the same Module test, so they test the same syllabus points. B is the later attempt.
- Second attempt means continuing to work after the 50-minute limit, so the field is empty if the student finished in time.

**Pitch insight:** student 4's heat-map shows i and j as "not understood", but they're a time problem, not a knowledge gap. The diagnosis catches what the heat-map gets wrong.
