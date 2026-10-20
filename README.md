# Exam Practice · Data Analytics in Accounting

A practice website for the oral exam in *Data Analytics in Accounting*. Students practise:

- **Data manipulation exams**: one Excel file plus one SQL database, five questions in eight minutes.
- **A question bank**: every Excel and SQL question, filterable by tool, dataset and skill.
- **Data interpretation exams**: regression output with four questions (predict, interpret, significance, reliability) in five minutes.

The site is static (HTML, CSS and JavaScript in `docs/`) and is served by GitHub Pages.

## How the content is made

The course folder contains cases and datasets but no exam questions, so the questions are written in
`generator/` and **every answer is computed from the same files students download**:

| Module | What it produces |
|---|---|
| `excel_questions.py` | NYC film permits (PwC), ETL cases 1–4, IntegrateCo payroll |
| `sql_questions.py` | Chinook, CS50 songs/movies/Fiftyville, OSU P-cards; each answer comes from running the reference query |
| `regression.py` | Two exams estimated on the restaurant case data, plus constructed business scenarios |
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
