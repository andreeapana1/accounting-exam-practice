# Exam Practice · Data Analytics in Accounting

A practice website for the oral exam in *Data Analytics in Accounting*. Students practise:

- **Data manipulation exams**: one Excel file plus one SQL database, five questions in eight minutes.
- **A question bank**: every Excel and SQL question, filterable by tool, dataset and skill.
- **Data interpretation exams**: regression output with four questions (predict, interpret, significance, reliability) in five minutes.

- **Examiner mode** 🎙: the browser reads each question aloud, the student answers out loud against a countdown,
  and the "examiner" interrupts once per question with a follow-up **chosen from what the student has said so far**:
  it quotes a wrong number back (*"You said 120 — can you check that?"*), asks for a missing unit or key point,
  catches classic misconceptions (*"significant means important"*, *"this proves fraud"*), or challenges a method the
  student named (*"You said VLOOKUP — what if the column is to the left?"*). The review page shows **what the student said, written down** (browser speech recognition, or
  typed), a **checklist of the key points they mentioned or missed**, what the examiner listens for, the model
  answer and, optionally, their own recording. It also gives feedback on **how they sounded** (pace, filler
  phrases, time before starting). Students pick a **Friendly, Standard or Strict** examiner (time per question and
  one or two interruptions), can **retry a single question**, and see their **progress per question type** under
  *My attempts* (saved in the browser). No AI service is involved.

The site is static (HTML, CSS and JavaScript in `docs/`) and is served by GitHub Pages.

## How the content is made

The course folder contains cases and datasets but no exam questions, so the questions are written in
`generator/` and **every answer is computed from the same files students download**. The questions are new:
they use the course files and skills but do not repeat the case assignments or the reference practice site.
Many are written as audit-style checks — reconciliations, control tests, uniqueness and data-quality questions.

| Module | What it produces |
|---|---|
| `excel_questions.py` | NYC film permits (PwC), ETL cases 1–4, IntegrateCo payroll |
| `sql_questions.py` | Chinook, CS50 songs/movies/Fiftyville, OSU P-cards; each answer comes from running the reference query |
| `regression.py` | Two exams estimated on the restaurant case data, plus constructed business scenarios |
| `followups.py` | The examiner's follow-up question and "listens for" point for every question |
| `keypoints.py` | The checklist of key points a spoken answer should contain |
| `check_overlap.py` | Flags any question too similar to a list of reference prompts (e.g. another site's questions) |
| `build.py` | Copies the download files, builds practice subsets of the large databases, assembles exams, writes `docs/data/content.json` |

The two largest databases are cut down so they download quickly: `pcards_2014.db` (calendar year 2014)
and `movies_subset.db` (movies with at least 5,000 IMDb votes).

## Rebuilding

The generator expects the course materials (`Excel/`, `SQL/`) in the folder above this repository.

```bash
pip install -r generator/requirements.txt
python generator/build.py
```

Preview locally with `python -m http.server --directory docs`.
