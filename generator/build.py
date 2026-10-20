"""Build docs/data/content.json and docs/files/ from the course materials.

Run from the repository root:  python generator/build.py
"""
import json
import random
import shutil
import zipfile

import excel_questions
import followups
import regression
import sql_questions
from common import DATA, EXCEL, FILES

ETL = EXCEL / "2. ETL Assignment" / "Data"
INTEGRATECO = EXCEL / "3. IntegrateCo Assignment"

DATASETS = {
    "nyc": dict(name="NYC film permits", tool="Excel", file="NYC_Film_Permits.csv",
                case="PwC Excel assignment",
                about="33,502 film permits issued by New York City (2011–2018): event type, start and end date/time, "
                      "borough, community boards, category and zip code. Comma-separated with quoted text fields."),
    "etl1": dict(name="Balance sheet extract (messy)", tool="Excel", file="ETL_Case1_balance_sheets.csv",
                 case="ETL Case 1 – Identifying data problems",
                 about="Balance sheet data for several companies (2016–2018). Contains duplicates, unquoted commas, "
                       "K/M suffixes, numbers in parentheses and inconsistent units."),
    "etl2": dict(name="Employee codes", tool="Excel", file="ETL_Case2_employee_codes.xlsx",
                 case="ETL Case 2 – Text extraction",
                 about="597 employees. EmployeeCode combines Location (3 letters), EmpID (4 digits), PlantID "
                       "(after the hyphen) and PayPeriod (W/M), e.g. JAP1080-19M."),
    "etl3": dict(name="Employee codes (messy)", tool="Excel", file="ETL_Case3_employee_codes_messy.xlsx",
                 case="ETL Case 3 – Advanced text extraction",
                 about="Same idea as Case 2 but messier: location codes of different lengths (US, ARG, Japan), "
                       "1–3 digit EmpIDs, 1–2 digit PlantIDs and pay periods recorded as W, M or Mo."),
    "etl4": dict(name="Hotel journal entries", tool="Excel", file="ETL_Case4_journal_entries.xlsx",
                 case="ETL Case 4 – Joining data",
                 about="789 journal-entry lines for a hotel and conference center with lookup tabs: BusinessUnits, "
                       "ChartOfAccounts, PreparerInfo (PreparerID unique only within a business unit) and Source."),
    "integrateco": dict(name="IntegrateCo payroll", tool="Excel", file="IntegrateCo_payroll.zip",
                        case="IntegrateCo case",
                        about="Pipe-delimited (|) .csv files: 2015 payroll (one row per employee, job and pay date), "
                              "2016 payroll from a new system (no dates, Gross_Wages combined), job codes (001–012, "
                              "stored as text) and employee locations."),
    "chinook": dict(name="Chinook music store", tool="SQL", file="Chinook_Sqlite.sqlite",
                    case="PwC SQL assignment",
                    about="A digital music store: Customer, Invoice, InvoiceLine, Track, Album, Artist, Genre, "
                          "Employee, MediaType and Playlist tables."),
    "songs": dict(name="Spotify top songs", tool="SQL", file="songs.db", case="CS50 songs",
                  about="Tables songs (name, artist_id, danceability, energy, valence, tempo, duration_ms, …) "
                        "and artists (id, name)."),
    "movies": dict(name="IMDb movies · practice subset", tool="SQL", file="movies_subset.db", case="CS50 movies",
                   about="Movies with at least 5,000 IMDb votes. Tables movies, people, stars, directors and "
                         "ratings. Answers on this site are computed on this subset."),
    "fiftyville": dict(name="Fiftyville mystery", tool="SQL", file="fiftyville.db", case="CS50 Fiftyville",
                       about="Town records: crime_scene_reports, interviews, courthouse_security_logs, "
                             "atm_transactions, bank_accounts, phone_calls, flights, airports, passengers, people."),
    "pcards": dict(name="OSU purchasing cards · 2014", tool="SQL", file="pcards_2014.db", case="P-card case",
                   about="All 116,031 Oklahoma State University P-card transactions in calendar year 2014 (table "
                         "pcards). Negative amounts are returns. TransactionDate is stored as text (M/D/YYYY)."),
}
EXAM_SQL = ["chinook", "songs", "movies", "pcards"]
EXAM_EXCEL = ["nyc", "etl1", "etl2", "etl3", "etl4", "integrateco"]
EXAM_MINUTES = 8


def copy_excel_files():
    shutil.copy(EXCEL / "1. PWC Assignment" / "NYC_Film_Permits.txt", FILES / "NYC_Film_Permits.csv")
    shutil.copy(ETL / "case 1" / "Analytics_mindset_case_studies_ETL_Case1.csv", FILES / "ETL_Case1_balance_sheets.csv")
    shutil.copy(ETL / "case 2" / "Analytics_mindset_case_studies_ETL_Case2_Excel.xlsx", FILES / "ETL_Case2_employee_codes.xlsx")
    shutil.copy(ETL / "case 3" / "Analytics_mindset_case_studies_ETL_Case3_Excel.xlsx",
                FILES / "ETL_Case3_employee_codes_messy.xlsx")
    shutil.copy(ETL / "case 4" / "Analytics_mindset_case_studies_ETL_Case4_Excel.xlsx", FILES / "ETL_Case4_journal_entries.xlsx")
    with zipfile.ZipFile(FILES / "IntegrateCo_payroll.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for part in ["2015payroll", "2016payroll", "jobcodes", "locations"]:
            name = f"Analytics_mindset_case_studies_IntegrateCo_{part}.csv"
            z.write(INTEGRATECO / name, name)


def make_exams(questions, per_pair=5, seed=7):
    """Each exam: one Excel file + one SQL database, five questions that fit in about eight minutes."""
    rng = random.Random(seed)
    by_ds = {}
    for q in questions:
        by_ds.setdefault(q["dataset"], []).append(q)
    exams, seen = [], set()
    pairs = [(e, s) for e in EXAM_EXCEL for s in EXAM_SQL]
    for k in range(per_pair):
        rng.shuffle(pairs)
        for e, s in pairs:
            for _ in range(5000):
                n_excel = rng.choice([2, 3])
                picked = rng.sample(by_ds[e], n_excel) + rng.sample(by_ds[s], 5 - n_excel)
                total = sum(q["minutes"] for q in picked)
                key = frozenset(q["id"] for q in picked)
                if 6 <= total <= EXAM_MINUTES and key not in seen:
                    break
            else:
                raise RuntimeError(f"no exam of at most {EXAM_MINUTES} minutes found for {e} + {s}")
            seen.add(key)
            picked.sort(key=lambda q: (q["tool"] != "Excel", q["id"]))
            exams.append({"datasets": [e, s], "questions": [q["id"] for q in picked],
                          "minutes": EXAM_MINUTES, "estimate": round(sum(q["minutes"] for q in picked), 1)})
    for i, ex in enumerate(exams, 1):
        ex["id"] = f"E{i:03d}"
    return exams


def main():
    FILES.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    copy_excel_files()
    questions = excel_questions.all_questions() + sql_questions.all_questions()
    for i, q in enumerate(questions, 1):
        q["id"] = f"Q{i:03d}"
    for key, ds in DATASETS.items():
        ds["size"] = (FILES / ds["file"]).stat().st_size
        ds["questions"] = sum(q["dataset"] == key for q in questions)
    regression_exams = regression.all_exams()
    followups.add_followups(questions, regression_exams)
    content = {
        "datasets": DATASETS,
        "questions": questions,
        "exams": make_exams(questions),
        "regression": regression_exams,
    }
    (DATA / "content.json").write_text(json.dumps(content, ensure_ascii=False, indent=1))
    print(f"{len(questions)} questions, {len(content['exams'])} exams, {len(content['regression'])} regression exams")


if __name__ == "__main__":
    main()
