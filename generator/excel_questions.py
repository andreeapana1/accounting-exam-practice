"""Excel questions. Every answer is computed from the course data files.

The questions are written for this site: they test the same files and skills as the course cases, but ask
new questions (mostly data-quality, reconciliation and control-style checks) rather than repeating the case
assignments or the questions on the reference practice site.
"""
import csv
import re
from collections import Counter, defaultdict
from datetime import datetime

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
    t = lambda s: datetime.strptime(s, "%m/%d/%Y %H:%M")
    for r in rows:
        r["s"], r["e"], r["en"] = t(r["StartDateTime"]), t(r["EndDateTime"]), t(r["EnteredOn"])

    late_entry = [r for r in rows if r["en"] > r["s"]]
    zips_na = sum(r["ZipCode"] == "N/A" for r in rows)
    zips_bad = sum(r["ZipCode"] != "N/A" and len(r["ZipCode"]) != 5 for r in rows)
    multi_precinct = sum("," in r["PolicePrecinct(s)"] for r in rows)
    boards3 = sum(len([x for x in r["CommunityBoard(s)"].split(",") if x.strip()]) >= 3 for r in rows)
    weekend = sum(r["s"].weekday() >= 5 for r in rows)
    early = sum(r["s"].hour < 7 for r in rows)
    longest = max(rows, key=lambda r: r["e"] - r["s"])
    longest_days = (longest["e"] - longest["s"]).total_seconds() / 86400
    overnight = sum(r["e"].date() > r["s"].date() for r in rows)
    month = Counter(r["s"].strftime("%B") for r in rows).most_common(1)[0]
    quiet_day = Counter(r["s"].strftime("%A") for r in rows).most_common()[-1]
    zips = len({r["ZipCode"] for r in rows if r["ZipCode"] != "N/A"})
    same_day = sum(r["s"].date() == r["en"].date() for r in rows)

    b.add("Is EventID a reliable unique identifier? Compare the number of distinct EventIDs with the number of records.",
          f"Yes — {num(len({r['EventID'] for r in rows}))} distinct EventIDs for {num(len(rows))} records",
          "=COUNTA(UNIQUE(A2:A33503)) versus =COUNTA(A2:A33503). Equal counts mean no EventID repeats.", 1.5,
          ["unique identifiers", "UNIQUE"])
    b.add("Missing zip codes are not blank cells. How are they recorded, and how many are there?",
          f'As the text "N/A" — {zips_na} records',
          'Filter the ZipCode column and look at the values: =COUNTIF(N:N,"N/A"). COUNTBLANK would return 0.', 1.5,
          ["missing data", "COUNTIF"])
    b.add("Apart from N/A, how many zip codes are not valid five-digit codes?", zips_bad,
          'Helper column =LEN(N2); count lengths other than 5 that are not "N/A".', 2, ["data quality", "LEN"])
    b.add("Which column contains exactly the same value in every record, so it adds nothing to the analysis?",
          "EventAgency", "Check each column with =COUNTA(UNIQUE(range)); the column with a count of 1 is constant.", 1.5,
          ["UNIQUE", "data quality"])
    b.add("Data check: how many permits were entered (EnteredOn) after the shoot had already started?",
          len(late_entry), "Helper column =E2>C2 (EnteredOn later than StartDateTime), then =COUNTIF(O:O,TRUE). "
          "These records are worth questioning.", 2, ["dates", "data quality", "COUNTIF"])
    b.add("How many permits list more than one police precinct?", num(multi_precinct),
          'Several precincts are separated by commas: =COUNTIF(J:J,"*,*").', 1.5, ["wildcards", "COUNTIF"])
    b.add("How many permits need three or more community boards?", boards3,
          'Count the commas: =LEN(I2)-LEN(SUBSTITUTE(I2,",",""))+1 gives the number of boards; count values >= 3.', 3,
          ["LEN", "SUBSTITUTE", "COUNTIF"])
    b.add("How many permits start on a Saturday or a Sunday?", num(weekend),
          "Helper column =WEEKDAY(C2,2) (Monday = 1); count values of 6 or 7.", 2, ["WEEKDAY", "COUNTIF"])
    b.add("What share of all permits start before 7:00 in the morning? (1 decimal)", f"{early / len(rows) * 100:.1f}%",
          "Helper column =HOUR(C2); =COUNTIF(P:P,\"<7\")/COUNTA(P:P).", 2, ["dates", "COUNTIF", "percentages"])
    b.add("Which permit lasts the longest, and how many days does it cover? (1 decimal)",
          f"EventID {longest['EventID']} ({longest['EventType']}): {longest_days:.1f} days",
          "Helper column =D2-C2 (days); sort descending or use =MAX() with XLOOKUP to find the EventID.", 2,
          ["date arithmetic", "MAX", "XLOOKUP"])
    b.add("How many shoots run overnight, i.e. end on a later calendar day than they start?", num(overnight),
          "=INT(D2)>INT(C2) in a helper column (INT drops the time of day), then count TRUE.", 2,
          ["dates", "date arithmetic"])
    b.add("In which calendar month (across all years) do the most permits start?",
          f"{month[0]} ({num(month[1])} permits)", '=TEXT(C2,"mmmm") helper column, then a PivotTable count.', 2,
          ["TEXT", "PivotTable"])
    b.add("On which day of the week do the fewest permits start?", f"{quiet_day[0]} ({num(quiet_day[1])} permits)",
          '=TEXT(C2,"dddd") helper column, then a PivotTable count sorted ascending.', 2, ["TEXT", "PivotTable"])
    b.add("How many different (valid) zip codes appear in the data?", zips,
          '=COUNTA(UNIQUE(FILTER(N2:N33503,N2:N33503<>"N/A")))', 2, ["UNIQUE", "filtering"])
    b.add("How many permits were entered on the same calendar day as the shoot starts?", num(same_day),
          "=INT(C2)=INT(E2) in a helper column (INT removes the time), then count TRUE.", 2,
          ["dates", "date arithmetic"])
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
    mex = [p for p in parsed if p["loc"] == "MEX"]
    aus_max = max(p["plant"] for p in parsed if p["loc"] == "AUS")
    first = parsed[0]
    emp_dupes = sum(n > 1 for n in Counter(p["emp"] for p in parsed).values())
    missing_ids = len(set(range(1000, 1598)) - {p["emp"] for p in parsed})
    names = Counter((p["first"], p["last"]) for p in parsed)
    shared_names = sum(n > 1 for n in names.values())

    b.add("How many employees work in Germany (GER)?", loc["GER"],
          '=LEFT(A2,3) in a helper column, then =COUNTIF(D:D,"GER").', 1.5, ["LEFT", "COUNTIF"])
    b.add("What share of the employees in Mexico are paid weekly? (1 decimal)",
          f"{sum(p['pay'] == 'W' for p in mex) / len(mex) * 100:.1f}%",
          '=RIGHT(A2,1) and =LEFT(A2,3) helper columns, then =COUNTIFS(D:D,"MEX",G:G,"W")/COUNTIF(D:D,"MEX").', 2,
          ["RIGHT", "COUNTIFS", "percentages"])
    b.add("Extract the EmpID from EmployeeCode. What is the EmpID of the first employee (Carl Rodriguez)?",
          first["emp"], "=MID(A2,4,4) — the EmpID is always four digits starting at position 4.", 1.5, ["MID"])
    b.add("Extract the PlantID (the digits after the hyphen). What is the highest PlantID used in Australia?",
          aus_max, '=MID(A2,FIND("-",A2)+1,2) then =MAXIFS(F:F,D:D,"AUS").', 2.5, ["MID", "FIND", "MAXIFS"])
    b.add("Create LocationPlantID in the form USA-12. How many distinct LocationPlantID values are there?", len(lp),
          '=LEFT(A2,3)&"-"&MID(A2,FIND("-",A2)+1,2), then =COUNTA(UNIQUE(H2:H598)).', 2.5,
          ["concatenation", "UNIQUE"])
    b.add("Which LocationPlantID has the most employees?", f"{top_lp} ({top_n} employees)",
          "PivotTable on LocationPlantID with a count, sorted descending.", 2.5, ["PivotTable"])
    assert emp_dupes == 0 and shared_names == 0
    b.add("EmpIDs are assigned from 1,000 to 1,597. Are they unique, and how many numbers in that range are not used?",
          f"Unique (no EmpID repeats); {missing_ids} number in the range is unused",
          "Extract EmpID with =MID(A2,4,4); =COUNTA(UNIQUE(E2:E598)) equals the row count, and 598 possible IDs minus "
          "597 used leaves the unused number.", 2.5, ["unique identifiers", "UNIQUE", "control totals"])
    fewest = loc.most_common()[-1]
    b.add("Which country has the fewest employees, and how many?", f"{fewest[0]} ({fewest[1]})",
          "=LEFT(A2,3) helper column, then a PivotTable count sorted ascending.", 1.5, ["LEFT", "PivotTable"])
    return b.items


def _parse_case3(code):
    m = re.fullmatch(r"([A-Za-z]+)(\d+)-(\d+)([A-Za-z]+)", code)
    pay = {"W": "W", "We": "W", "M": "M", "Mo": "M"}[m[4]]
    return dict(loc=m[1], emp=int(m[2]), plant=int(m[3]), pay=pay, raw_pay=m[4], code=code)


def etl3():
    b = Bank("etl3", "Excel")
    rows = _case_rows(ETL / "case 3" / "Analytics_mindset_case_studies_ETL_Case3_Excel.xlsx", "Case 3 data")
    parsed = [dict(_parse_case3(c), first=f, last=l) for c, f, l in rows]
    loc = Counter(p["loc"] for p in parsed)
    emp_sum = sum(p["emp"] for p in parsed)
    emp_dupes = sum(n > 1 for n in Counter(p["emp"] for p in parsed).values())
    max_plant = max(parsed, key=lambda p: p["plant"])
    longest = max(parsed, key=lambda p: len(p["code"]))
    by_plant = defaultdict(set)
    for p in parsed:
        by_plant[(p["loc"], p["plant"])].add(p["pay"])
    weekly_only = sum(v == {"W"} for v in by_plant.values())
    ger_plants = len({p["plant"] for p in parsed if p["loc"] == "GER"})
    us_three = sum(1 for p in parsed if p["loc"] == "US" and p["emp"] >= 100)

    b.add("Location codes have different lengths (e.g. US, ARG, Japan). How many employees work in Japan?", loc["Japan"],
          'Location = letters before the first digit: =LEFT(A2,MIN(FIND({0,1,2,3,4,5,6,7,8,9},A2&"0123456789"))-1), '
          'then =COUNTIF(D:D,"Japan").', 2.5, ["LEFT", "MIN", "FIND"])
    b.add("How many employees work in the two countries that do not use a three-letter code (Canada and Japan)?",
          loc["Canada"] + loc["Japan"], 'Extract the location, then =COUNTIF(D:D,"Canada")+COUNTIF(D:D,"Japan").', 2.5,
          ["LEFT", "FIND", "COUNTIF"])
    b.add("What is the EmpID of Carl Rodriguez (EmployeeCode Japan177-3Mo)?", 177,
          'MID from the end of the location code up to the hyphen: =MID(A2,LEN(D2)+1,FIND("-",A2)-LEN(D2)-1).', 1.5,
          ["MID", "FIND"])
    b.add("Is EmpID unique in Case 3? How many EmpID values appear more than once?",
          f"{emp_dupes} — every EmpID is used once, so it can serve as an identifier" if emp_dupes == 0 else emp_dupes,
          "Extract EmpID, then a PivotTable count (or COUNTIF) and look for counts above 1.", 3,
          ["unique identifiers", "MID", "FIND"])
    b.add("What is the sum of all extracted EmpID values? (A control total for your extraction.)", num(emp_sum),
          "=SUM(E2:E598) — EmpID must be converted to a number with VALUE() first.", 2.5, ["VALUE", "control totals"])
    top_plant = max_plant["plant"]
    b.add("What is the highest PlantID number in use, and how many employees work at a plant with that number "
          "(in any country)?", f"Plant {top_plant}: {sum(p['plant'] == top_plant for p in parsed)} employees",
          'Extract PlantID as a number with =VALUE(MID(A2,FIND("-",A2)+1,2)) (stripping letters), then =MAX(F:F) and '
          '=COUNTIF(F:F,MAX(F:F)).', 3, ["MID", "FIND", "VALUE", "COUNTIF"])
    max_len = len(longest["code"])
    b.add("What is the length of the longest EmployeeCode, and how many codes have that length?",
          f"{max_len} characters, {sum(len(p['code']) == max_len for p in parsed)} codes",
          "=LEN(A2) in a helper column, then =MAX(D:D) and =COUNTIF(D:D,MAX(D:D)).", 1.5, ["LEN", "MAX", "COUNTIF"])
    b.add("After building LocationPlantID (e.g. US-8), how many plants employ only weekly-paid staff?", weekly_only,
          "Normalise PayPeriod to W/M, then a PivotTable with LocationPlantID in rows and PayPeriod in columns; "
          "count plants with no M employees.", 3.5, ["PivotTable", "concatenation", "IF"])
    b.add("How many different plants does Germany operate?", ger_plants,
          '=COUNTA(UNIQUE(FILTER(F2:F598,D2:D598="GER"))) using the extracted Location and PlantID.', 2.5,
          ["UNIQUE", "filtering"])
    b.add("How many US employees have an EmpID of 100 or more (three digits)?", us_three,
          '=COUNTIFS(D:D,"US",E:E,">=100") after converting EmpID to a number.', 2.5, ["COUNTIFS", "VALUE"])
    return b.items


# ------------------------------------------------------------ ETL case 4
def etl4():
    b = Bank("etl4", "Excel")
    wb = openpyxl.load_workbook(ETL / "case 4" / "Analytics_mindset_case_studies_ETL_Case4_Excel.xlsx", data_only=True)
    je = [r for r in wb["JELineItems"].iter_rows(min_row=2, values_only=True) if r[0]]
    coa_rows = [r for r in wb["ChartOfAccounts"].iter_rows(min_row=2, values_only=True) if r[1]]
    coa = {r[1]: (r[0].strip(), r[2], r[3]) for r in coa_rows}
    prep = {(r[1], r[2]): r[0].split("|")[0].strip() for r in wb["PreparerInfo"].iter_rows(min_row=2, values_only=True) if r[0]}

    f = lambda v: float(v) if v not in (None, "") else 0.0
    total_amount = sum(f(r[9]) for r in je)
    by_je = defaultdict(float)
    debit_by_je = defaultdict(float)
    desc = {}
    for r in je:
        by_je[r[0]] += f(r[9])
        debit_by_je[r[0]] += f(r[7])
        desc[r[0]] = r[6]
    unbalanced = sum(abs(v) > 0.005 for v in by_je.values())
    biggest = max(debit_by_je.items(), key=lambda kv: kv[1])
    revenue = sum(f(r[9]) for r in je if coa[r[1]][1] == "Revenue")
    system_lines = sum(1 for r in je if prep.get((r[3], r[2])) in ("POS", "GUESTSYS"))
    weekend = sum(1 for r in je if r[5].weekday() >= 5)
    used = {r[1] for r in je}
    unused = len(set(coa) - used)
    acct = coa[76930][0]
    days = len({r[5].date() for r in je})
    debit_credit_mismatch = sum(1 for r in je if f(r[7]) and f(r[8]))

    b.add("How many journal-entry line items are there, and how many distinct journal entries (JENumber)?",
          f"{len(je)} line items, {len({r[0] for r in je})} journal entries",
          "=COUNTA(A2:A790) and =COUNTA(UNIQUE(A2:A790)).", 1.5, ["UNIQUE", "counting"])
    b.add("What is the sum of the Amount column? What does this tell you?",
          f"{money(total_amount)} — debits equal credits, so the journal is balanced overall",
          "=SUM(J2:J790). Debits are positive and credits negative, so a balanced ledger sums to zero.", 1.5,
          ["control totals"])
    b.add("Does every individual journal entry balance? How many JENumbers have debits that do not equal credits?",
          f"{unbalanced} — every journal entry balances on its own" if unbalanced == 0 else unbalanced, "PivotTable with JENumber in rows and Sum of Amount; any entry not equal to 0 is unbalanced. "
          "Or =SUMIF(A:A,A2,J:J) per line.", 3, ["control totals", "SUMIF", "PivotTable"])
    b.add("Which journal entry has the largest total debit, and what is its description?",
          f"JE {biggest[0]}: {money(biggest[1])} ({desc[biggest[0]]})",
          "PivotTable: JENumber in rows, Sum of Debit, sorted descending; look up JEDescription.", 2.5,
          ["PivotTable", "XLOOKUP"])
    b.add("What is the GLAccountName for GL account 76930?", acct,
          "=XLOOKUP(76930,ChartOfAccounts!B:B,ChartOfAccounts!A:A) — VLOOKUP fails because the name is left of the number.",
          1.5, ["XLOOKUP", "INDEX/MATCH"])
    b.add("What is the total Amount posted to accounts with AccountType = Revenue?", money(revenue),
          "Look up AccountType from ChartOfAccounts, then =SUMIF(N:N,\"Revenue\",J:J). Revenue is a credit, so it is negative.",
          2.5, ["INDEX/MATCH", "SUMIF"])
    b.add("How many line items were recorded by a system (POS or GUESTSYS) rather than by a person?", system_lines,
          "Look up PreparerName on both PreparerID and BusinessUnitID (PreparerID alone is not unique), then count "
          "POS and GUESTSYS.", 3, ["array formulas", "INDEX/MATCH", "COUNTIF"])
    b.add("How many line items have an EffectiveDate that falls on a weekend?", weekend,
          "=WEEKDAY(F2,2)>=6 in a helper column, then count TRUE.", 2, ["WEEKDAY", "dates"])
    b.add("How many accounts in the chart of accounts are never used in the journal?", unused,
          "In ChartOfAccounts add =COUNTIF(JELineItems!B:B,B2) and count the zeros.", 2.5, ["COUNTIF", "control totals"])
    b.add("Over how many different days do the journal entries run?", days,
          "=COUNTA(UNIQUE(F2:F790)) on EffectiveDate.", 1, ["UNIQUE", "dates"])
    b.add("Data check: how many line items have both a Debit and a Credit filled in?",
          f"{debit_credit_mismatch} — each line is either a debit or a credit" if debit_credit_mismatch == 0
          else debit_credit_mismatch,
          '=COUNTIFS(H:H,"<>",I:I,"<>") — each line should be either a debit or a credit.', 1.5,
          ["data quality", "COUNTIFS"])
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
    locs = {r["Employee_Name"]: r["Location"].strip() for r in _read_pipe("Analytics_mindset_case_studies_IntegrateCo_locations.csv")}
    f = lambda v: float(v or 0)

    gross15 = sum(f(r["Reg_Pay"]) + f(r["OT_Pay"]) for r in p15)
    gross16 = sum(f(r["Gross_Wages"]) for r in p16)
    phantom = [r for r in p16 if not r["Employee_Number"].strip()]

    ot = defaultdict(float)
    for r in p15:
        ot[(r["Emp_No"], f'{r["First_Name"]} {r["Last_Name"]}')] += f(r["OT_Pay"])
    (top_no, top_name), top_ot = max(ot.items(), key=lambda kv: kv[1])

    # Overtime without 40 regular hours in the same pay period (all pay on one date = one period).
    period = defaultdict(lambda: [0.0, 0.0])
    for r in p15:
        k = (f'{r["First_Name"]} {r["Last_Name"]}', r["Pay_Date"])
        period[k][0] += f(r["Reg_Hrs"])
        period[k][1] += f(r["OT_Hrs"])
    early_ot = [k for k, (reg, o) in period.items() if reg < 40 and o > 0]

    bad = [r for r in p15 if jobcode(r["Job"]) not in jobs]
    assert len(bad) == 1
    emp15 = {r["Emp_No"] for r in p15}
    emp16 = {r["Employee_Number"] for r in p16 if r["Employee_Number"].strip()}
    left = len(emp15 - emp16)
    new = len(emp16 - emp15)
    loc2 = sum(1 for v in locs.values() if v == "2")
    unmatched = {r["Employee_Name"] for r in p16 if r["Employee_Name"].strip() and r["Employee_Name"] not in locs}
    rate = {}
    for L in ("1", "2"):
        rs = [r for r in p16 if locs.get(r["Employee_Name"]) == L]
        hrs = sum(f(r["Hours"]) + f(r["OT_Hours"]) for r in rs)
        rate[L] = sum(f(r["Gross_Wages"]) for r in rs) / hrs
    zero_rows = sum(1 for r in p16 if f(r["Gross_Wages"]) == 0 and f(r["Hours"]) == 0)

    b.add("The IntegrateCo files are .csv files. Which delimiter do they actually use, and what happens if you just "
          "double-click to open one?", "The pipe character | — everything lands in a single column",
          "Open the file in a text editor first. Import with Data > From Text/CSV and choose the | delimiter "
          "(or Text to Columns > Delimited > Other: |).", 1, ["delimiters", "import"])
    b.add("What is the difference between 2016 Gross_Wages and 2015 gross pay (Reg_Pay + OT_Pay), 2016 minus 2015?",
          money(gross16 - gross15), "2016: =SUM(Gross_Wages). 2015: Reg_Pay + OT_Pay. In 2016 Gross_Wages already "
          "combines both, so the definitions must be aligned before comparing.", 2.5, ["aggregation", "comparability"])
    b.add("How many 2016 rows have no Employee_Number ('phantom' entries), and what are their total Gross_Wages?",
          f"{len(phantom)} rows, {money(sum(f(r['Gross_Wages']) for r in phantom))}",
          '=COUNTBLANK(C2:C805) and =SUMIF(C:C,"",G:G) on the 2016 data.', 2, ["missing data", "COUNTBLANK", "SUMIF"])
    b.add("Which employee earned the most overtime pay in 2015, and how much?",
          f"{top_name} (Emp_No {top_no}): {money(top_ot)}",
          "PivotTable on 2015 data: Emp_No and name in Rows, Sum of OT_Pay in Values, sort descending. Group on "
          "Emp_No — two different employees share the name Cynthia Lunt.", 2.5, ["PivotTable", "unique identifiers"])
    b.add("Control test: in how many employee pay periods in 2015 was overtime paid although the employee had "
          "fewer than 40 regular hours?", len(early_ot),
          "PivotTable with employee and Pay_Date in rows, Sum of Reg_Hrs and Sum of OT_Hrs; count rows with "
          "Reg_Hrs < 40 and OT_Hrs > 0.", 3.5, ["PivotTable", "internal controls"])
    b.add("Job codes must be 001–012. Which Job value in the 2015 data contains an invalid job code?",
          f'{bad[0]["Job"]} (job code {jobcode(bad[0]["Job"])}, employee {bad[0]["First_Name"]} {bad[0]["Last_Name"]})',
          "Extract the job code from Job, then =ISNA(MATCH(L2,JobCodes!A:A,0)) and look for TRUE. "
          "Keep job codes as text so 001 is not turned into 1.", 3, ["MID", "MATCH", "ISNA", "text vs number"])
    b.add("Why does a lookup from payroll job codes to jobcodes.csv fail when the job code file is opened directly in Excel?",
          "Excel converts 001 to the number 1, losing the leading zeros, so text '001' does not match number 1",
          "Import Job_Code as Text in the import wizard (or Power Query), keeping the three-digit code.", 1.5,
          ["text vs number", "import"])
    b.add("How many 2015 employees (Emp_No) do not appear in the 2016 data, and how many 2016 employees are new?",
          f"{left} left, {new} new", "Use COUNTIF of each Emp_No in the other year's Employee_Number column and count "
          "zeros. Turnover is one possible reason for the payroll change.", 3, ["COUNTIF", "comparability"])
    b.add("Using the locations file, how many employees work at location 2?", loc2,
          'Import with the | delimiter, then =COUNTIF(B:B,2).', 1, ["import", "COUNTIF"])
    b.add("How many named 2016 employees cannot be matched to the locations file by name?",
          f"{len(unmatched)} — every named 2016 employee has a location" if not unmatched else len(unmatched),
          "=ISNA(XLOOKUP(D2,Locations!A:A,Locations!B:B)) on the distinct 2016 names; check spelling and spaces.", 2.5,
          ["XLOOKUP", "ISNA", "data quality"])
    b.add("In 2016, what was the average pay per hour (Gross_Wages ÷ (Hours + OT_Hours)) at location 1 and at "
          "location 2? (2 decimals)", f"Location 1: {rate['1']:.2f}; location 2: {rate['2']:.2f}",
          "Add Location with XLOOKUP on Employee_Name, then SUMIFS of wages and hours per location and divide.", 3.5,
          ["XLOOKUP", "SUMIF", "comparability"])
    b.add("How many 2016 rows have zero hours and zero gross wages?", zero_rows,
          '=COUNTIFS(E:E,0,G:G,0). Empty rows inflate record counts but not totals.', 1.5, ["COUNTIFS", "data quality"])
    return b.items


def all_questions():
    return nyc() + etl1() + etl2() + etl3() + etl4() + integrateco()
