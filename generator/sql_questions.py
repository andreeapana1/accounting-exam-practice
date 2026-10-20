"""SQL questions. Answers come from running the reference query on the downloadable database.

The questions are new: they use the course databases but do not repeat the case assignments or the
questions on the reference practice site.
"""
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
    b.ask("Who does Jane Peacock report to? Give the manager's full name and title.",
          "SELECT m.FirstName || ' ' || m.LastName, m.Title\nFROM Employee e\nJOIN Employee m ON m.EmployeeId = e.ReportsTo\n"
          "WHERE e.FirstName = 'Jane' AND e.LastName = 'Peacock';", fmt=lambda r: f"{r[0][0]} ({r[0][1]})", minutes=2,
          skills=["JOIN", "self join"])
    b.ask("Which sales support agent looks after the customers with the highest total invoice value?",
          "SELECT e.FirstName || ' ' || e.LastName AS Agent, ROUND(SUM(i.Total), 2) AS Sales\nFROM Employee e\n"
          "JOIN Customer c ON c.SupportRepId = e.EmployeeId\nJOIN Invoice i ON i.CustomerId = c.CustomerId\n"
          "GROUP BY e.EmployeeId\nORDER BY Sales DESC\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} ({money(r[0][1])})",
          minutes=3, skills=["JOIN", "GROUP BY"])
    b.ask("Control check: for how many invoices does Total differ from the sum of UnitPrice × Quantity on its lines?",
          "SELECT COUNT(*) FROM (\n  SELECT i.InvoiceId\n  FROM Invoice i JOIN InvoiceLine l ON l.InvoiceId = i.InvoiceId\n"
          "  GROUP BY i.InvoiceId\n  HAVING ABS(i.Total - SUM(l.UnitPrice * l.Quantity)) > 0.005\n);",
          fmt=lambda r: f"{r[0][0]} — every invoice total reconciles to its lines" if r[0][0] == 0 else num(r[0][0]),
          minutes=3, skills=["control totals", "JOIN", "HAVING"])
    b.ask("How many tracks have never been sold?",
          "SELECT COUNT(*)\nFROM Track t\nLEFT JOIN InvoiceLine l ON l.TrackId = t.TrackId\nWHERE l.InvoiceLineId IS NULL;",
          minutes=2, skills=["JOIN", "NULL"])
    b.ask("Which media type has the most tracks?",
          "SELECT m.Name, COUNT(*) AS Tracks\nFROM Track t JOIN MediaType m ON m.MediaTypeId = t.MediaTypeId\n"
          "GROUP BY m.Name\nORDER BY Tracks DESC\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} ({num(r[0][1])} tracks)",
          minutes=1.5, skills=["JOIN", "GROUP BY"])
    b.ask("Which playlist contains the most tracks?",
          "SELECT p.Name, COUNT(*) AS Tracks\nFROM PlaylistTrack pt JOIN Playlist p ON p.PlaylistId = pt.PlaylistId\n"
          "GROUP BY p.PlaylistId\nORDER BY Tracks DESC\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} ({num(r[0][1])} tracks)",
          minutes=1.5, skills=["JOIN", "GROUP BY"])
    b.ask("Which artist has the most albums in the store?",
          "SELECT ar.Name, COUNT(*) AS Albums\nFROM Album al JOIN Artist ar ON ar.ArtistId = al.ArtistId\n"
          "GROUP BY ar.ArtistId\nORDER BY Albums DESC\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} ({r[0][1]} albums)",
          minutes=1.5, skills=["JOIN", "GROUP BY"])
    b.ask("Which calendar year had the highest total invoice value?",
          "SELECT strftime('%Y', InvoiceDate) AS Year, ROUND(SUM(Total), 2) AS Revenue\nFROM Invoice\nGROUP BY Year\n"
          "ORDER BY Revenue DESC\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} ({money(r[0][1])})", minutes=2,
          skills=["strftime", "dates", "GROUP BY"])
    b.ask("How many tracks are longer than 10 minutes?", "SELECT COUNT(*) FROM Track WHERE Milliseconds > 10 * 60 * 1000;",
          minutes=1.5, skills=["WHERE", "units of measurement"])
    b.ask("Ignoring tracks without a composer, which composer has the most tracks?",
          "SELECT Composer, COUNT(*) AS Tracks\nFROM Track\nWHERE Composer IS NOT NULL\nGROUP BY Composer\n"
          "ORDER BY Tracks DESC\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} ({r[0][1]} tracks)", minutes=1.5,
          skills=["NULL", "GROUP BY"])
    b.ask("How many tracks have no composer recorded?", "SELECT COUNT(*) FROM Track WHERE Composer IS NULL;",
          minutes=1, skills=["NULL", "missing data"])
    b.ask("How many cities have more than one customer?",
          "SELECT COUNT(*) FROM (\n  SELECT City FROM Customer\n  GROUP BY City\n  HAVING COUNT(*) > 1\n);",
          minutes=1.5, skills=["GROUP BY", "HAVING"])
    b.ask("How many customers have no support representative assigned?",
          "SELECT COUNT(*) FROM Customer WHERE SupportRepId IS NULL;",
          fmt=lambda r: f"{r[0][0]} — every customer has a representative" if r[0][0] == 0 else num(r[0][0]),
          minutes=1, skills=["NULL", "WHERE"])
    b.ask("What is the average number of lines per invoice? (2 decimals)",
          "SELECT ROUND(1.0 * COUNT(*) / COUNT(DISTINCT InvoiceId), 2) FROM InvoiceLine;", minutes=1.5,
          skills=["COUNT", "DISTINCT"])
    b.ask("Which employee was hired first, and on what date?",
          "SELECT FirstName || ' ' || LastName, HireDate FROM Employee ORDER BY HireDate LIMIT 1;",
          fmt=lambda r: f"{r[0][0]} ({r[0][1][:10]})", minutes=1, skills=["ORDER BY", "dates"])
    return b.items


# --------------------------------------------------------------------- songs
def songs():
    b = SqlBank("songs", "songs.db")
    b.ask("Which song is the loudest (loudness closest to 0 dB)?",
          "SELECT name, loudness FROM songs ORDER BY loudness DESC LIMIT 1;",
          fmt=lambda r: f"{r[0][0]} ({r[0][1]} dB)", minutes=1, skills=["ORDER BY", "LIMIT"])
    b.ask("Which musical key (0–11) is used by the most songs?",
          "SELECT key, COUNT(*) AS n FROM songs GROUP BY key ORDER BY n DESC LIMIT 1;",
          fmt=lambda r: f"Key {r[0][0]} ({r[0][1]} songs)", minutes=1.5, skills=["GROUP BY"])
    b.ask("duration_ms is in milliseconds. How many songs are longer than four minutes?",
          "SELECT COUNT(*) FROM songs WHERE duration_ms > 4 * 60 * 1000;", minutes=1.5,
          skills=["WHERE", "units of measurement"])
    b.ask("What is the total running time of all songs, in minutes? (1 decimal)",
          "SELECT ROUND(SUM(duration_ms) / 60000.0, 1) FROM songs;", minutes=1.5, skills=["SUM", "units of measurement"])
    b.ask("How many artists in the artists table have no songs in the songs table?",
          "SELECT COUNT(*)\nFROM artists a\nLEFT JOIN songs s ON s.artist_id = a.id\nWHERE s.id IS NULL;",
          fmt=lambda r: f"{r[0][0]} — every artist has at least one song" if r[0][0] == 0 else num(r[0][0]),
          minutes=2, skills=["JOIN", "NULL"])
    b.ask("Which song has the biggest gap between its energy and its valence?",
          "SELECT name, ROUND(ABS(energy - valence), 3) AS gap\nFROM songs\nORDER BY gap DESC\nLIMIT 1;",
          fmt=lambda r: f"{r[0][0]} (gap {r[0][1]})", minutes=2, skills=["calculated fields", "ORDER BY"])
    b.ask("What is the energy of the 10th most danceable song?",
          "SELECT energy FROM songs ORDER BY danceability DESC LIMIT 1 OFFSET 9;", minutes=1.5,
          skills=["ORDER BY", "LIMIT"])
    b.ask("Which artist has the most songs in the database?",
          "SELECT a.name, COUNT(*) AS n\nFROM songs s JOIN artists a ON a.id = s.artist_id\n"
          "GROUP BY a.name ORDER BY n DESC LIMIT 1;", fmt=lambda r: f"{r[0][0]} ({r[0][1]} songs)", minutes=2,
          skills=["JOIN", "GROUP BY"])
    b.ask("How many songs have speechiness above 0.3 (lots of spoken words)?",
          "SELECT COUNT(*) FROM songs WHERE speechiness > 0.3;", minutes=1, skills=["WHERE"])
    b.ask("Which artist's single shortest song is the shortest of all, and how long is it in seconds?",
          "SELECT a.name, s.name, s.duration_ms / 1000.0\nFROM songs s JOIN artists a ON a.id = s.artist_id\n"
          "ORDER BY s.duration_ms\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} — {r[0][1]} ({r[0][2]:.0f} seconds)", minutes=2,
          skills=["JOIN", "ORDER BY", "units of measurement"])
    return b.items


# -------------------------------------------------------------------- movies
def movies():
    b = SqlBank("movies", "movies_subset.db")
    b.ask("Which movie has the most IMDb votes?",
          "SELECT m.title, r.votes\nFROM movies m JOIN ratings r ON r.movie_id = m.id\nORDER BY r.votes DESC\nLIMIT 1;",
          fmt=lambda r: f"{r[0][0]} ({num(r[0][1])} votes)", minutes=1.5, skills=["JOIN", "ORDER BY"])
    b.ask("How many people in the people table have no birth year recorded?",
          "SELECT COUNT(*) FROM people WHERE birth IS NULL;", minutes=1, skills=["NULL", "missing data"])
    b.ask("Which person has directed the most movies in this database?",
          "SELECT p.name, COUNT(*) AS n\nFROM directors d JOIN people p ON p.id = d.person_id\nGROUP BY p.id\n"
          "ORDER BY n DESC\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} ({r[0][1]} movies)", minutes=2,
          skills=["JOIN", "GROUP BY"])
    b.ask("How many movies list exactly one star in the stars table?",
          "SELECT COUNT(*) FROM (\n  SELECT movie_id FROM stars\n  GROUP BY movie_id\n  HAVING COUNT(*) = 1\n);",
          minutes=2, skills=["GROUP BY", "HAVING"])
    b.ask("How many movie titles are used by more than one movie (same title, different movie)?",
          "SELECT COUNT(*) FROM (\n  SELECT title FROM movies\n  GROUP BY title\n  HAVING COUNT(*) > 1\n);",
          minutes=2, skills=["GROUP BY", "HAVING", "unique identifiers"])
    b.ask("How many movies have more than one director?",
          "SELECT COUNT(*) FROM (\n  SELECT movie_id FROM directors\n  GROUP BY movie_id\n  HAVING COUNT(*) > 1\n);",
          minutes=2, skills=["GROUP BY", "HAVING"])
    b.ask("Among people born in 1990 or later, who has starred in the most movies?",
          "SELECT p.name, COUNT(*) AS n\nFROM stars s JOIN people p ON p.id = s.person_id\nWHERE p.birth >= 1990\n"
          "GROUP BY p.id\nORDER BY n DESC\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} ({r[0][1]} movies)", minutes=2.5,
          skills=["JOIN", "WHERE", "GROUP BY"])
    b.ask("What is the average number of votes for movies rated 8.0 or higher? (whole number)",
          "SELECT ROUND(AVG(votes)) FROM ratings WHERE rating >= 8.0;", fmt=lambda r: num(int(r[0][0])), minutes=1.5,
          skills=["AVG", "WHERE"])
    b.ask("What is the earliest release year in the database, and how many movies are from that year?",
          "SELECT year, COUNT(*) FROM movies\nWHERE year = (SELECT MIN(year) FROM movies);",
          fmt=lambda r: f"{r[0][0]} ({r[0][1]} movies)", minutes=1.5, skills=["subqueries", "MIN"])
    b.ask("Which movie released in 2020 or later has the highest rating (ties broken by votes)?",
          "SELECT m.title, r.rating\nFROM movies m JOIN ratings r ON r.movie_id = m.id\nWHERE m.year >= 2020\n"
          "ORDER BY r.rating DESC, r.votes DESC\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} ({r[0][1]})", minutes=2,
          skills=["JOIN", "ORDER BY"])
    b.ask("How many movies have no director listed?",
          "SELECT COUNT(*)\nFROM movies m\nLEFT JOIN directors d ON d.movie_id = m.id\nWHERE d.person_id IS NULL;",
          minutes=2, skills=["JOIN", "NULL"])
    return b.items


# ---------------------------------------------------------------- Fiftyville
def fiftyville():
    b = SqlBank("fiftyville", "fiftyville.db")
    day = "year = 2020 AND month = 7 AND day = 28"
    b.ask("How many crime scene reports were filed on July 28, 2020?",
          f"SELECT COUNT(*) FROM crime_scene_reports WHERE {day};", minutes=1, skills=["WHERE"])
    b.ask("How many vehicles left the courthouse parking lot between 10:15 and 10:25 on July 28, 2020?",
          f"SELECT COUNT(*) FROM courthouse_security_logs\nWHERE {day} AND hour = 10\n"
          "  AND minute BETWEEN 15 AND 25 AND activity = 'exit';", minutes=1.5, skills=["WHERE", "BETWEEN"])
    b.ask("How many withdrawals were made at the Fifer Street ATM on July 28, 2020, and what was their total?",
          f"SELECT COUNT(*), SUM(amount) FROM atm_transactions\nWHERE {day}\n"
          "  AND atm_location = 'Fifer Street' AND transaction_type = 'withdraw';",
          fmt=lambda r: f"{r[0][0]} withdrawals, {num(r[0][1])} in total", minutes=1.5, skills=["WHERE", "SUM"])
    b.ask("How many phone calls on July 28, 2020 lasted less than a minute?",
          f"SELECT COUNT(*) FROM phone_calls WHERE {day} AND duration < 60;", minutes=1, skills=["WHERE"])
    b.ask("At what time does the earliest flight out of Fiftyville leave on July 29, 2020, and where does it go?",
          "SELECT f.hour, f.minute, a.city\nFROM flights f JOIN airports a ON a.id = f.destination_airport_id\n"
          "WHERE f.year = 2020 AND f.month = 7 AND f.day = 29\n"
          "  AND f.origin_airport_id = (SELECT id FROM airports WHERE city = 'Fiftyville')\n"
          "ORDER BY f.hour, f.minute LIMIT 1;", fmt=lambda r: f"{r[0][0]}:{r[0][1]:02d} to {r[0][2]}", minutes=2,
          skills=["JOIN", "subqueries", "ORDER BY"])
    b.ask("Combine the courthouse exits (10:15–10:25), the Fifer Street withdrawals and the short calls on July 28. "
          "How many people match all three clues?",
          f"SELECT COUNT(*) FROM people p\nWHERE p.license_plate IN (\n    SELECT license_plate FROM courthouse_security_logs\n"
          f"    WHERE {day} AND hour = 10 AND minute BETWEEN 15 AND 25 AND activity = 'exit')\n"
          "  AND p.id IN (\n    SELECT person_id FROM bank_accounts WHERE account_number IN (\n"
          f"      SELECT account_number FROM atm_transactions\n      WHERE {day} AND atm_location = 'Fifer Street'\n"
          "        AND transaction_type = 'withdraw'))\n"
          f"  AND p.phone_number IN (\n    SELECT caller FROM phone_calls WHERE {day} AND duration < 60);",
          minutes=5, skills=["subqueries", "IN", "investigation"])
    return b.items


# -------------------------------------------------------------------- P-cards
def pcards():
    b = SqlBank("pcards", "pcards_2014.db")
    b.ask("Which cardholder had the most transactions in 2014, and how many?",
          "SELECT FullName, COUNT(*) AS NumTrans\nFROM pcards\nGROUP BY FullName\nORDER BY NumTrans DESC\nLIMIT 1;",
          fmt=lambda r: f"{r[0][0]} ({num(r[0][1])})", minutes=1.5, skills=["GROUP BY", "ORDER BY"])
    b.ask("How many cardholders had more than 10 transactions in 2014?",
          "SELECT COUNT(*) FROM (\n  SELECT FullName FROM pcards\n  GROUP BY FullName\n  HAVING COUNT(*) > 10\n);",
          minutes=2, skills=["GROUP BY", "HAVING"])
    b.ask("How many cardholders bought from more than 100 different vendors in 2014?",
          "SELECT COUNT(*) FROM (\n  SELECT FullName FROM pcards\n  GROUP BY FullName\n"
          "  HAVING COUNT(DISTINCT Vendor) > 100\n);", minutes=2, skills=["GROUP BY", "HAVING", "DISTINCT"])
    b.ask("Which vendor was used by the largest number of different cardholders?",
          "SELECT Vendor, COUNT(DISTINCT FullName) AS Cardholders\nFROM pcards\nGROUP BY Vendor\n"
          "ORDER BY Cardholders DESC\nLIMIT 1;", fmt=lambda r: f"{r[0][0]} ({r[0][1]} cardholders)", minutes=2,
          skills=["GROUP BY", "DISTINCT"])
    b.ask("What percentage of 2014 transactions are returns (negative amounts)? (2 decimals)",
          "SELECT ROUND(100.0 * SUM(CASE WHEN Amount < 0 THEN 1 ELSE 0 END) / COUNT(*), 2) FROM pcards;",
          fmt=lambda r: f"{r[0][0]}%", minutes=2, skills=["CASE WHEN", "returns", "percentages"])
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
    b.ask("Control test: how many employee-months in 2014 exceeded $10,000 of spending?",
          "SELECT COUNT(*) FROM (\n  SELECT FullName, Month FROM pcards\n  GROUP BY FullName, Month\n"
          "  HAVING SUM(Amount) > 10000\n);", minutes=2.5, skills=["GROUP BY", "HAVING", "internal controls"])
    b.ask("Just under the limit: how many transactions are between $4,900.00 and $4,999.99, compared with between "
          "$4,800.00 and $4,899.99?",
          "SELECT SUM(Amount BETWEEN 4900 AND 4999.99) AS Just_below,\n       SUM(Amount BETWEEN 4800 AND 4899.99) AS Band_below\n"
          "FROM pcards;", fmt=lambda r: f"{r[0][0]} versus {r[0][1]}", minutes=2,
          skills=["BETWEEN", "fraud tests", "internal controls"])
    b.ask("Split purchases: how many cases are there where the same cardholder made more than one purchase from the "
          "same vendor on the same day and the combined total was more than $5,000?",
          "SELECT COUNT(*) FROM (\n  SELECT FullName, Vendor, TransactionDate\n  FROM pcards\n"
          "  GROUP BY FullName, Vendor, TransactionDate\n  HAVING COUNT(*) > 1 AND SUM(Amount) > 5000\n);",
          minutes=3, skills=["GROUP BY", "HAVING", "internal controls"])
    b.ask("Split across people: on how many vendor-days did exactly two different cardholders buy from the same vendor "
          "with a combined total above $5,000?",
          "SELECT COUNT(*) FROM (\n  SELECT Vendor, TransactionDate\n  FROM pcards\n  WHERE Amount > 0\n"
          "  GROUP BY Vendor, TransactionDate\n  HAVING COUNT(DISTINCT FullName) = 2 AND SUM(Amount) > 5000\n);",
          minutes=3, skills=["GROUP BY", "HAVING", "DISTINCT", "internal controls"])
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
                        "the real last date is in December. Sort by Year, Month and the day instead",
          minutes=2, skills=["dates", "data types"])
    b.ask("How many transactions have no Description?",
          "SELECT COUNT(*) FROM pcards WHERE Description IS NULL OR TRIM(Description) = '';", minutes=1,
          skills=["NULL", "missing data"])
    b.ask("Travel control: on how many cardholder-days was there both a hotel/motel purchase and a restaurant or "
          "fast-food purchase? (MCC contains HOTEL or MOTEL, and RESTAURANT.)",
          "SELECT COUNT(*) FROM (\n  SELECT FullName, TransactionDate\n  FROM pcards\n  GROUP BY FullName, TransactionDate\n"
          "  HAVING SUM(MCC LIKE '%HOTEL%' OR MCC LIKE '%MOTEL%') > 0\n     AND SUM(MCC LIKE '%RESTAURANT%') > 0\n);",
          minutes=3.5, skills=["GROUP BY", "HAVING", "LIKE", "internal controls"])
    return b.items


def all_questions():
    build_databases()
    return chinook() + songs() + movies() + fiftyville() + pcards()
