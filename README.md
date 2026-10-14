# MyTalent — Student Report Automation

Turn a tutor's raw assessment sheet into a color-coded progress report, an updated class-wide statistics ledger, and an AI tutor that answers follow-up questions — all from a single file upload.

Built for the MyTalent hackathon. One upload, three outputs, zero manual spreadsheet wrangling.

---

## The problem

Tutors at MyTalent mark each student's module assessment by hand, then spend time manually building progress reports, updating class trackers, and figuring out where each student is struggling. It's slow, repetitive, and the insights get lost in spreadsheets.

## The demo (what a judge sees in 60 seconds)

1. **Upload** a student's marked assessment — a single `.xlsx` file named `{student_id}_exhibit1.xlsx`.
2. **A heatmap report is generated instantly** — `{student_id}_exhibit2.xlsx`, where every module is color-coded by how the student performed:
    - **DONE** → Green
    - **C** → Yellow
    - **Anything else** → Red
3. **The class-wide ledger updates silently in the background** — the student's grades and state are appended/updated in `exhibit3.xlsx` in real time. The tutor just sees a confirmation that it's done.
4. **Ask the AI tutor anything** — a RAG chatbot is automatically grounded on that student's heatmap. The tutor asks follow-up questions ("where should this student focus next?") and gets a personalized plan back.

No configuration, no copy-paste, no leaving the page.

---

## How it works

The whole flow lives in a single Streamlit app (`src/hackathon/app.py`) and uses **only Streamlit and OpenAI** — no other frameworks.

### 1. Upload (Exhibit 1)

A file picker accepts **only `.xlsx`** files following the naming convention `{student_id}_exhibit1.xlsx`. This is the tutor's marked assessment and the single trigger for the entire workflow.

### 2. Heatmap report (Exhibit 2)

From the uploaded Exhibit 1, the app generates `{student_id}_exhibit2.xlsx` — a performance heatmap across the student's modules. Cells are colored by grade state (DONE → green, C → yellow, everything else → red) so a tutor can read a student's strengths and gaps at a glance.

### 3. Real-time class ledger (Exhibit 3)

`data/exhibit3.xlsx` holds every student's performance across each section, module, and test (A and B). On each upload, the matching student's row is appended or updated **in real time**.

> This step is intentionally invisible — the tutor is never prompted or shown the ledger. They only get a notification that `exhibit3.xlsx` has been updated.

### 4. RAG chatbot (Streamlit + OpenAI)

The freshly generated Exhibit 2 is automatically passed as context to a question-answering chatbot powered by OpenAI (`gpt-5-mini`). The tutor asks follow-up questions directly beneath the report and gets back a personalized improvement plan grounded in that student's actual data.

### Flow at a glance

```
Tutor marks assessment
        │
        ▼
Upload {student_id}_exhibit1.xlsx
        │
        ├──▶ Generate {student_id}_exhibit2.xlsx   (color-coded heatmap)
        │
        ├──▶ Update data/exhibit3.xlsx             (silent, real-time ledger)
        │
        └──▶ RAG chatbot grounded on exhibit2       (gpt-5-mini follow-ups)
```

---

## Tech stack

| Layer                  | Choice                                                |
| ---------------------- | ----------------------------------------------------- |
| UI                     | Streamlit                                             |
| LLM                    | OpenAI `gpt-5-mini`                                   |
| Reports / spreadsheets | Python + `openpyxl` (xlsx read/write + cell coloring) |
| Heatmap                | `matplotlib`                                          |

Deliberately minimal: Streamlit and OpenAI only, with a clean, emoji-free UI.

---

## Project structure

```
.
├── src/
│   └── hackathon/
│       └── app.py            # Streamlit app — entire workflow lives here
├── data/
│   └── exhibit3.xlsx         # Class-wide statistics ledger (updated in real time)
├── .env                      # OPENAI_API_KEY=...
├── requirements.txt
└── README.md
```

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your OpenAI key
echo "OPENAI_API_KEY=sk-..." > .env

# 3. Run the app
streamlit run src/hackathon/app.py
```

Then open the local URL Streamlit prints, upload a `{student_id}_exhibit1.xlsx` file, and watch the three outputs generate.

### Requirements

- Python 3.10+
- An OpenAI API key with access to `gpt-5-mini`
- `data/exhibit3.xlsx` present (the class ledger the app updates)

---

## Conventions

- **Input file name:** `{student_id}_exhibit1.xlsx`
- **Generated report:** `{student_id}_exhibit2.xlsx`
- **Ledger (never shown to the user):** `data/exhibit3.xlsx`
- **Color legend:** DONE = green · C = yellow · everything else = re# MyTalent — Student Report Automation

Turn a tutor's raw assessment sheet into a color-coded progress report, an updated class-wide statistics ledger, and an AI tutor that answers follow-up questions — all from a single file upload.

Built for the MyTalent hackathon. One upload, three outputs, zero manual spreadsheet wrangling.

---

## The problem

Tutors at MyTalent mark each student's module assessment by hand, then spend time manually building progress reports, updating class trackers, and figuring out where each student is struggling. It's slow, repetitive, and the insights get lost in spreadsheets.

## The demo (what a judge sees in 60 seconds)

1. **Upload** a student's marked assessment — a single `.xlsx` file named `{student_id}_exhibit1.xlsx`.
2. **A heatmap report is generated instantly** — `{student_id}_exhibit2.xlsx`, where every module is color-coded by how the student performed:
    - **DONE** → Green
    - **C** → Yellow
    - **Anything else** → Red
3. **The class-wide ledger updates silently in the background** — the student's grades and state are appended/updated in `exhibit3.xlsx` in real time. The tutor just sees a confirmation that it's done.
4. **Ask the AI tutor anything** — a RAG chatbot is automatically grounded on that student's heatmap. The tutor asks follow-up questions ("where should this student focus next?") and gets a personalized plan back.

No configuration, no copy-paste, no leaving the page.

---

## How it works

The whole flow lives in a single Streamlit app (`src/hackathon/app.py`) and uses **only Streamlit and OpenAI** — no other frameworks.

### 1. Upload (Exhibit 1)

A file picker accepts **only `.xlsx`** files following the naming convention `{student_id}_exhibit1.xlsx`. This is the tutor's marked assessment and the single trigger for the entire workflow.

### 2. Heatmap report (Exhibit 2)

From the uploaded Exhibit 1, the app generates `{student_id}_exhibit2.xlsx` — a performance heatmap across the student's modules. Cells are colored by grade state (DONE → green, C → yellow, everything else → red) so a tutor can read a student's strengths and gaps at a glance.

### 3. Real-time class ledger (Exhibit 3)

`data/exhibit3.xlsx` holds every student's performance across each section, module, and test (A and B). On each upload, the matching student's row is appended or updated **in real time**.

> This step is intentionally invisible — the tutor is never prompted or shown the ledger. They only get a notification that `exhibit3.xlsx` has been updated.

### 4. RAG chatbot (Streamlit + OpenAI)

The freshly generated Exhibit 2 is automatically passed as context to a question-answering chatbot powered by OpenAI (`gpt-5-mini`). The tutor asks follow-up questions directly beneath the report and gets back a personalized improvement plan grounded in that student's actual data.

### Flow at a glance

```
Tutor marks assessment
        │
        ▼
Upload {student_id}_exhibit1.xlsx
        │
        ├──▶ Generate {student_id}_exhibit2.xlsx   (color-coded heatmap)
        │
        ├──▶ Update data/exhibit3.xlsx             (silent, real-time ledger)
        │
        └──▶ RAG chatbot grounded on exhibit2       (gpt-5-mini follow-ups)
```

---

## Tech stack

| Layer                  | Choice                                                |
| ---------------------- | ----------------------------------------------------- |
| UI                     | Streamlit                                             |
| LLM                    | OpenAI `gpt-5-mini`                                   |
| Reports / spreadsheets | Python + `openpyxl` (xlsx read/write + cell coloring) |
| Heatmap                | `matplotlib`                                          |

Deliberately minimal: Streamlit and OpenAI only, with a clean, emoji-free UI.

---

## Project structure

```
.
├── src/
│   └── hackathon/
│       └── app.py            # Streamlit app — entire workflow lives here
├── data/
│   └── exhibit3.xlsx         # Class-wide statistics ledger (updated in real time)
├── .env                      # OPENAI_API_KEY=...
├── requirements.txt
└── README.md
```

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your OpenAI key
echo "OPENAI_API_KEY=sk-..." > .env

# 3. Run the app
streamlit run src/hackathon/app.py
```

Then open the local URL Streamlit prints, upload a `{student_id}_exhibit1.xlsx` file, and watch the three outputs generate.

### Requirements

- Python 3.10+
- An OpenAI API key with access to `gpt-5-mini`
- `data/exhibit3.xlsx` present (the class ledger the app updates)

---

## Conventions

- **Input file name:** `{student_id}_exhibit1.xlsx`
- **Generated report:** `{student_id}_exhibit2.xlsx`
- **Ledger (never shown to the user):** `data/exhibit3.xlsx`
- **Color legend:** DONE = green · C = yellow · everything else = red
