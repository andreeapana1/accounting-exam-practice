"""Examiner follow-up questions for Examiner mode.

Each data manipulation question gets the follow-up for its most "examinable" skill; each regression
question gets one by question kind. Every follow-up has the point an examiner listens for.
"""

# Ordered by priority: the first skill a question has that appears here decides its follow-up.
SKILL_FOLLOWUPS = [
    ("internal controls", "Suppose your query flags someone. Does that prove they broke the rules? What would you do next?",
     "A flag is only an indication: there can be approved exceptions. Next step is follow-up testing — check "
     "receipts, approvals or ask the cardholder's supervisor."),
    ("fraud tests", "What can this test tell an auditor, and what can it not tell them?",
     "It points to higher-risk transactions or people; it does not prove fraud. Results need further evidence."),
    ("unique identifiers", "Which field, or combination of fields, uniquely identifies a row here — and how did you check?",
     "Names are not unique; the identifier may need two columns combined. Check by comparing the count of "
     "distinct keys with the number of rows."),
    ("control totals", "How would you convince a reviewer that nothing went wrong in this step?",
     "Reconcile a control total: row counts in and out, or a total that must tie out (e.g. debits = credits)."),
    ("text vs number", "Why does it matter whether the code is stored as text or as a number?",
     "001 as a number becomes 1, so lookups and joins against the text value silently fail."),
    ("delimiters", "What would happen if you just double-clicked the file to open it?",
     "Everything lands in one column because the delimiter is not a comma; you must choose the delimiter when importing."),
    ("text qualifiers", "How should the file have been saved so this problem never happens?",
     "Put text containing the delimiter inside a text qualifier (double quotes), or use a pipe delimiter as the "
     "AICPA Audit Data Standards recommend."),
    ("units of measurement", "If you had not noticed this, what would go wrong in the analysis?",
     "Values in different units (dollars vs millions) are not comparable — totals and ratios would be wildly wrong."),
    ("duplicates", "How do you decide whether a repeated row is a real duplicate or two genuine transactions?",
     "Check a unique identifier or all fields; ask whether two identical transactions could legitimately occur."),
    ("missing data", "What should you do with the missing values — delete them, fill them, or something else?",
     "It depends on why they are missing; document the choice and how it affects the result. Never fill silently."),
    ("NULL", "Why can COUNT of a column give a different answer from COUNT(*)?",
     "COUNT(column) skips NULL values; COUNT(*) counts every row."),
    ("returns", "Returns are stored as negative amounts. How did you make sure your answer treats them correctly?",
     "Filter on Amount < 0 and remember the 'largest' return is the most negative number."),
    ("comparability", "Why can't you simply compare the two years' totals as they come out of the systems?",
     "The systems define and aggregate fields differently; align definitions (Reg_Pay + OT_Pay = Gross_Wages) first."),
    ("aggregation", "At what level is each dataset aggregated, and why does that matter before combining them?",
     "Data must be at the same level (e.g. per employee per job) before joining or comparing, or totals double-count."),
    ("HAVING", "What is the difference between WHERE and HAVING in your query?",
     "WHERE filters rows before grouping; HAVING filters groups after aggregation."),
    ("JOIN", "Which join did you use, and what would change with a LEFT JOIN instead?",
     "An inner join keeps only matches; a left join keeps every row from the left table with NULLs where nothing matches."),
    ("subqueries", "Why did you avoid typing the ID number directly into the query?",
     "Hard-coding values makes the query fragile; a subquery finds the ID from the data, so it still works if IDs change."),
    ("INDEX/MATCH", "Why INDEX/MATCH or XLOOKUP rather than VLOOKUP here?",
     "VLOOKUP only looks to the right and breaks when columns move; INDEX/MATCH and XLOOKUP look in any direction."),
    ("XLOOKUP", "What happens with your formula if the value is not found?",
     "It returns #N/A (or a chosen default); you should check for and explain unmatched rows rather than hide them."),
    ("array formulas", "Why does this lookup need two conditions?",
     "PreparerID is only unique within a business unit, so you must match on both PreparerID and BusinessUnitID."),
    ("PivotTable", "Why a PivotTable rather than formulas — and how would someone else check your work?",
     "PivotTables are fast for summaries; to make it reviewable, keep the source data intact and the pivot refreshable."),
    ("COUNTIFS", "Walk me through each condition in your formula. What would change if you dropped one?",
     "Each condition narrows the rows; dropping one counts records outside the intended population."),
    ("wildcards", "Could your text search pick up records you did not intend? Give an example.",
     "Wildcards match anywhere: '*BROADWAY*' also matches cross streets; check a sample of matches."),
    ("LIKE", "Is your text search case-sensitive, and could it match things you did not mean?",
     "LIKE is case-insensitive for ASCII in SQLite; '%amazon%' also matches AmazonPrime, Kindle etc. — review the vendors."),
    ("data types", "How is this date stored, and how does that affect sorting and filtering?",
     "It is text, so it sorts character by character; use the Year/Month columns or convert to a real date."),
    ("dates", "How does Excel or SQL store a date behind what you see?",
     "Excel stores a serial number of days; SQLite stores dates as text — calculations depend on the real type."),
    ("date arithmetic", "How did you turn the difference between two dates into hours or minutes?",
     "Subtracting dates gives days; multiply by 24 for hours or by 24×60 for minutes."),
    ("DISTINCT", "Why did you need DISTINCT here — what would the number be without it?",
     "Without DISTINCT, a person or album appearing several times is counted several times."),
    ("GROUP BY", "What exactly does each row of your result represent?",
     "One row per group (e.g. per cardholder); every selected column must be grouped or aggregated."),
    ("CASE WHEN", "Talk me through the logic of your CASE expression. What happens at exactly the boundary?",
     "Boundaries must match the rule (>= 500 vs > 500); check one value on each side."),
    ("MID", "Your formula works on the first row. How do you know it works on all of them?",
     "Positions differ between rows when lengths vary; use FIND to locate the hyphen and spot-check unusual rows."),
    ("FIND", "Why did you use FIND instead of a fixed position?",
     "The parts have different lengths, so the hyphen moves; FIND locates it in every row."),
    ("LEFT", "What assumption does LEFT make, and when would it break?",
     "It assumes a fixed number of characters; it breaks when codes have different lengths (e.g. US vs Japan)."),
    ("import", "What is the first thing you check after importing a file?",
     "Row and column counts, that columns split correctly, and that numbers and dates came in as the right type."),
    ("SUMIF", "Your SUMIF gives a total. How would you show the CFO it is complete — that nothing was missed?",
     "Reconcile: the sum over all categories should equal the grand total; check for blanks or misspelled categories."),
    ("COUNTIF", "Would your COUNTIF still be right if some cells had a trailing space or different capitals?",
     "COUNTIF ignores case but not extra spaces; clean the text (TRIM) or check distinct values first."),
    ("UNIQUE", "How would you find out which values are causing duplicates in the first place?",
     "Count each value (PivotTable or COUNTIF) and look at those that appear more than once."),
    ("ORDER BY", "If two rows tie, which one comes first in your result — and does it matter for the answer?",
     "Without a second sort key the order of ties is arbitrary; add a tie-breaker when the position matters."),
    ("LIMIT", "Why is LIMIT without ORDER BY risky?",
     "Without ORDER BY, the database may return rows in any order, so 'the first five' is not guaranteed."),
    ("AVG", "Is the average a good summary here, or would something else describe the data better?",
     "Averages are pulled by outliers and skew; the median or a distribution may be more informative."),
    ("SUM", "What would make this total misleading even if the formula is correct?",
     "Duplicates, returns (negative values), totals rows included in the range, or mixed units."),
    ("COUNT", "What exactly are you counting — rows, people or transactions — and why does it matter?",
     "Rows are not always entities: one person can have many rows, so say which unit you count."),
    ("WHERE", "Is your condition inclusive or exclusive at the boundary — and is that what the question asked?",
     "> versus >= changes the answer for values exactly at the limit; read the control rule carefully."),
]
FALLBACK = ("How would you check that your answer is right before you hand it in?",
            "A sanity check: compare with a total or count, recompute one record by hand, or solve it a second way.")

REGRESSION_FOLLOWUPS = {
    "P": ("Talk me through the calculation. Which terms matter for this group, and which drop out?",
          "Plug in each value; terms multiplied by a dummy of 0 drop out; state the answer in the outcome's unit."),
    "I": ("Now explain the {d} effect to {stakeholder} in one sentence — without the words 'coefficient' or 'dummy'.",
          "Plain words, the unit, the comparison group, and 'all else equal'. No statistical jargon."),
    "S": ("Does 'statistically significant' mean the effect is important for the business?",
          "No — significance says the effect is unlikely to be zero; importance depends on its size in context."),
    "R": ("So what would you tell {stakeholder} instead of just giving that number?",
          "Warn that it is outside the data; offer a prediction within the range, or suggest collecting more data."),
}


def add_followups(questions, regression_exams):
    for q in questions:
        skills = set(q["skills"])
        for skill, ask, listen in SKILL_FOLLOWUPS:
            if skill in skills:
                break
        else:
            ask, listen = FALLBACK
        q["followup"] = {"ask": ask, "listen": listen}
    for ex in regression_exams:
        stakeholder = ex["stakeholder"]
        for q in ex["questions"]:
            ask, listen = REGRESSION_FOLLOWUPS[q["kind"]]
            q["followup"] = {"ask": ask.format(d=ex["d"]["name"].lower(), stakeholder=stakeholder), "listen": listen}
