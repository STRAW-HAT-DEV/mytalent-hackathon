"""
Synthetic Exhibit 1 data for the "Mark -> Diagnose -> Decide" prototype.

Key format: {student_id}.{module_number}.{test_character}.{question_identifier}
  e.g. 3.2.A.d = student 3, module 2, test A, question d

5 students (1-5) x 3 modules (1-3) x 2 tests (A, B) x 10 questions (a-j) = 300 cells.

Outputs (all CSV, import straight into Google Sheets / Excel):
  syllabus_map.csv        module.question -> syllabus point, topic, skill
  marks_raw.csv           what the tutor actually typed (messy, shuffled) -> the pipeline's INPUT
  marks_expected.csv      what cleaning should produce + the true outcome (test oracle)
  timing_log.csv          student-entered exam timing log (messy)
  expected_tests.csv      expected Exhibit 3 results per test (score, band)
  expected_heatmap.csv    expected Exhibit 2 status per student x syllabus point
  expected_summary.csv    expected Exhibit 2 summary percentages per student
  expected_diagnosis.csv  expected diagnosis per student with evidence

Run: python generate.py
"""
import csv
import random
import re
from pathlib import Path

OUT = Path(__file__).parent
STUDENTS = [1, 2, 3, 4, 5]
MODULES = [1, 2, 3]
TESTS = ["A", "B"]
QUESTIONS = list("abcdefghij")
TIME_LIMIT_MIN = 50

# ---------------------------------------------------------------------------
# 1. Syllabus map: each module's 10 questions test 10 syllabus points.
#    Tests A and B of a module are parallel forms (same points).
#    "chain_rule" is a skill shared across modules -> cross-module gap detection.
# ---------------------------------------------------------------------------
TOPICS = {
    1: ["Domain and range", "Linear functions", "Quadratics", "Polynomials",
        "Composite functions", "Inverse functions", "Transformations",
        "Exponential functions", "Logarithms", "Circular functions"],
    2: ["Limits and first principles", "Power rule", "Product rule", "Chain rule",
        "Quotient rule", "Derivatives of exp and log", "Tangents and normals",
        "Stationary points", "Optimisation", "Rates of change"],
    3: ["Antiderivatives", "Integrating powers", "Definite integrals",
        "Integrating exponentials", "Integrating circular functions",
        "Reverse chain rule", "Area under a curve", "Area between curves",
        "Fundamental theorem", "Average value"],
}
SHARED_SKILL = {(1, "e"): "chain_rule", (2, "d"): "chain_rule", (3, "f"): "chain_rule"}


def syllabus_point(m, q):
    return f"{m}.{QUESTIONS.index(q) + 1}"


def skill(m, q):
    return SHARED_SKILL.get((m, q), f"sp_{syllabus_point(m, q)}")


# ---------------------------------------------------------------------------
# 2. True outcomes (what the tutor meant). D=DONE W=wrong C=careless B=BLANK
#    N = whole test not submitted. One string per test, questions a..j.
# ---------------------------------------------------------------------------
GRID = {
    # Student 1 - strong / on track. Perfect scores, one C->DONE and one W->DONE recovery.
    1: {"1A": "DDDDDDDDDD", "1B": "DDDDDDDDDD",
        "2A": "DDDDDDDDCD", "2B": "DDDDDDDDDD",
        "3A": "DDDDDDDWDD", "3B": "DDDDDDDDDD"},
    # Student 2 - careless. C scattered on points that are DONE in the other attempt.
    2: {"1A": "DDCDDDCDDD", "1B": "DCDDDDDDCD",
        "2A": "DDDCDDDDDC", "2B": "CDDDDDCDDD",
        "3A": "DDDDCDDCDD", "3B": "DDCDDDDDDD"},
    # Student 3 - knowledge gap. Always W on chain rule (1.e, 2.d, 3.f). Scores look fine (80-90%).
    3: {"1A": "DDDDWDDDDD", "1B": "DDDDWDDDDD",
        "2A": "DDDWDDDDDD", "2B": "DDDWDDDDDD",
        "3A": "DDDDDWDDDD", "3B": "DDDDDWDDCD"},
    # Student 4 - time allocation. Trailing blanks, hits time limit; content is known (DONE elsewhere).
    #   1B has a one-off W at g (regression, should NOT trigger a gap). 2A is exactly 40% (band boundary).
    4: {"1A": "DDDDDDDBBB", "1B": "DDDDDDWDDB",
        "2A": "DDDDBBBBBB", "2B": "DDDDDDDDBB",
        "3A": "DDDDDDDBBB", "3B": "DDDDDDDDDD"},
    # Student 5 - new student. One test only, 0% (W/C/BLANK, C scores zero). Everything else not submitted.
    5: {"1A": "WWBWWBWWBC", "1B": "NNNNNNNNNN",
        "2A": "NNNNNNNNNN", "2B": "NNNNNNNNNN",
        "3A": "NNNNNNNNNN", "3B": "NNNNNNNNNN"},
}
CODE = {"D": "DONE", "W": "W", "C": "C", "B": "BLANK", "N": "NOT_SUBMITTED"}
# How a clean tutor writes each value (Exhibit 1 style)
TYPED = {"DONE": "DONE", "W": "W", "C": "C", "BLANK": "\\Blank\\"}


def key(s, m, t, q):
    return f"{s}.{m}.{t}.{q}"


true_outcome = {}
for s in STUDENTS:
    for m in MODULES:
        for t in TESTS:
            row = GRID[s][f"{m}{t}"]
            for q, ch in zip(QUESTIONS, row):
                true_outcome[key(s, m, t, q)] = CODE[ch]

# ---------------------------------------------------------------------------
# 3. Messy raw entries. Each edge case: raw value typed, what cleaning should
#    output, the flag it should raise, and a note. None raw = row is absent.
# ---------------------------------------------------------------------------
EDGE = {
    # --- harmless formatting: cleaning normalises silently
    "1.1.A.a": ("DONE ", None, "trailing space"),
    "1.2.B.c": ("done", None, "lowercase"),
    "2.2.A.d": (" C", None, "leading space"),
    "3.1.A.e": ("w", None, "lowercase W"),
    "4.1.A.h": ("Blank", None, "Blank without backslashes"),
    "4.1.A.i": ("\\blank\\", None, "lowercase \\blank\\"),
    "4.3.A.j": ("BLANK", None, "uppercase BLANK"),
    # --- non-standard wording: rules can't map it, AI suggests, tutor confirms
    "3.2.A.d": ("Wrong", "NON_STANDARD", "word instead of code -> suggest W"),
    "3.3.A.f": ("错", "NON_STANDARD", "Chinese for 'wrong' -> suggest W"),
    "5.1.A.j": ("C 粗心", "NON_STANDARD", "code plus Chinese note 'careless' -> suggest C"),
    # --- genuinely ambiguous: never guess, tutor must resolve
    "4.2.A.e": ("", "UNMARKED", "empty cell inside a submitted test: forgot to mark, or left blank?"),
    "5.1.A.c": ("?", "INVALID_VALUE", "unknown value"),
    "4.3.B.j": (None, "MISSING_ROW", "row missing from a submitted test"),
}
DUPLICATES = [  # same key entered twice
    ("2.1.A.c", "DONE", "CONFLICT", "duplicate key with a different value (first entry was 'C')"),
    ("1.2.A.b", "DONE", "DUPLICATE_SAME", "duplicate key, same value -> keep one"),
]
INVALID_KEYS = [  # rows that must be rejected
    ("6.1.A.a", "DONE", "unknown student 6"),
    ("1.4.A.a", "DONE", "module 4 does not exist"),
    ("1.1.C.a", "DONE", "test C does not exist"),
    ("1.1.A.k", "DONE", "question k out of range a-j"),
    ("1-1-A-a", "DONE", "malformed key (dashes)"),
    ("2.1.a.b", "W", "lowercase test character - reject, don't guess"),
]
# Student 5: 1B..3A rows present but every cell empty; 3B rows absent entirely.
NOT_SUBMITTED_ABSENT = {(5, 3, "B")}

raw_rows, expected_rows = [], []
for s in STUDENTS:
    for m in MODULES:
        for t in TESTS:
            for q in QUESTIONS:
                k = key(s, m, t, q)
                truth = true_outcome[k]
                if truth == "NOT_SUBMITTED":
                    if (s, m, t) not in NOT_SUBMITTED_ABSENT:
                        raw_rows.append({"key": k, "outcome": ""})
                    expected_rows.append(dict(key=k, cleaned_outcome="NOT_SUBMITTED", flag="",
                                              true_outcome=truth,
                                              note="whole test empty/absent -> not submitted"))
                    continue
                if k in EDGE:
                    raw, flag, note = EDGE[k]
                    if raw is not None:
                        raw_rows.append({"key": k, "outcome": raw})
                    cleaned = truth if flag is None else ""
                    expected_rows.append(dict(key=k, cleaned_outcome=cleaned, flag=flag or "",
                                              true_outcome=truth, note=note))
                else:
                    raw_rows.append({"key": k, "outcome": TYPED[truth]})
                    expected_rows.append(dict(key=k, cleaned_outcome=truth, flag="",
                                              true_outcome=truth, note=""))

# first entry of the conflicting duplicate uses the true value typed lowercase
for r in raw_rows:
    if r["key"] == "2.1.A.c":
        r["outcome"] = "c"
for r in expected_rows:
    if r["key"] == "2.1.A.c":
        r.update(cleaned_outcome="", flag="CONFLICT",
                 note="entered twice: 'c' and 'DONE' -> tutor picks")
    if r["key"] == "1.2.A.b":
        r.update(flag="DUPLICATE_SAME", note="entered twice with the same value -> keep one")

for k, v, _flag, _note in DUPLICATES:
    raw_rows.append({"key": k, "outcome": v})
for k, v, note in INVALID_KEYS:
    raw_rows.append({"key": k, "outcome": v})
    expected_rows.append(dict(key=k, cleaned_outcome="", flag="INVALID_KEY",
                              true_outcome="", note=note))

random.seed(42)
random.shuffle(raw_rows)  # pipeline must not rely on row order

# ---------------------------------------------------------------------------
# 4. Timing log (student-entered). Second attempt = keep working after the
#    time limit, so it is empty when the student finished inside the limit.
# ---------------------------------------------------------------------------
TEST_DATES = {("1", "A"): "2026-07-06", ("1", "B"): "2026-07-13",
              ("2", "A"): "2026-08-03", ("2", "B"): "2026-08-10",
              ("3", "A"): "2026-09-07", ("3", "B"): "2026-09-14"}
PROFILE = {  # minutes to end of first attempt, minutes to end of second attempt, checks
    1: (44, None, 2),
    2: (31, None, 0),  # finishes early, never checks -> careless signal
    3: (46, None, 1),
    4: (50, 18, 0),    # hits the limit every time, keeps going afterwards
}


def score_pct(s, m, t):
    outs = [true_outcome[key(s, m, t, q)] for q in QUESTIONS]
    return round(100 * sum(o == "DONE" for o in outs) / len(outs))


def hhmm(start_min):
    return f"{16 + start_min // 60}:{start_min % 60:02d}"


timing_rows, timing_flags = [], {}
for s in STUDENTS:
    for m in MODULES:
        for t in TESTS:
            if true_outcome[key(s, m, t, "a")] == "NOT_SUBMITTED":
                continue
            tk = f"{s}.{m}.{t}"
            if tk == "5.1.A":
                timing_flags[tk] = "MISSING_TIMING"  # student forgot to log
                continue
            first, second, checks = PROFILE[s]
            if (s, m, t) == (4, 3, "B"):  # student 4 improves on the last test
                first, second, checks = 47, None, 1
            row = dict(test_key=tk, date=TEST_DATES[(str(m), t)], start="16:00",
                       end_first_attempt=hhmm(first),
                       end_second_attempt=hhmm(first + second) if second else "",
                       checks=str(checks), final_score=str(score_pct(s, m, t)),
                       time_limit_min=str(TIME_LIMIT_MIN))
            if tk == "2.2.B":
                row["end_first_attempt"] = "15:35"
                timing_flags[tk] = "END_BEFORE_START"
            if tk == "1.3.B":
                row["checks"] = ""
                timing_flags[tk] = "MISSING_CHECKS"
            if tk == "3.1.A":
                row["final_score"] = "100"
                timing_flags[tk] = "SCORE_MISMATCH (logged 100, marks say 90)"
            timing_rows.append(row)

# ---------------------------------------------------------------------------
# 5. Expected Exhibit 3: score per test. Score = DONE / 10 (C and BLANK score 0).
#    Bands (assumption): Low <40, Mid 40-<75, High >=75. 75% is impossible with 10 Qs.
# ---------------------------------------------------------------------------
def band(p):
    return "High (75-100)" if p >= 75 else "Mid (40-75)" if p >= 40 else "Low (0-40)"


test_rows = []
for s in STUDENTS:
    for m in MODULES:
        for t in TESTS:
            outs = [true_outcome[key(s, m, t, q)] for q in QUESTIONS]
            if outs[0] == "NOT_SUBMITTED":
                test_rows.append(dict(test_key=f"{s}.{m}.{t}", student_id=s, module=m, test=t,
                                      done="", w="", c="", blank="", score_pct="",
                                      band="Not submitted"))
                continue
            p = score_pct(s, m, t)
            test_rows.append(dict(test_key=f"{s}.{m}.{t}", student_id=s, module=m, test=t,
                                  done=outs.count("DONE"), w=outs.count("W"), c=outs.count("C"),
                                  blank=outs.count("BLANK"), score_pct=p, band=band(p)))

# ---------------------------------------------------------------------------
# 6. Expected Exhibit 2: latest submitted attempt per syllabus point wins.
#    DONE -> mastered, C -> partial, W/BLANK -> not understood, none -> not covered.
# ---------------------------------------------------------------------------
STATUS = {"DONE": "MASTERED", "C": "PARTIAL", "W": "NOT_UNDERSTOOD", "BLANK": "NOT_UNDERSTOOD"}
heat_rows, summary_rows = [], []
for s in STUDENTS:
    statuses = []
    for m in MODULES:
        for q in QUESTIONS:
            latest = None
            for t in TESTS:  # B is later than A
                o = true_outcome[key(s, m, t, q)]
                if o != "NOT_SUBMITTED":
                    latest = (t, o)
            st = STATUS[latest[1]] if latest else "NOT_COVERED"
            statuses.append(st)
            heat_rows.append(dict(student_id=s, syllabus_point=syllabus_point(m, q),
                                  latest_test=f"{m}.{latest[0]}" if latest else "",
                                  latest_outcome=latest[1] if latest else "", status=st))
    total = len(statuses)
    covered = sum(x != "NOT_COVERED" for x in statuses)
    understood = sum(x in ("MASTERED", "PARTIAL") for x in statuses)
    mastered = statuses.count("MASTERED")
    summary_rows.append(dict(
        student_id=s, total_points=total, covered=covered,
        covered_pct=round(100 * covered / total, 2),
        understood=understood, understood_pct=round(100 * understood / total, 2),
        mastered=mastered, mastered_of_all_pct=round(100 * mastered / total, 2),
        mastered_of_covered_pct=round(100 * mastered / covered, 2) if covered else ""))

# ---------------------------------------------------------------------------
# 7. Expected diagnosis (rules, applied to true outcomes + clean timing).
# ---------------------------------------------------------------------------
diag_rows = []
for s in STUDENTS:
    submitted = [(m, t) for m in MODULES for t in TESTS
                 if true_outcome[key(s, m, t, "a")] != "NOT_SUBMITTED"]
    if len(submitted) < 2:
        diag_rows.append(dict(student_id=s, diagnosis="INSUFFICIENT_EVIDENCE",
                              evidence=f"only {len(submitted)} submitted test",
                              suggested_next_step="Probe in session; no label yet"))
        continue
    # knowledge gap: same skill W in >=2 different tests
    w_by_skill = {}
    for m, t in submitted:
        for q in QUESTIONS:
            if true_outcome[key(s, m, t, q)] == "W":
                w_by_skill.setdefault(skill(m, q), []).append(key(s, m, t, q))
    gaps = {k: v for k, v in w_by_skill.items() if len(v) >= 2}
    # careless: C on points that are DONE in the other attempt of the same module
    careless = [key(s, m, t, q) for m, t in submitted for q in QUESTIONS
                if true_outcome[key(s, m, t, q)] == "C"
                and true_outcome[key(s, m, "B" if t == "A" else "A", q)] == "DONE"]
    # time: tests with >=2 trailing blanks
    trailing = []
    for m, t in submitted:
        outs = [true_outcome[key(s, m, t, q)] for q in QUESTIONS]
        n = 0
        for o in reversed(outs):
            if o == "BLANK":
                n += 1
            else:
                break
        if n >= 2:
            trailing.append(f"{s}.{m}.{t} ({n} trailing blanks)")
    if gaps:
        sk, keys = max(gaps.items(), key=lambda kv: len(kv[1]))
        diag_rows.append(dict(student_id=s, diagnosis="KNOWLEDGE_GAP",
                              evidence=f"{sk}: W in " + ", ".join(keys),
                              suggested_next_step="Re-teach chain rule; redo Demo; Retest"))
    elif len(trailing) >= 2:
        diag_rows.append(dict(student_id=s, diagnosis="TIME_ALLOCATION",
                              evidence="; ".join(trailing) + "; timing log hits 50-min limit, 0 checks",
                              suggested_next_step="Timed section practice at 5 min/question"))
    elif len(careless) >= 3:
        diag_rows.append(dict(student_id=s, diagnosis="CARELESS",
                              evidence=f"{len(careless)} C on points DONE elsewhere: " + ", ".join(careless)
                              + "; finishes in ~31 min with 0 checks",
                              suggested_next_step="2-minute check routine; Retest in 3 days"))
    else:
        diag_rows.append(dict(student_id=s, diagnosis="ON_TRACK",
                              evidence="isolated errors only, each recovered on the next attempt",
                              suggested_next_step="Move on to next Module / VCAA mock"))

# ---------------------------------------------------------------------------
# write files
# ---------------------------------------------------------------------------
def write(name, rows, fields):
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


write("syllabus_map.csv",
      [dict(module=m, question=q, syllabus_point=syllabus_point(m, q),
            topic=TOPICS[m][QUESTIONS.index(q)], skill=skill(m, q))
       for m in MODULES for q in QUESTIONS],
      ["module", "question", "syllabus_point", "topic", "skill"])
write("marks_raw.csv", raw_rows, ["key", "outcome"])
write("marks_expected.csv", expected_rows,
      ["key", "cleaned_outcome", "flag", "true_outcome", "note"])
for r in timing_rows:
    r["expected_flag"] = timing_flags.get(r["test_key"], "")
# 5.1.A has no timing row at all (student forgot to log) -> expect MISSING_TIMING
write("timing_log.csv", timing_rows,
      ["test_key", "date", "start", "end_first_attempt", "end_second_attempt",
       "checks", "final_score", "time_limit_min", "expected_flag"])
write("expected_tests.csv", test_rows,
      ["test_key", "student_id", "module", "test", "done", "w", "c", "blank", "score_pct", "band"])
write("expected_heatmap.csv", heat_rows,
      ["student_id", "syllabus_point", "latest_test", "latest_outcome", "status"])
write("expected_summary.csv", summary_rows, list(summary_rows[0].keys()))
write("expected_diagnosis.csv", diag_rows,
      ["student_id", "diagnosis", "evidence", "suggested_next_step"])

# sanity checks
KEY_RE = re.compile(r"^[1-5]\.[1-3]\.[AB]\.[a-j]$")
assert len(true_outcome) == 300
assert all(KEY_RE.match(k) for k in true_outcome)
print(f"raw rows: {len(raw_rows)} | expected rows: {len(expected_rows)} | "
      f"timing rows: {len(timing_rows)}")
for d in diag_rows:
    print(d["student_id"], d["diagnosis"])
