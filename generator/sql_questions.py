"""SQL questions. Answers come from running the reference query on the downloadable database."""
import shutil
import sqlite3

from common import FILES, SQL, Bank, money, num

CS50 = SQL / "Part 1" / "cs50 assignment"


# ------------------------------------------------------------- database files
def build_databases():
    """Copy the small databases and build practice subsets of the two large ones."""
    FILES.mkdir(parents=True, exist_ok=True)
    shutil.copy(SQL / "Part 1" / "pwc assignment" / "Chinook_Sqlite.sqlite", FILES / "Chinook_Sqlite.sqlite")
    shutil.copy(CS50 / "songs" / "songs.db", FILES / "songs.db")
    shutil.copy(CS50 / "mystery" / "fiftyville.db", FILES / "fiftyville.db")

    # P-cards: calendar year 2014 only (the year the internal-audit tasks use).
    out = FILES / "pcards_2014.db"
    out.unlink(missing_ok=True)
    con = sqlite3.connect(out)
    con.execute("ATTACH DATABASE ? AS src", (str(SQL / "part 2" / "pcards.db"),))
    con.execute("CREATE TABLE pcards AS SELECT * FROM src.pcards WHERE Year = 2014")
    con.commit()
    con.execute("DETACH DATABASE src")
    con.execute("VACUUM")
    con.close()

    # Movies: keep films with at least 5,000 IMDb votes, plus everyone who starred in or directed them.
    out = FILES / "movies_subset.db"
    out.unlink(missing_ok=True)
    con = sqlite3.connect(out)
    con.execute("ATTACH DATABASE ? AS src", (str(CS50 / "movies" / "movies.db"),))
    con.executescript("""
        CREATE TABLE movies (id INTEGER, title TEXT NOT NULL, year NUMERIC, PRIMARY KEY(id));
        CREATE TABLE people (id INTEGER, name TEXT NOT NULL, birth NUMERIC, PRIMARY KEY(id));
        CREATE TABLE stars (movie_id INTEGER NOT NULL, person_id INTEGER NOT NULL);
        CREATE TABLE directors (movie_id INTEGER NOT NULL, person_id INTEGER NOT NULL);
        CREATE TABLE ratings (movie_id INTEGER NOT NULL, rating REAL NOT NULL, votes INTEGER NOT NULL);
        CREATE TEMP TABLE keep AS SELECT movie_id FROM src.ratings WHERE votes >= 5000;
        INSERT INTO movies SELECT * FROM src.movies WHERE id IN (SELECT movie_id FROM keep);
        INSERT INTO ratings SELECT * FROM src.ratings WHERE movie_id IN (SELECT movie_id FROM keep);
        INSERT INTO stars SELECT * FROM src.stars WHERE movie_id IN (SELECT movie_id FROM keep);
        INSERT INTO directors SELECT * FROM src.directors WHERE movie_id IN (SELECT movie_id FROM keep);
        INSERT INTO people SELECT * FROM src.people WHERE id IN
            (SELECT person_id FROM stars UNION SELECT person_id FROM directors);
    """)
    con.commit()
    con.execute("DETACH DATABASE src")
    con.execute("VACUUM")
    con.close()


# ------------------------------------------------------------------- helpers
class SqlBank(Bank):
    def __init__(self, dataset, file):
        super().__init__(dataset, "SQL")
        self.con = sqlite3.connect(FILES / file)

    def rows(self, sql):
        return self.con.execute(sql).fetchall()

    def ask(self, prompt, sql, fmt=None, minutes=1.5, skills=(), expect=None):
        """Run the reference query; fmt turns the result rows into the displayed answer."""
        rows = self.rows(sql)
        if fmt is None:
            fmt = auto_format
        answer = fmt(rows)
        if expect is not None:
            assert str(answer) == str(expect), (prompt, answer, expect)
        self.add(prompt, answer, sql, minutes, skills)
        return rows


def auto_format(rows):
    if len(rows) == 1 and len(rows[0]) == 1:
        v = rows[0][0]
        if isinstance(v, int):
            return num(v)
        return f"{v:,}" if isinstance(v, float) else v
    first = ", ".join(str(c) for c in rows[0]) if rows else "—"
    return f"{len(rows)} rows; first row: {first}"


def count_and_first(rows):
    return f"{len(rows)} rows; first: {rows[0][0]}" if rows else "0 rows"


def joined(rows):
    return ", ".join(str(r[0]) for r in rows)


# ------------------------------------------------------------------- Chinook
def chinook():
    b = SqlBank("chinook", "Chinook_Sqlite.sqlite")
    b.add("How many columns does the Customer table have?", len(b.rows("PRAGMA table_info(Customer)")),
          "PRAGMA table_info(Customer);\n-- or: SELECT * FROM Customer LIMIT 1; and count the columns", 1, ["schema"])
    b.ask("If you select only the first 5 rows of Customer, what is the Country in the last row?",
          "SELECT Country FROM Customer LIMIT 1 OFFSET 4;", minutes=1, skills=["LIMIT"], expect="Czech Republic")
    b.ask("If you sort Customer by LastName, what is the last name in the third row?",
          "SELECT LastName FROM Customer ORDER BY LastName LIMIT 1 OFFSET 2;", minutes=1,
          skills=["ORDER BY", "LIMIT"], expect="Bernard")
    b.ask("How many rows are in the Invoice table?", "SELECT COUNT(*) FROM Invoice;", minutes=0.5,
          skills=["COUNT"], expect=412)
    b.ask("How many invoices have totals greater than $20?", "SELECT COUNT(*) FROM Invoice WHERE Total > 20;",
          minutes=1, skills=["WHERE"], expect=4)
    b.ask("How many invoices have totals greater than $10 and less than $20?",
          "SELECT COUNT(*) FROM Invoice WHERE Total > 10 AND Total < 20;", minutes=1, skills=["WHERE", "AND"],
          expect=60)
    b.ask("How many invoices are from customers in Brazil, Argentina or Chile?",
          "SELECT COUNT(*)\nFROM Invoice i JOIN Customer c ON c.CustomerId = i.CustomerId\n"
          "WHERE c.Country IN ('Brazil', 'Argentina', 'Chile');", minutes=1.5, skills=["JOIN", "IN"], expect=49)
    b.ask("How many invoices have a billing country that starts with “C”?",
          "SELECT COUNT(*) FROM Invoice WHERE BillingCountry LIKE 'C%';", minutes=1, skills=["LIKE"], expect=77)
    b.ask("How many customers list their company?", "SELECT COUNT(Company) FROM Customer;", minutes=1,
          skills=["COUNT", "NULL"], expect=10)
    b.ask("How many employees does Chinook have?", "SELECT COUNT(*) FROM Employee;", minutes=0.5,
          skills=["COUNT"], expect=8)
    b.ask("How long is the longest employee last name?", "SELECT MAX(LENGTH(LastName)) FROM Employee;",
          minutes=1, skills=["LENGTH", "MAX"], expect=8)
    b.ask("How many employees were born on a Sunday?",
          "SELECT COUNT(*) FROM Employee WHERE strftime('%w', BirthDate) = '0';", minutes=2,
          skills=["dates", "strftime"], expect=2)
    b.ask("How old was the oldest employee when they were hired? (years, 1 decimal)",
          "SELECT ROUND(MAX((julianday(HireDate) - julianday(BirthDate)) / 365.25), 1) FROM Employee;",
          fmt=lambda r: f"{r[0][0]} years (about 55.5, depending on how you count a year)", minutes=2.5, skills=["dates", "julianday"])
    b.ask("Which billing country has the highest total invoice value, and how much is it?",
          "SELECT BillingCountry, ROUND(SUM(Total), 2) AS TotalValue\nFROM Invoice\nGROUP BY BillingCountry\n"
          "ORDER BY TotalValue DESC\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} ({money(r[0][1])})", minutes=2,
          skills=["GROUP BY", "SUM", "ORDER BY"])
    b.ask("How many invoice line items are there?", "SELECT COUNT(*) FROM InvoiceLine;", minutes=0.5,
          skills=["COUNT"], expect="2,240")
    b.ask("How many distinct unit prices are there in InvoiceLine?",
          "SELECT COUNT(DISTINCT UnitPrice) FROM InvoiceLine;", minutes=1, skills=["DISTINCT"], expect=2)
    b.ask("How many downloads (invoice lines) happened at each price? Give the count for $0.99.",
          "SELECT UnitPrice, COUNT(*) AS Downloads\nFROM InvoiceLine\nGROUP BY UnitPrice;",
          fmt=lambda r: "; ".join(f"${p}: {num(n)}" for p, n in r), minutes=1.5, skills=["GROUP BY"])
    b.ask("What is the range of invoice dates in the database (first and last date)?",
          "SELECT MIN(InvoiceDate), MAX(InvoiceDate) FROM Invoice;",
          fmt=lambda r: f"{r[0][0][:10]} to {r[0][1][:10]} (about 5 years)", minutes=1, skills=["MIN", "MAX"])
    b.ask("What is the maximum number of times any single track has been downloaded, and how many tracks share it?",
          "SELECT Downloads, COUNT(*) AS Tracks FROM (\n  SELECT TrackId, COUNT(*) AS Downloads\n"
          "  FROM InvoiceLine GROUP BY TrackId\n)\nGROUP BY Downloads\nORDER BY Downloads DESC\nLIMIT 1;",
          fmt=lambda r: f"{r[0][0]} downloads, shared by {r[0][1]} tracks", minutes=3,
          skills=["subqueries", "GROUP BY"])
    b.ask("What is the most popular genre by number of tracks sold?",
          "SELECT g.Name, COUNT(*) AS Sold\nFROM InvoiceLine il\nJOIN Track t ON t.TrackId = il.TrackId\n"
          "JOIN Genre g ON g.GenreId = t.GenreId\nGROUP BY g.Name\nORDER BY Sold DESC\nLIMIT 1;",
          fmt=lambda r: f"{r[0][0]} ({num(r[0][1])} tracks sold)", minutes=2.5, skills=["JOIN", "GROUP BY"])
    b.ask("How many distinct albums have at least one track that was downloaded?",
          "SELECT COUNT(DISTINCT t.AlbumId)\nFROM InvoiceLine il JOIN Track t ON t.TrackId = il.TrackId;",
          minutes=2, skills=["JOIN", "DISTINCT"])
    b.ask("Which customer has spent the most in total? Give the full name and amount.",
          "SELECT c.FirstName || ' ' || c.LastName AS Customer, ROUND(SUM(i.Total), 2) AS Spent\n"
          "FROM Invoice i JOIN Customer c ON c.CustomerId = i.CustomerId\nGROUP BY c.CustomerId\n"
          "ORDER BY Spent DESC\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} ({money(r[0][1])})", minutes=2.5,
          skills=["JOIN", "GROUP BY", "concatenation"])
    return b.items


# --------------------------------------------------------------------- songs
def songs():
    b = SqlBank("songs", "songs.db")
    b.ask("List the names of all songs in decreasing order of tempo. Which song is first?",
          "SELECT name FROM songs ORDER BY tempo DESC;", fmt=count_and_first, minutes=1, skills=["ORDER BY"])
    b.ask("List the names of the top 3 longest songs, longest first.",
          "SELECT name FROM songs ORDER BY duration_ms DESC LIMIT 3;", fmt=joined, minutes=1,
          skills=["ORDER BY", "LIMIT"])
    b.ask("How many songs have danceability, energy and valence all greater than 0.6?",
          "SELECT COUNT(*) FROM songs\nWHERE danceability > 0.6 AND energy > 0.6 AND valence > 0.6;",
          minutes=1, skills=["WHERE", "AND"])
    b.ask("What is the average tempo of all songs? (2 decimals)", "SELECT ROUND(AVG(tempo), 2) FROM songs;",
          minutes=1, skills=["AVG"])
    b.ask("How many songs are by Drake? (Do not assume Drake's artist_id.)",
          "SELECT COUNT(*) FROM songs\nWHERE artist_id = (SELECT id FROM artists WHERE name = 'Drake');",
          minutes=1.5, skills=["subqueries"])
    b.ask("What is the average energy of songs by Post Malone? (3 decimals)",
          "SELECT ROUND(AVG(energy), 3)\nFROM songs s JOIN artists a ON a.id = s.artist_id\nWHERE a.name = 'Post Malone';",
          minutes=1.5, skills=["JOIN", "AVG"])
    b.ask("How many songs feature other artists (the name contains “feat.”)?",
          "SELECT COUNT(*) FROM songs WHERE name LIKE '%feat.%';", minutes=1, skills=["LIKE"])
    b.ask("Which artist has the most songs in the database?",
          "SELECT a.name, COUNT(*) AS n\nFROM songs s JOIN artists a ON a.id = s.artist_id\n"
          "GROUP BY a.name ORDER BY n DESC LIMIT 1;", fmt=lambda r: f"{r[0][0]} ({r[0][1]} songs)", minutes=2,
          skills=["JOIN", "GROUP BY"])
    return b.items


# -------------------------------------------------------------------- movies
def movies():
    b = SqlBank("movies", "movies_subset.db")
    b.ask("How many movies in the database were released in 2007?",
          "SELECT COUNT(*) FROM movies WHERE year = 2007;", minutes=0.5, skills=["WHERE"])
    b.ask("What is Johnny Depp's birth year?", "SELECT birth FROM people WHERE name = 'Johnny Depp';",
          fmt=lambda r: str(r[0][0]), minutes=0.5, skills=["WHERE"])
    b.ask("List the titles of all movies released in 2017 or later, alphabetically. How many are there, and which is first?",
          "SELECT title FROM movies WHERE year >= 2017 ORDER BY title;", fmt=count_and_first, minutes=1.5,
          skills=["WHERE", "ORDER BY"])
    b.ask("How many movies have an IMDb rating greater than 9.0?",
          "SELECT COUNT(*) FROM ratings WHERE rating > 9.0;", minutes=0.5, skills=["WHERE"])
    b.ask("List all Toy Story movies in chronological order with their release year.",
          "SELECT title, year FROM movies WHERE title LIKE 'Toy Story%' ORDER BY year;",
          fmt=lambda r: "; ".join(f"{t} ({y})" for t, y in r), minutes=1.5, skills=["LIKE", "ORDER BY"])
    b.ask("What is the average rating of all movies released in 2013? (2 decimals)",
          "SELECT ROUND(AVG(rating), 2)\nFROM ratings r JOIN movies m ON m.id = r.movie_id\nWHERE m.year = 2013;",
          minutes=1.5, skills=["JOIN", "AVG"])
    b.ask("List all 2011 movies with their ratings, highest rating first (ties alphabetically). Which movie is first?",
          "SELECT m.title, r.rating\nFROM movies m JOIN ratings r ON r.movie_id = m.id\nWHERE m.year = 2011\n"
          "ORDER BY r.rating DESC, m.title;", fmt=lambda r: f"{len(r)} rows; first: {r[0][0]} ({r[0][1]})",
          minutes=2, skills=["JOIN", "ORDER BY"])
    b.ask("How many people starred in Harry Potter and the Sorcerer's Stone?",
          "SELECT COUNT(*) FROM stars\nWHERE movie_id = (SELECT id FROM movies\n"
          "                  WHERE title = 'Harry Potter and the Sorcerer''s Stone');", minutes=1.5,
          skills=["subqueries", "escaping quotes"])
    b.ask("How many different people starred in a movie released in 2003? (Count each person once.)",
          "SELECT COUNT(DISTINCT s.person_id)\nFROM stars s JOIN movies m ON m.id = s.movie_id\nWHERE m.year = 2003;",
          minutes=2, skills=["JOIN", "DISTINCT"])
    b.ask("How many different people have directed a movie with a rating of at least 8.0?",
          "SELECT COUNT(DISTINCT d.person_id)\nFROM directors d JOIN ratings r ON r.movie_id = d.movie_id\n"
          "WHERE r.rating >= 8.0;", minutes=2, skills=["JOIN", "DISTINCT"])
    b.ask("List the five highest-rated movies starring Helena Bonham Carter, highest first.",
          "SELECT m.title\nFROM movies m\nJOIN stars s ON s.movie_id = m.id\nJOIN people p ON p.id = s.person_id\n"
          "JOIN ratings r ON r.movie_id = m.id\nWHERE p.name = 'Helena Bonham Carter'\nORDER BY r.rating DESC\nLIMIT 5;",
          fmt=joined, minutes=2.5, skills=["JOIN", "ORDER BY", "LIMIT"])
    b.ask("List the titles of all movies in which both Johnny Depp and Helena Bonham Carter starred.",
          "SELECT title FROM movies WHERE id IN (\n  SELECT movie_id FROM stars JOIN people ON people.id = person_id\n"
          "  WHERE name = 'Johnny Depp'\n  INTERSECT\n  SELECT movie_id FROM stars JOIN people ON people.id = person_id\n"
          "  WHERE name = 'Helena Bonham Carter'\n) ORDER BY title;", fmt=joined, minutes=3,
          skills=["subqueries", "INTERSECT"])
    b.ask("How many different people starred in a movie with Kevin Bacon (born 1958), excluding Kevin Bacon himself?",
          "SELECT COUNT(DISTINCT person_id) FROM stars\nWHERE movie_id IN (\n  SELECT movie_id FROM stars\n"
          "  WHERE person_id = (SELECT id FROM people WHERE name = 'Kevin Bacon' AND birth = 1958)\n)\n"
          "AND person_id <> (SELECT id FROM people WHERE name = 'Kevin Bacon' AND birth = 1958);",
          minutes=3, skills=["subqueries"])
    return b.items


# ---------------------------------------------------------------- Fiftyville
def fiftyville():
    b = SqlBank("fiftyville", "fiftyville.db")
    thief_sql = """SELECT p.name
FROM people p
WHERE p.license_plate IN (
    SELECT license_plate FROM courthouse_security_logs
    WHERE year = 2020 AND month = 7 AND day = 28 AND hour = 10
      AND minute BETWEEN 15 AND 25 AND activity = 'exit')
  AND p.id IN (
    SELECT person_id FROM bank_accounts WHERE account_number IN (
        SELECT account_number FROM atm_transactions
        WHERE year = 2020 AND month = 7 AND day = 28
          AND atm_location = 'Fifer Street' AND transaction_type = 'withdraw'))
  AND p.phone_number IN (
    SELECT caller FROM phone_calls
    WHERE year = 2020 AND month = 7 AND day = 28 AND duration < 60)
  AND p.passport_number IN (
    SELECT passport_number FROM passengers WHERE flight_id = (
        SELECT id FROM flights
        WHERE year = 2020 AND month = 7 AND day = 29
          AND origin_airport_id = (SELECT id FROM airports WHERE city = 'Fiftyville')
        ORDER BY hour, minute LIMIT 1));"""
    b.ask("Start with the crime scene report for July 28, 2020 on Chamberlin Street. At what time and where did the theft happen?",
          "SELECT description FROM crime_scene_reports\nWHERE year = 2020 AND month = 7 AND day = 28\n"
          "  AND street = 'Chamberlin Street';", fmt=lambda r: "10:15am at the Chamberlin Street courthouse",
          minutes=1.5, skills=["WHERE"])
    rows = b.ask("Use the witness interviews, courthouse logs, ATM withdrawals, phone calls and the first flight out the "
                 "next morning. Who is the thief?", thief_sql, minutes=6, skills=["subqueries", "IN", "investigation"])
    thief = rows[0][0]
    b.ask("Which city did the thief escape to?",
          "SELECT a.city FROM flights f JOIN airports a ON a.id = f.destination_airport_id\n"
          "WHERE f.year = 2020 AND f.month = 7 AND f.day = 29\n"
          "  AND f.origin_airport_id = (SELECT id FROM airports WHERE city = 'Fiftyville')\n"
          "ORDER BY f.hour, f.minute LIMIT 1;", minutes=2, skills=["JOIN", "ORDER BY"])
    b.ask("Who is the accomplice (the person the thief called for less than a minute)?",
          f"SELECT name FROM people WHERE phone_number = (\n  SELECT receiver FROM phone_calls\n"
          f"  WHERE year = 2020 AND month = 7 AND day = 28 AND duration < 60\n"
          f"    AND caller = (SELECT phone_number FROM people WHERE name = '{thief}'));", minutes=2,
          skills=["subqueries"])
    return b.items


# -------------------------------------------------------------------- P-cards
def pcards():
    b = SqlBank("pcards", "pcards_2014.db")
    b.ask("What is the total number of P-card transactions in the database? Label the column TotalTrans.",
          "SELECT COUNT(*) AS TotalTrans FROM pcards;", minutes=0.5, skills=["COUNT", "aliases"])
    b.ask("How many transactions are for $5,000 or more? Label the column TotalTransGT5k.",
          "SELECT COUNT(*) AS TotalTransGT5k FROM pcards WHERE Amount >= 5000;", minutes=1, skills=["WHERE"])
    b.ask("What is the total dollar amount of returns (negative amounts) from January to March 2014?",
          "SELECT ROUND(SUM(Amount), 2) AS TotalReturns2014Q1\nFROM pcards\nWHERE Amount < 0 AND Month BETWEEN 1 AND 3;",
          fmt=lambda r: money(r[0][0]), minutes=1.5, skills=["SUM", "BETWEEN", "returns"])
    b.ask("Which cardholder had the most transactions in 2014, and how many?",
          "SELECT FullName, COUNT(*) AS NumTrans\nFROM pcards\nGROUP BY FullName\nORDER BY NumTrans DESC\nLIMIT 1;",
          fmt=lambda r: f"{r[0][0]} ({num(r[0][1])})", minutes=1.5, skills=["GROUP BY", "ORDER BY"])
    b.ask("How many cardholders had more than 10 transactions in 2014?",
          "SELECT COUNT(*) FROM (\n  SELECT FullName FROM pcards\n  GROUP BY FullName\n  HAVING COUNT(*) > 10\n);",
          minutes=2, skills=["GROUP BY", "HAVING"])
    b.ask("Who returned the greatest dollar amount of goods in 2014? Give the name and the returned value.",
          "SELECT FullName, ROUND(SUM(Amount), 2) AS ReturnedGoodsValue, COUNT(*) AS ReturnedGoodsCount\n"
          "FROM pcards\nWHERE Amount < 0\nGROUP BY FullName\nORDER BY ReturnedGoodsValue\nLIMIT 1;",
          fmt=lambda r: f"{r[0][0]} ({money(r[0][1])}, {r[0][2]} returns)", minutes=2.5,
          skills=["GROUP BY", "returns", "ORDER BY"])
    b.ask("How many 2014 transactions over $3,000 came from a vendor with Amazon somewhere in the name?",
          "SELECT COUNT(*) FROM pcards\nWHERE Vendor LIKE '%amazon%' AND Amount > 3000;", minutes=1.5,
          skills=["LIKE", "WHERE"])
    b.ask("If OSU had to pay 4.5% state sales tax on all 2014 P-card purchases, how much sales tax did it save?",
          "SELECT ROUND(SUM(Amount) * 0.045, 2) AS SalesTaxSaved FROM pcards;", fmt=lambda r: money(r[0][0]),
          minutes=1.5, skills=["calculated fields"])
    b.ask("OSU would earn 0.75% on Amazon.com transactions of $500 or more and 0.50% on smaller ones (vendor exactly "
          "'Amazon.com', any capitalisation). What would OSU have earned in 2014?",
          "SELECT ROUND(SUM(CASE WHEN Amount >= 500 THEN Amount * 0.0075\n"
          "                      ELSE Amount * 0.005 END), 2) AS AmazonEarnings\nFROM pcards\n"
          "WHERE UPPER(Vendor) = 'AMAZON.COM';", fmt=lambda r: money(r[0][0]), minutes=2.5,
          skills=["CASE WHEN", "UPPER"])
    b.ask("What is the average transaction amount in 2014? (2 decimals)", "SELECT ROUND(AVG(Amount), 2) FROM pcards;",
          fmt=lambda r: money(r[0][0]), minutes=0.5, skills=["AVG"])
    b.ask("Control test: which employees spent more than $50,000 in 2014? How many are there, and who spent the most?",
          "SELECT FullName, ROUND(SUM(Amount), 2) AS TotalSpent\nFROM pcards\nGROUP BY FullName\n"
          "HAVING SUM(Amount) > 50000\nORDER BY TotalSpent DESC;",
          fmt=lambda r: f"{len(r)} employees; highest: {r[0][0]} ({money(r[0][1])})", minutes=2,
          skills=["GROUP BY", "HAVING", "internal controls"])
    b.ask("Control test: how many employee-months in 2014 exceeded $10,000 of spending?",
          "SELECT COUNT(*) FROM (\n  SELECT FullName, Month FROM pcards\n  GROUP BY FullName, Month\n"
          "  HAVING SUM(Amount) > 10000\n);", minutes=2.5, skills=["GROUP BY", "HAVING", "internal controls"])
    b.ask("Control test: how many single transactions in 2014 were for more than $5,000?",
          "SELECT COUNT(*) FROM pcards WHERE Amount > 5000;", minutes=1, skills=["WHERE", "internal controls"])
    b.ask("Split purchases: how many cases are there where the same cardholder made more than one purchase from the "
          "same vendor on the same day and the combined total was more than $5,000?",
          "SELECT COUNT(*) FROM (\n  SELECT FullName, Vendor, TransactionDate\n  FROM pcards\n"
          "  GROUP BY FullName, Vendor, TransactionDate\n  HAVING COUNT(*) > 1 AND SUM(Amount) > 5000\n);",
          minutes=3, skills=["GROUP BY", "HAVING", "internal controls"])
    b.ask("Benford's law: what percentage of 2014 transactions of $1.00 or more start with the digit 1? (3 decimals)",
          "SELECT ROUND(100.0 * SUM(CASE WHEN SUBSTR(CAST(Amount AS TEXT), 1, 1) = '1' THEN 1 ELSE 0 END)\n"
          "             / COUNT(*), 3) AS PctDigit1\nFROM pcards\nWHERE Amount >= 1;",
          fmt=lambda r: f"{r[0][0]}% (Benford expects 30.103%)", minutes=3, skills=["SUBSTR", "CASE WHEN", "fraud tests"])
    b.ask("Duplicate payments: how many groups of charges have the same date, vendor, cardholder and amount "
          "(excluding returns)?",
          "SELECT COUNT(*) FROM (\n  SELECT TransactionDate, Vendor, FullName, Amount\n  FROM pcards\n  WHERE Amount > 0\n"
          "  GROUP BY TransactionDate, Vendor, FullName, Amount\n  HAVING COUNT(*) > 1\n);", minutes=3,
          skills=["GROUP BY", "HAVING", "fraud tests"])
    b.ask("Round-number test: how many 2014 transactions are four-digit whole amounts ending in 000 (e.g. 2000.00)?",
          "SELECT COUNT(*) FROM pcards\nWHERE Amount BETWEEN 1000 AND 9999 AND Amount % 1000 = 0;", minutes=2,
          skills=["modulo", "fraud tests"])
    b.ask("Which merchant category (MCC) had the highest total spending in 2014?",
          "SELECT MCC, ROUND(SUM(Amount), 2) AS Spent\nFROM pcards\nGROUP BY MCC\nORDER BY Spent DESC\nLIMIT 1;",
          fmt=lambda r: f"{r[0][0]} ({money(r[0][1])})", minutes=1.5, skills=["GROUP BY"])
    b.ask("TransactionDate is stored as text like '7/26/2014 0:00:00'. If you sort by TransactionDate descending, "
          "which value comes first, and why is this misleading?",
          "SELECT TransactionDate FROM pcards ORDER BY TransactionDate DESC LIMIT 1;",
          fmt=lambda r: f"{r[0][0]} — text sorts character by character, so '9/…' comes after '12/…'; "
                        "the real last date is in December. Sort by Year, Month and the day instead", minutes=2, skills=["dates", "data types"])
    b.ask("Which month of 2014 had the highest total spending?",
          "SELECT Month, ROUND(SUM(Amount), 2) AS Spent\nFROM pcards\nGROUP BY Month\nORDER BY Spent DESC\nLIMIT 1;",
          fmt=lambda r: f"Month {r[0][0]} ({money(r[0][1])})", minutes=1.5, skills=["GROUP BY"])
    return b.items


def all_questions():
    build_databases()
    return chinook() + songs() + movies() + fiftyville() + pcards()
