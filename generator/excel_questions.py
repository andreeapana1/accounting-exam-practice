"""Excel questions. Every answer is computed from the course data files."""
import csv
import re
from collections import Counter, defaultdict

import openpyxl

from common import EXCEL, Bank, money, num

ETL = EXCEL / "2. ETL Assignment" / "Data"
INTEGRATECO = EXCEL / "3. IntegrateCo Assignment"
PWC = EXCEL / "1. PWC Assignment"


# ---------------------------------------------------------------- NYC permits
def nyc():
    b = Bank("nyc", "Excel")
    with open(PWC / "NYC_Film_Permits.txt", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())

    # Official answers from the course solution file; the simple ones are re-checked here.
    wb = openpyxl.load_workbook(PWC / "solutions.xlsx", data_only=True)
    official = {r[0]: r[2] for r in wb.active.iter_rows(min_row=3, values_only=True) if r[0]}
    assert official[1] == len(rows)
    assert official[2] == len(cols)
    assert official[3] == sum(1 for r in rows if r["ZipCode"] == "N/A")
    assert official[4] == sum(1 for r in rows if r["ZipCode"] != "N/A" and len(r["ZipCode"]) != 5)
    assert official[8] == len({r["EventType"] for r in rows})
    shooting = [r for r in rows if r["EventType"] == "Shooting Permit"]
    assert official[9] == Counter(r["EventType"] for r in rows).most_common(1)[0][0]
    assert official[10] == Counter(r["Category"] for r in shooting).most_common(1)[0][0]
    assert official[11] == sum(1 for r in shooting if r["Category"] == "Student")

    pct = lambda v, d=2: f"{v * 100:.{d}f}%"
    b.add("How many records does the NYC film permit table have (excluding the header)?",
          num(official[1]), "Import the file, then =COUNTA(A:A)-1 or check the row number of the last record.",
          1, ["import", "counting"])
    b.add("How many columns does the table have?", official[2],
          "=COUNTA(1:1) on the header row, or =COLUMNS(Table1).", 0.5, ["import"])
    b.add("How many records have a missing value for ZipCode?", official[3],
          'Missing zip codes are stored as the text "N/A", not as blanks: =COUNTIF(N:N,"N/A").', 1.5, ["missing data", "COUNTIF"])
    b.add("How many records have an invalid value for ZipCode (not a 5-digit code)?", official[4],
          'Add a helper column =LEN(N2) and filter for lengths other than 5, excluding "N/A" (two records have zip code 83).', 2, ["data quality", "LEN"])
    b.add("Which column has the same value for every record? Give the exact column name.", official[5],
          "Use a PivotTable or =COUNTA(UNIQUE(F2:F33503)) per column; EventAgency has only one value.", 1.5,
          ["UNIQUE", "PivotTable"])
    b.add("What is the oldest EnteredOn value? Give the complete date and time.",
          official[6].strftime("%-m/%-d/%Y %H:%M"), "=MIN(E2:E33503) formatted as date/time.", 1, ["dates", "MIN"])
    b.add("What is the newest EnteredOn value? Give the complete date and time.",
          official[7].strftime("%-m/%-d/%Y %H:%M"), "=MAX(E2:E33503) formatted as date/time.", 1, ["dates", "MAX"])
    b.add("How many different event types are there?", official[8],
          "=COUNTA(UNIQUE(B2:B33503)), or put EventType in PivotTable rows.", 1, ["UNIQUE", "PivotTable"])
    b.add("What is the most common event type?", official[9],
          "PivotTable: EventType in Rows, Count of EventID in Values, sort descending.", 1, ["PivotTable"])
    b.add("Considering only shooting permits, what is the most common Category?", official[10],
          "PivotTable filtered on EventType = Shooting Permit; Category in Rows, count, sort descending.", 1.5,
          ["PivotTable", "filtering"])
    b.add("How many shooting permits have been granted for student films?", official[11],
          '=COUNTIFS(B:B,"Shooting Permit",K:K,"Student")', 1, ["COUNTIFS"])
    b.add("What percentage of shooting permits required approval by more than one Community Board? (2 decimals)",
          pct(official[12]), 'Count shooting permits whose CommunityBoard(s) contains a comma: '
          '=COUNTIFS(B:B,"Shooting Permit",I:I,"*,*")/COUNTIF(B:B,"Shooting Permit")', 2.5,
          ["COUNTIFS", "wildcards", "percentages"])
    b.add("In which year did the number of shoots in Brooklyn first outnumber the shoots in Manhattan?", official[13],
          "Add a helper column =YEAR(C2); PivotTable with Year in Rows, Borough in Columns, count of EventID.", 2.5,
          ["YEAR", "PivotTable"])
    b.add("What percentage of shoots in Manhattan take place on or near Broadway? Round to the nearest percent.",
          pct(official[14], 0), 'Filter Borough = Manhattan and EventType = Shooting Permit, then '
          '=COUNTIFS(...,G:G,"*BROADWAY*")/COUNTIFS(...)', 2.5, ["wildcards", "COUNTIFS"])
    b.add("How many shooting permit applications since 2013 have been submitted from a foreign country?",
          official[15], 'Filter EventType = Shooting Permit, EnteredOn >= 1/1/2013 and Country <> "United States of America".',
          2, ["filtering", "dates"])
    b.add("What is the average duration of a shooting permit in hours, rounded to the nearest half hour?",
          f"{official[16]} hours", "Helper column =(D2-C2)*24, then =MROUND(AVERAGEIF(B:B,\"Shooting Permit\",O:O),0.5).",
          2.5, ["date arithmetic", "AVERAGEIF"])
    b.add("What was the duration of the shortest shoot, in minutes?", f"{official[17]} minute",
          "Helper column =(D2-C2)*24*60, then =MINIFS(...) for shooting permits.", 2, ["date arithmetic", "MINIFS"])
    b.add("What is the average lead time in days between EnteredOn and StartDateTime for shooting permits? "
          "Round to the nearest day.", f"{official[18]} days",
          "Helper column =C2-E2, then =ROUND(AVERAGEIF(B:B,\"Shooting Permit\",P:P),0).", 2, ["date arithmetic"])
    b.add("On which day of the week do shooting permits most often start? Give the full day name.", official[19],
          '=TEXT(C2,"dddd") in a helper column, then a PivotTable count.', 2, ["TEXT", "PivotTable"])
    b.add("What percentage of shooting permits include at least part of a day on a Friday? (2 decimals)",
          pct(official[20]), "A permit touches Friday if any date from INT(start) to INT(end) is a Friday. "
          "Helper: =SUMPRODUCT(--(WEEKDAY(ROW(INDIRECT(INT(C2)&\":\"&INT(D2))))=6))>0", 3.5,
          ["WEEKDAY", "date arithmetic"])
    return b.items


# ------------------------------------------------------------ ETL case 1
def etl1():
    b = Bank("etl1", "Excel")
    with open(ETL / "case 1" / "Analytics_mindset_case_studies_ETL_Case1.csv", newline="", encoding="utf-8-sig") as f:
        raw = list(csv.reader(f))
    header, rows = raw[0], [r for r in raw[1:] if any(c.strip() for c in r)]

    # Apple's name contains a comma that is not quoted, so its rows have one extra field.
    extra = [r for r in rows if len(r) > len(header)]
    dup_count = len(rows) - len({tuple(r) for r in rows})
    missing_ticker = sum(1 for r in rows if not r[0].strip())
    spaced_ticker = sum(1 for r in rows if " " in r[0].strip())
    cash = [r[3] for r in rows if len(r) == len(header)] + [r[4] for r in extra]
    suffixed = sum(1 for c in cash if re.search(r"\s[KM]$", c.strip()))
    paren = sum(1 for r in rows if r[-1].strip().startswith("("))
    inv_blank = sum(1 for r in rows if len(r) == len(header) and r[5].strip() in ("", "-"))

    b.add("How many data rows (excluding the header) does the ETL Case 1 balance sheet file contain, "
          "including any duplicates?", len(rows),
          "Open the .csv in a text editor or import it; count the rows below the header.", 1, ["import"])
    b.add("How many rows are exact duplicates of a row above them?", dup_count,
          "Data > Remove Duplicates (all columns) reports how many duplicate rows were removed.", 1.5,
          ["duplicates"])
    b.add("How many rows have a blank Ticker?", missing_ticker,
          "=COUNTBLANK(A2:A23) or filter Ticker on (Blanks). These rows have no unique identifier.", 1,
          ["missing data", "unique identifiers"])
    b.add("How many rows have a Ticker containing spaces (e.g. 'A M Z N')?", spaced_ticker,
          '=SUMPRODUCT(--ISNUMBER(SEARCH(" ",A2:A23))) — fix with =SUBSTITUTE(A2," ","").', 1.5,
          ["SUBSTITUTE", "text cleaning"])
    b.add("Which company's rows split into one column too many when the file is imported, and why?",
          "Apple, Inc. — the comma in the name is not enclosed in a text qualifier (quotes)",
          "Look for rows whose last column is filled when others are empty; the unquoted comma in "
          "'Apple, Inc.' is read as a delimiter.", 2, ["delimiters", "text qualifiers"])
    b.add("How many Cash values are written with a K or M suffix instead of a full number?", suffixed,
          '=COUNTIF(D2:D23,"* K")+COUNTIF(D2:D23,"* M") (after fixing the Apple rows).', 1.5,
          ["units of measurement", "COUNTIF"])
    b.add("After cleaning, what is Apple's 2018 Cash in dollars?", "25,900,000,000",
          '"25900 M" means 25,900 million: =VALUE(LEFT(D2,LEN(D2)-2))*1000000.', 1.5,
          ["units of measurement", "LEFT", "VALUE"])
    b.add("How many Total Depreciation values are written as negatives in parentheses, e.g. (14200000000)?", paren,
          '=COUNTIF(H2:H23,"(*")  — convert with =-VALUE(SUBSTITUTE(SUBSTITUTE(H2,"(",""),")","")).', 1.5,
          ["number formats", "SUBSTITUTE"])
    b.add("How many Inventories values are missing (blank or a dash)?", inv_blank,
          "Filter Inventories for blanks, spaces and '-' entries; decide whether they mean zero or unknown.", 1.5,
          ["missing data"])
    b.add("Total Current Assets for American Airlines 2016 is 10300 while Cash is 3220000000. What problem does this show?",
          "Inconsistent units — Total Current Assets is stated in millions, the other columns in dollars",
          "Compare magnitudes across columns: 10,300 million = 10.3 billion, so multiply that column by 1,000,000.", 1.5,
          ["units of measurement"])
    return b.items


# ------------------------------------------------------------ ETL case 2 / 3
def _case_rows(path, sheet):
    wb = openpyxl.load_workbook(path, read_only=True)
    return [r[:3] for r in wb[sheet].iter_rows(min_row=2, values_only=True) if r[0]]


def etl2():
    b = Bank("etl2", "Excel")
    rows = _case_rows(ETL / "case 2" / "Analytics_mindset_case_studies_ETL_Case2_Excel.xlsx", "Case 2")
    parsed = []
    for code, first, last in rows:
        m = re.fullmatch(r"([A-Z]{3})(\d+)-(\d+)([WM])", code)
        parsed.append(dict(loc=m[1], emp=int(m[2]), plant=int(m[3]), pay=m[4], first=first, last=last))
    loc = Counter(p["loc"] for p in parsed)
    lp = Counter(f'{p["loc"]}-{p["plant"]}' for p in parsed)
    top_lp, top_n = lp.most_common(1)[0]
    weekly = sum(p["pay"] == "W" for p in parsed)
    aus_max = max(p["plant"] for p in parsed if p["loc"] == "AUS")
    first = parsed[0]

    b.add("How many employees work in Germany (GER)?", loc["GER"],
          '=LEFT(A2,3) in a helper column, then =COUNTIF(D:D,"GER").', 1.5, ["LEFT", "COUNTIF"])
    b.add("How many employees are paid weekly?", weekly, '=RIGHT(A2,1), then =COUNTIF(G:G,"W").', 1.5,
          ["RIGHT", "COUNTIF"])
    b.add("Extract the EmpID from EmployeeCode. What is the EmpID of the first employee (Carl Rodriguez)?",
          first["emp"], "=MID(A2,4,4) — the EmpID is always four digits starting at position 4.", 1.5, ["MID"])
    b.add("Extract the PlantID (the digits after the hyphen). What is the highest PlantID used in Australia?",
          aus_max, '=MID(A2,FIND("-",A2)+1,2) then =MAXIFS(F:F,D:D,"AUS").', 2.5, ["MID", "FIND", "MAXIFS"])
    b.add("Create LocationPlantID in the form USA-12. How many distinct LocationPlantID values are there?", len(lp),
          '=LEFT(A2,3)&"-"&MID(A2,FIND("-",A2)+1,2), then =COUNTA(UNIQUE(H2:H598)).', 2.5,
          ["concatenation", "UNIQUE"])
    b.add("Which LocationPlantID has the most employees?", f"{top_lp} ({top_n} employees)",
          "PivotTable on LocationPlantID with a count, sorted descending.", 2.5, ["PivotTable"])
    b.add("Which country has the most employees, and how many?", f"{loc.most_common(1)[0][0]} ({loc.most_common(1)[0][1]})",
          "LEFT(A2,3) helper column, then PivotTable count by location.", 1.5, ["LEFT", "PivotTable"])
    b.add("How many employees are paid monthly at plant JAP-19?",
          sum(1 for p in parsed if p["loc"] == "JAP" and p["plant"] == 19 and p["pay"] == "M"),
          '=COUNTIFS(H:H,"JAP-19",G:G,"M")', 2, ["COUNTIFS"])
    return b.items


def _parse_case3(code):
    m = re.fullmatch(r"([A-Za-z]+)(\d+)-(\d+)([A-Za-z]+)", code)
    pay = {"W": "W", "We": "W", "M": "M", "Mo": "M"}[m[4]]
    return dict(loc=m[1], emp=int(m[2]), plant=int(m[3]), pay=pay, raw_pay=m[4])


def etl3():
    b = Bank("etl3", "Excel")
    rows = _case_rows(ETL / "case 3" / "Analytics_mindset_case_studies_ETL_Case3_Excel.xlsx", "Case 3 data")
    parsed = [dict(_parse_case3(c), first=f, last=l) for c, f, l in rows]
    loc = Counter(p["loc"] for p in parsed)
    monthly = sum(p["pay"] == "M" for p in parsed)
    two_digit = sum(p["plant"] >= 10 for p in parsed)
    lp = Counter(f'{p["loc"]}-{p["plant"]}' for p in parsed)
    can = Counter(p["plant"] for p in parsed if p["loc"] == "Canada").most_common(1)[0]
    emp_sum = sum(p["emp"] for p in parsed)

    b.add("Location codes have different lengths (e.g. US, ARG, Japan). How many employees work in Japan?", loc["Japan"],
          'Location = letters before the first digit: =LEFT(A2,MIN(FIND({0,1,2,3,4,5,6,7,8,9},A2&"0123456789"))-1), '
          'then =COUNTIF(D:D,"Japan").', 2.5, ["LEFT", "MIN", "FIND"])
    b.add("How many employees are paid monthly? (The pay period is recorded as M or Mo.)", monthly,
          'Pay period = text after the plant digits; =COUNTIF(G:G,"M")+COUNTIF(G:G,"Mo"), or normalise with '
          '=IF(LEFT(G2,1)="M","M","W").', 2, ["IF", "COUNTIF"])
    b.add("How many employees have a two-digit PlantID?", two_digit,
          'PlantID = digits after the hyphen: =IF(ISNUMBER(--MID(A2,FIND("-",A2)+2,1)),MID(A2,FIND("-",A2)+1,2),'
          'MID(A2,FIND("-",A2)+1,1)), then count values >= 10.', 3, ["MID", "FIND", "ISNUMBER", "VALUE"])
    b.add("What is the EmpID of Carl Rodriguez (EmployeeCode Japan177-3Mo)?", 177,
          'MID from the end of the location code up to the hyphen: =MID(A2,LEN(D2)+1,FIND("-",A2)-LEN(D2)-1).', 1.5,
          ["MID", "FIND"])
    b.add("Create LocationPlantID (e.g. US-8). How many distinct LocationPlantID values are there?", len(lp),
          '=D2&"-"&F2, then =COUNTA(UNIQUE(H2:H598)).', 3, ["concatenation", "UNIQUE"])
    b.add("Which plant number in Canada has the most employees?", f"Plant {can[0]} ({can[1]} employees)",
          '=COUNTIFS(D:D,"Canada",F:F,n) for each plant, or a PivotTable filtered on Canada.', 2.5, ["COUNTIFS"])
    b.add("What is the sum of all extracted EmpID values? (A quick check that your extraction is correct.)",
          num(emp_sum), "=SUM(E2:E598) — EmpID must be converted to a number with VALUE() first.", 2.5,
          ["VALUE", "control totals"])
    b.add("How many EmployeeCodes record the monthly pay period as Mo rather than M?",
          sum(len(p["raw_pay"]) == 2 for p in parsed),
          '=SUMPRODUCT(--(RIGHT(A2:A598,2)="Mo")), or =COUNTIF(A:A,"*Mo").', 2,
          ["RIGHT", "data quality"])
    return b.items


# ------------------------------------------------------------ ETL case 4
def etl4():
    b = Bank("etl4", "Excel")
    wb = openpyxl.load_workbook(ETL / "case 4" / "Analytics_mindset_case_studies_ETL_Case4_Excel.xlsx", data_only=True)
    je = [r for r in wb["JELineItems"].iter_rows(min_row=2, values_only=True) if r[0]]
    bu = {r[0]: r[1] for r in wb["BusinessUnits"].iter_rows(min_row=2, values_only=True) if r[0]}
    coa = {r[1]: (r[0].strip(), r[2], r[3]) for r in wb["ChartOfAccounts"].iter_rows(min_row=2, values_only=True) if r[1]}
    prep = {(r[1], r[2]): r[0].split("|")[0].strip() for r in wb["PreparerInfo"].iter_rows(min_row=2, values_only=True) if r[0]}
    src = {r[0]: r[1] for r in wb["Source"].iter_rows(min_row=2, values_only=True) if r[0]}

    f = lambda v: float(v) if v not in (None, "") else 0.0
    total_debit = sum(f(r[7]) for r in je)
    total_amount = sum(f(r[9]) for r in je)
    hotel_lines = sum(1 for r in je if bu[r[2]] == "HOTEL")
    revenue = sum(f(r[9]) for r in je if coa[r[1]][1] == "Revenue")
    by_prep = Counter(prep.get((r[3], r[2]), "UNKNOWN") for r in je)
    top_prep = by_prep.most_common(1)[0]
    pcard_debit = sum(f(r[7]) for r in je if src[r[4]] == "PURCHASE CARD")
    acct = coa[76930][0]
    payroll_exp = sum(f(r[9]) for r in je if "Payroll" in (coa[r[1]][2] or ""))

    b.add("How many journal-entry line items are there, and how many distinct journal entries (JENumber)?",
          f"{len(je)} line items, {len({r[0] for r in je})} journal entries",
          "=COUNTA(A2:A790) and =COUNTA(UNIQUE(A2:A790)).", 1.5, ["UNIQUE", "counting"])
    b.add("What is the sum of the Amount column? What does this tell you?",
          f"{money(total_amount)} — debits equal credits, so the journal is balanced",
          "=SUM(J2:J790). Debits are positive and credits negative, so a balanced ledger sums to zero.", 1.5,
          ["control totals"])
    b.add("What is the total of the Debit column?", money(total_debit), "=SUM(H2:H790)", 1, ["SUM"])
    b.add("What is the GLAccountName for GL account 76930?", acct,
          "=XLOOKUP(76930,ChartOfAccounts!B:B,ChartOfAccounts!A:A) — VLOOKUP fails because the name is left of the number.",
          1.5, ["XLOOKUP", "INDEX/MATCH"])
    b.add("How many line items belong to the HOTEL business unit?", hotel_lines,
          "Look up BusinessUnit with =INDEX(BusinessUnits!B:B,MATCH(C2,BusinessUnits!A:A,0)), then COUNTIF.", 2,
          ["INDEX/MATCH", "COUNTIF"])
    b.add("What is the total Amount posted to accounts with AccountType = Revenue?", money(revenue),
          "Look up AccountType from ChartOfAccounts, then =SUMIF(N:N,\"Revenue\",J:J). Revenue is a credit, so it is negative.",
          2.5, ["INDEX/MATCH", "SUMIF"])
    b.add("PreparerID is only unique within a business unit. Which preparer recorded the most line items?",
          f"{top_prep[0]} ({top_prep[1]} line items)",
          "Match on both PreparerID and BusinessUnitID: =INDEX(PreparerInfo!A:A,MATCH(1,(PreparerInfo!B:B=D2)*"
          "(PreparerInfo!C:C=C2),0)), then a PivotTable count.", 3.5, ["INDEX/MATCH", "array formulas",
                                                                       "unique identifiers"])
    b.add("What is the total debit amount for line items whose Source is PURCHASE CARD?", money(pcard_debit),
          "Look up Source from the Source tab with XLOOKUP on SourceID, then SUMIF.", 2, ["XLOOKUP", "SUMIF"])
    b.add("What is the net Amount posted to accounts whose AccountClass contains 'Payroll'?", money(payroll_exp),
          '=SUMIF(O:O,"*Payroll*",J:J) after looking up AccountClass.', 2.5, ["SUMIF", "wildcards"])
    return b.items


# ------------------------------------------------------------ IntegrateCo
def _read_pipe(name):
    with open(INTEGRATECO / name, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter="|"))


def jobcode(project):
    m = re.match(r"\d\d[HS]?(\d{3})", project)
    return m[1] if m else None


def integrateco():
    b = Bank("integrateco", "Excel")
    p15 = _read_pipe("Analytics_mindset_case_studies_IntegrateCo_2015payroll.csv")
    p16 = _read_pipe("Analytics_mindset_case_studies_IntegrateCo_2016payroll.csv")
    jobs = {r["Job_Code"]: r["Job_Description"] for r in _read_pipe("Analytics_mindset_case_studies_IntegrateCo_jobcodes.csv")}
    locs = {r["Employee_Name"]: r["Location"] for r in _read_pipe("Analytics_mindset_case_studies_IntegrateCo_locations.csv")}
    f = lambda v: float(v or 0)

    gross15 = sum(f(r["Reg_Pay"]) + f(r["OT_Pay"]) for r in p15)
    gross16 = sum(f(r["Gross_Wages"]) for r in p16)
    phantom = [r for r in p16 if not r["Employee_Number"].strip()]
    cost16 = sum(f(r["Gross_Wages"]) + f(r["SocSec_Medicare"]) + f(r["FUTA"]) + f(r["SUTA"]) + f(r["Work_Comp"]) for r in p16)

    ot = defaultdict(float)
    for r in p15:
        ot[(r["Emp_No"], f'{r["First_Name"]} {r["Last_Name"]}')] += f(r["OT_Pay"])
    (top_no, top_name), top_ot = max(ot.items(), key=lambda kv: kv[1])

    ot_job = defaultdict(float)
    for r in p15:
        ot_job[jobcode(r["Job"])] += f(r["OT_Pay"])
    top_job = max(ot_job.items(), key=lambda kv: kv[1])

    month = defaultdict(float)
    for r in p15:
        month[int(r["Pay_Date"].split("/")[0])] += f(r["Reg_Pay"]) + f(r["OT_Pay"])
    top_month = max(month.items(), key=lambda kv: kv[1])
    month_names = ["", "January", "February", "March", "April", "May", "June"]

    bad = [r for r in p15 if jobcode(r["Job"]) not in jobs]
    assert len(bad) == 1
    job005_15 = sum(f(r["Reg_Pay"]) + f(r["OT_Pay"]) for r in p15 if jobcode(r["Job"]) == "005")
    job005_16 = sum(f(r["Gross_Wages"]) for r in p16 if jobcode(r["Project"]) == "005")
    loc2 = sum(1 for v in locs.values() if v.strip() == "2")
    pay_dates = len({r["Pay_Date"] for r in p15})

    b.add("The IntegrateCo files are .csv files. Which delimiter do they actually use?", "The pipe character |",
          "Open the file in a text editor first. Import with Data > From Text/CSV and choose the | delimiter "
          "(or Text to Columns > Delimited > Other: |).", 1, ["delimiters", "import"])
    b.add("How many data rows does the 2015 payroll file contain?", num(len(p15)),
          "Import with the | delimiter, then =COUNTA(A:A)-1.", 1, ["import", "counting"])
    b.add("What is total gross pay (Reg_Pay + OT_Pay) in the first six months of 2015?", money(gross15),
          "=SUM(K:K)+SUM(L:L) on the 2015 data.", 1.5, ["SUM"])
    b.add("What is the difference between 2016 Gross_Wages and 2015 gross pay (2016 minus 2015)?",
          money(gross16 - gross15), "2016: =SUM(Gross_Wages). 2015: Reg_Pay + OT_Pay. In 2016 Gross_Wages already "
          "combines both, so the definitions must be aligned before comparing.", 2.5, ["aggregation", "comparability"])
    b.add("How many 2016 transactions have no Employee_Number ('phantom' entries)?", len(phantom),
          '=COUNTBLANK(C2:C805) on the 2016 data.', 1.5, ["missing data", "COUNTBLANK"])
    b.add("What is the total Gross_Wages of the 2016 entries without an Employee_Number?",
          money(sum(f(r["Gross_Wages"]) for r in phantom)), '=SUMIF(C:C,"",G:G)', 2, ["SUMIF", "missing data"])
    b.add("What was the total employee cost in 2016 (gross wages + SocSec_Medicare + FUTA + SUTA + Work_Comp)?",
          money(cost16), "=SUM(G:K) on the 2016 data.", 1.5, ["SUM"])
    b.add("Which employee earned the most overtime pay in 2015, and how much?",
          f"{top_name} (Emp_No {top_no}): {money(top_ot)}",
          "PivotTable on 2015 data: Emp_No and name in Rows, Sum of OT_Pay in Values, sort descending.", 2.5,
          ["PivotTable"])
    b.add("Extract the three-digit job code from the Job field (e.g. 14S001SG → 001). Which job code had the most "
          "overtime pay in 2015?", f"{top_job[0]} {jobs[top_job[0]]} ({money(top_job[1])})",
          'Job code = the three digits after the 2-digit year and optional H/S: '
          '=IF(ISNUMBER(--MID(H2,3,1)),MID(H2,3,3),MID(H2,4,3)), then a PivotTable on OT_Pay.', 3.5,
          ["MID", "IF", "ISNUMBER", "PivotTable"])
    b.add("In which month of 2015 was gross pay highest, and how much was it?",
          f"{month_names[top_month[0]]} ({money(top_month[1])})",
          "Helper column =MONTH(A2) and gross pay =K2+L2, then a PivotTable by month.", 2.5,
          ["MONTH", "PivotTable"])
    b.add("Job codes must be 001–012. Which Job value in the 2015 data contains an invalid job code?",
          f'{bad[0]["Job"]} (job code {jobcode(bad[0]["Job"])}, employee {bad[0]["First_Name"]} {bad[0]["Last_Name"]})',
          "Extract the job code from Job, then =ISNA(MATCH(L2,JobCodes!A:A,0)) and count TRUE. "
          "Keep job codes as text so 001 is not turned into 1.", 3, ["MATCH", "ISNA", "text vs number"])
    b.add("Why does a lookup from payroll job codes to jobcodes.csv fail when the job code file is opened directly in Excel?",
          "Excel converts 001 to the number 1, losing the leading zeros, so text '001' does not match number 1",
          "Import Job_Code as Text in the import wizard (or Power Query), keeping the three-digit code.", 1.5,
          ["text vs number", "import"])
    b.add("What are total gross wages for job code 005 (Installation) in 2015 and in 2016?",
          f"2015: {money(job005_15)}; 2016: {money(job005_16)}",
          "Extract job code in both years, then SUMIF on 005.", 3, ["SUMIF", "MID"])
    b.add("Using the locations file, how many employees work at location 2?", loc2,
          'Import with the | delimiter, then =COUNTIF(B:B,2).', 1, ["import", "COUNTIF"])
    b.add("How many different pay dates (payroll runs) are in the 2015 data?", pay_dates,
          "=COUNTA(UNIQUE(A2:A4982))", 1, ["UNIQUE"])
    return b.items


def all_questions():
    return nyc() + etl1() + etl2() + etl3() + etl4() + integrateco()
