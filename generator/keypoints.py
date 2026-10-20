"""Key points a spoken answer should contain, for the Examiner mode checklist.

A key point is either {"label", "terms"} (met if the transcript contains any of the terms) or
{"label", "number", "tol"} (met if the transcript mentions a number close to the target).
Matching is on words, not meaning, so the site tells students they can correct the transcript.
"""
import re

# How a student might name each skill out loud.
SKILL_TERMS = {
    "COUNTIF": ["countif", "count if"], "COUNTIFS": ["countifs", "count ifs", "count if"],
    "SUMIF": ["sumif", "sum if"], "AVERAGEIF": ["averageif", "average if"], "MAXIFS": ["maxifs", "max if"],
    "MINIFS": ["minifs", "min if"], "COUNTBLANK": ["countblank", "count blank", "blank"],
    "PivotTable": ["pivot"], "XLOOKUP": ["xlookup", "x lookup", "lookup"], "INDEX/MATCH": ["index", "match", "lookup"],
    "LEFT": ["left"], "RIGHT": ["right"], "MID": ["mid", "middle"], "FIND": ["find", "position of the hyphen"],
    "LEN": ["len", "length"], "VALUE": ["value", "convert to a number"], "IF": ["if"],
    "ISNUMBER": ["isnumber", "is number"], "SUBSTITUTE": ["substitute", "replace"], "UNIQUE": ["unique", "distinct"],
    "TEXT": ["text function", "day name", "dddd"], "WEEKDAY": ["weekday"], "YEAR": ["year"], "MONTH": ["month"],
    "MIN": ["min", "oldest", "earliest", "smallest"], "MAX": ["max", "newest", "latest", "largest"],
    "SUM": ["sum", "total", "add"], "MATCH": ["match"], "ISNA": ["isna", "not found"],
    "concatenation": ["concatenat", "ampersand", "combine"], "array formulas": ["two conditions", "both", "array"],
    "JOIN": ["join"], "GROUP BY": ["group by", "group"], "HAVING": ["having"], "WHERE": ["where", "filter"],
    "ORDER BY": ["order by", "sort"], "LIMIT": ["limit"], "COUNT": ["count"], "DISTINCT": ["distinct", "unique"],
    "LIKE": ["like", "wildcard", "percent sign"], "subqueries": ["subquery", "sub query", "nested", "inner query"],
    "AVG": ["average", "avg", "mean"], "CASE WHEN": ["case"], "BETWEEN": ["between"], "LENGTH": ["length"],
    "strftime": ["strftime", "weekday", "day of the week"], "julianday": ["julian", "difference"],
    "INTERSECT": ["intersect", "both"], "UPPER": ["upper", "capital"], "SUBSTR": ["substr", "first digit", "first character"],
    "modulo": ["modulo", "remainder", "divisible"], "IN": [" in ", "list of"], "NULL": ["null", "empty"],
    "dates": ["date"], "date arithmetic": ["subtract", "difference", "minus", "times 24"],
    "delimiters": ["delimiter", "pipe", "separator"], "text qualifiers": ["quote", "qualifier"],
    "text vs number": ["text", "leading zero"], "duplicates": ["duplicate"], "missing data": ["missing", "blank", "empty", "n/a"],
    "unique identifiers": ["unique", "identifier", " id"], "control totals": ["total", "reconcil", "balance", "check"],
    "internal controls": ["control", "limit", "policy"], "fraud tests": ["fraud", "benford", "duplicate", "round"],
    "returns": ["negative", "return", "refund"], "units of measurement": ["million", "unit", "thousand"],
    "aggregation": ["level", "aggregat"], "comparability": ["definition", "same", "align", "combine"],
    "number formats": ["parenthes", "negative", "minus"], "data quality": ["invalid", "quality", "wrong"],
    "text cleaning": ["clean", "substitute", "trim", "remove the spaces"], "import": ["import", "delimiter", "open"],
    "filtering": ["filter"], "wildcards": ["wildcard", "asterisk", "star"], "percentages": ["percent", "divide"],
    "counting": ["count"], "schema": ["pragma", "table info", "columns"], "aliases": ["alias", " as "],
    "calculated fields": ["multiply", "times", "4.5"], "escaping quotes": ["quote", "apostrophe"],
    "investigation": ["log", "atm", "phone", "flight"], "data types": ["text", "string"],
}

# Words that show the student covered the point behind each follow-up (keyed like followups.SKILL_FOLLOWUPS).
FOLLOWUP_TERMS = {
    "internal controls": ["not prove", "doesn't prove", "does not prove", "exception", "follow up", "follow-up", "investigat", "receipt", "approv"],
    "fraud tests": ["not prove", "doesn't prove", "indicat", "risk", "further", "evidence", "red flag"],
    "unique identifiers": ["combin", "distinct", "unique", "count the rows", "number of rows"],
    "control totals": ["reconcil", "control total", "row count", "tie", "debits equal", "zero"],
    "text vs number": ["leading zero", "becomes 1", "text", "lookup fail", "won't match", "will not match"],
    "delimiters": ["one column", "single column", "delimiter", "pipe"],
    "text qualifiers": ["quote", "qualifier", "pipe"],
    "units of measurement": ["million", "not comparable", "different unit", "wrong total"],
    "duplicates": ["identifier", "id", "all fields", "legitimate", "genuine", "every column"],
    "missing data": ["depends", "why", "document", "reason"],
    "NULL": ["null", "skip", "ignore"],
    "returns": ["negative", "less than zero", "most negative", "minus"],
    "comparability": ["definition", "align", "reg pay", "gross wages", "same way"],
    "aggregation": ["level", "same level", "double count", "aggregat"],
    "HAVING": ["before", "after", "group", "aggregat"],
    "JOIN": ["left join", "keep", "all rows", "null", "match"],
    "subqueries": ["hard cod", "hard-cod", "change", "fragile", "look it up", "find the id"],
    "INDEX/MATCH": ["left", "right", "direction", "column moves", "breaks"],
    "XLOOKUP": ["n/a", "not found", "error", "default"],
    "array formulas": ["business unit", "both", "two conditions", "not unique"],
    "PivotTable": ["fast", "summar", "refresh", "source data", "review"],
    "COUNTIFS": ["condition", "narrow", "population", "outside"],
    "wildcards": ["also match", "cross street", "sample", "anywhere"],
    "LIKE": ["case", "also match", "prime", "kindle", "review"],
    "data types": ["text", "character", "year", "month", "convert"],
    "dates": ["serial", "number of days", "text", "stored"],
    "date arithmetic": ["24", "days", "60", "hours", "minutes"],
    "DISTINCT": ["more than once", "several times", "twice", "duplicate", "double"],
    "GROUP BY": ["one row per", "each row", "per cardholder", "per group", "aggregat"],
    "CASE WHEN": ["boundary", "equal", "greater than or equal", "500", "each side"],
    "MID": ["length", "different", "find", "spot check", "spot-check", "unusual"],
    "FIND": ["hyphen", "moves", "different length", "position"],
    "LEFT": ["fixed", "length", "japan", "us", "different"],
    "import": ["row", "column", "type", "count", "split"],
    "SUMIF": ["grand total", "reconcil", "blank", "misspel", "add up"],
    "COUNTIF": ["space", "trim", "capital", "case"],
    "UNIQUE": ["pivot", "countif", "more than once", "count each"],
    "ORDER BY": ["tie", "arbitrary", "second", "tie-break", "tiebreak"],
    "LIMIT": ["order", "any order", "not guaranteed", "random"],
    "AVG": ["outlier", "median", "skew"],
    "SUM": ["duplicate", "return", "negative", "total row", "unit"],
    "COUNT": ["rows", "people", "person", "transaction", "unit"],
    "WHERE": ["boundary", "equal", "inclusive", "exactly"],
    None: ["check", "total", "count", "recompute", "by hand", "second way", "compare"],
}

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def answer_point(answer):
    """The checklist item for the answer itself: a number if it starts with one, otherwise key words."""
    head = re.split(r" \(| — |; |: ", answer)[0].strip()
    m = NUM.match(head.replace("$", ""))
    if m:
        value = float(m.group().replace(",", ""))
        tol = 0 if value.is_integer() and abs(value) < 1000 else 0.01
        return {"label": f"Gave the answer ({head})", "number": value, "tol": tol, "answer": True,
                "probe": "What number did you actually get?"}
    if len(head) <= 32:
        longest = max(head.lower().split(), key=len)
        terms = [head.lower()] + ([longest] if len(longest) > 3 and longest != head.lower() else [])
    else:
        words = [w.strip(".,'\"").lower() for w in head.split()]
        terms = sorted({w for w in words if len(w) > 5}, key=len, reverse=True)[:3]
    return {"label": f"Gave the answer ({head})", "terms": terms, "answer": True,
            "probe": "So what is your answer, in one sentence?"}


def manipulation_points(q, followup_skill):
    points = [answer_point(q["answer"])]
    named = [s for s in q["skills"] if s in SKILL_TERMS][:2]
    for s in named:
        points.append({"label": f"Explained the method ({s})", "terms": SKILL_TERMS[s],
                       "probe": "Which Excel formula or feature would you use for that, and why?" if q["tool"] == "Excel"
                       else "Which part of the SQL query does that, and why that clause?"})
    fu_terms = FOLLOWUP_TERMS.get(followup_skill, FOLLOWUP_TERMS[None])
    points.append({"label": "Answered the follow-up (see what the examiner listens for)", "terms": fu_terms, "followup": True})
    return points
