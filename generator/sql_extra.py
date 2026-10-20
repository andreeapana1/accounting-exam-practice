"""More SQL questions on the same course databases (second batch). Answers come from the reference queries."""
from common import money, num
from sql_questions import SqlBank


def first(fmt):
    """Format the top row, refusing a tie with the second row so every answer is unambiguous.

    Queries using this return two rows (LIMIT 2) ordered so the deciding value is the last column.
    """
    def f(rows):
        assert len(rows) < 2 or rows[0][-1] != rows[1][-1], f"tie: {rows}"
        return fmt(rows[0])
    return f


def chinook():
    b = SqlBank("chinook", "Chinook_Sqlite.sqlite")
    b.ask("Which sales support agent looks after the most customers?",
          "SELECT e.FirstName || ' ' || e.LastName AS Agent, COUNT(*) AS Customers\nFROM Customer c\n"
          "JOIN Employee e ON e.EmployeeId = c.SupportRepId\nGROUP BY e.EmployeeId\nORDER BY Customers DESC\nLIMIT 2;",
          fmt=first(lambda r: f"{r[0]} ({r[1]} customers)"), minutes=2, skills=["JOIN", "GROUP BY"])
    b.ask("Which country has the most customers?",
          "SELECT Country, COUNT(*) AS Customers\nFROM Customer\nGROUP BY Country\nORDER BY Customers DESC\nLIMIT 2;",
          fmt=first(lambda r: f"{r[0]} ({r[1]} customers)"), minutes=1, skills=["GROUP BY", "ORDER BY"])
    b.ask("Which genre has the longest average track length, in minutes? (2 decimals)",
          "SELECT g.Name, ROUND(AVG(t.Milliseconds) / 60000.0, 2) AS AvgMinutes\nFROM Track t\n"
          "JOIN Genre g ON g.GenreId = t.GenreId\nGROUP BY g.Name\nORDER BY AvgMinutes DESC\nLIMIT 2;",
          fmt=first(lambda r: f"{r[0]} ({r[1]} minutes)"), minutes=2.5, skills=["JOIN", "AVG", "units of measurement"])
    b.ask("Which album has the most tracks?",
          "SELECT a.Title, COUNT(*) AS Tracks\nFROM Track t JOIN Album a ON a.AlbumId = t.AlbumId\n"
          "GROUP BY a.AlbumId\nORDER BY Tracks DESC\nLIMIT 2;", fmt=first(lambda r: f"{r[0]} ({r[1]} tracks)"),
          minutes=1.5, skills=["JOIN", "GROUP BY"])
    b.ask("How many invoices were issued in 2011?",
          "SELECT COUNT(*) FROM Invoice WHERE strftime('%Y', InvoiceDate) = '2011';", minutes=1,
          skills=["strftime", "dates"])
    b.ask("What share of all tracks are video files (media type name contains 'video')? (1 decimal)",
          "SELECT ROUND(100.0 * SUM(m.Name LIKE '%video%') / COUNT(*), 1)\nFROM Track t\n"
          "JOIN MediaType m ON m.MediaTypeId = t.MediaTypeId;", fmt=lambda r: f"{r[0][0]}%", minutes=2,
          skills=["JOIN", "LIKE", "percentages"])
    b.ask("Which customer bought tracks from the largest number of different genres?",
          "SELECT c.FirstName || ' ' || c.LastName, COUNT(DISTINCT t.GenreId) AS Genres\nFROM Customer c\n"
          "JOIN Invoice i ON i.CustomerId = c.CustomerId\nJOIN InvoiceLine l ON l.InvoiceId = i.InvoiceId\n"
          "JOIN Track t ON t.TrackId = l.TrackId\nGROUP BY c.CustomerId\nORDER BY Genres DESC\nLIMIT 2;",
          fmt=first(lambda r: f"{r[0]} ({r[1]} genres)"), minutes=3, skills=["JOIN", "DISTINCT", "GROUP BY"])
    b.ask("What is the total revenue from Rock tracks (UnitPrice × Quantity on invoice lines)?",
          "SELECT ROUND(SUM(l.UnitPrice * l.Quantity), 2)\nFROM InvoiceLine l\nJOIN Track t ON t.TrackId = l.TrackId\n"
          "JOIN Genre g ON g.GenreId = t.GenreId\nWHERE g.Name = 'Rock';", fmt=lambda r: money(r[0][0]), minutes=2.5,
          skills=["JOIN", "SUM", "calculated fields"])
    b.ask("How many employees have nobody reporting to them?",
          "SELECT COUNT(*) FROM Employee e\nWHERE NOT EXISTS (SELECT 1 FROM Employee x WHERE x.ReportsTo = e.EmployeeId);",
          minutes=2.5, skills=["subqueries", "self join"])
    return b.items


def songs():
    b = SqlBank("songs", "songs.db")
    b.ask("Which song has the highest speechiness?",
          "SELECT name, speechiness FROM songs ORDER BY speechiness DESC LIMIT 2;",
          fmt=first(lambda r: f"{r[0]} ({r[1]})"), minutes=1, skills=["ORDER BY", "LIMIT"])
    b.ask("How many songs have loudness above −5 dB?", "SELECT COUNT(*) FROM songs WHERE loudness > -5;",
          minutes=1, skills=["WHERE"])
    b.ask("How many artists have exactly one song in the database?",
          "SELECT COUNT(*) FROM (\n  SELECT artist_id FROM songs\n  GROUP BY artist_id\n  HAVING COUNT(*) = 1\n);",
          minutes=2, skills=["GROUP BY", "HAVING"])
    b.ask("Rounded down to whole minutes, which song length is most common, and how many songs have it?",
          "SELECT duration_ms / 60000 AS Minutes, COUNT(*) AS Songs\nFROM songs\nGROUP BY Minutes\n"
          "ORDER BY Songs DESC\nLIMIT 2;", fmt=first(lambda r: f"{r[0]} minutes ({r[1]} songs)"), minutes=2.5,
          skills=["GROUP BY", "units of measurement", "calculated fields"])
    b.ask("Which musical key is used by the fewest songs?",
          "SELECT key, COUNT(*) AS n FROM songs GROUP BY key ORDER BY n DESC LIMIT 2 OFFSET 10;",
          fmt=lambda r: f"Key {r[-1][0]} ({r[-1][1]} songs)" if r[-1][1] != r[0][1] else "tie", minutes=1.5,
          skills=["GROUP BY", "ORDER BY"])
    return b.items


def movies():
    b = SqlBank("movies", "movies_subset.db")
    b.ask("Which person has starred in the most movies in this database?",
          "SELECT p.name, COUNT(*) AS n\nFROM stars s JOIN people p ON p.id = s.person_id\nGROUP BY p.id\n"
          "ORDER BY n DESC\nLIMIT 2;", fmt=first(lambda r: f"{r[0]} ({r[1]} movies)"), minutes=2,
          skills=["JOIN", "GROUP BY"])
    b.ask("Data check: how many people have a birth year before 1900?", "SELECT COUNT(*) FROM people WHERE birth < 1900;",
          minutes=1, skills=["WHERE", "data quality"])
    b.ask("What is the largest number of stars listed for one movie, and how many movies have that many?",
          "SELECT n, COUNT(*) FROM (\n  SELECT movie_id, COUNT(*) AS n FROM stars GROUP BY movie_id\n)\n"
          "WHERE n = (SELECT MAX(c) FROM (SELECT COUNT(*) AS c FROM stars GROUP BY movie_id));",
          fmt=lambda r: f"{r[0][0]} stars, {r[0][1]} movies", minutes=3, skills=["subqueries", "GROUP BY", "MAX"])
    b.ask("What is the average rating of movies with more than 1,000,000 votes? (2 decimals)",
          "SELECT ROUND(AVG(rating), 2) FROM ratings WHERE votes > 1000000;", minutes=1, skills=["AVG", "WHERE"])
    b.ask("How many movies have a rating below 3.0?", "SELECT COUNT(*) FROM ratings WHERE rating < 3.0;", minutes=1,
          skills=["WHERE"])
    b.ask("Who directed The Shawshank Redemption?",
          "SELECT p.name\nFROM directors d\nJOIN people p ON p.id = d.person_id\nJOIN movies m ON m.id = d.movie_id\n"
          "WHERE m.title = 'The Shawshank Redemption';", minutes=1.5, skills=["JOIN"])
    b.ask("How many different people have both starred in one movie and directed another (or the same) movie?",
          "SELECT COUNT(*) FROM (\n  SELECT person_id FROM stars\n  INTERSECT\n  SELECT person_id FROM directors\n);",
          minutes=2.5, skills=["INTERSECT", "subqueries"])
    return b.items


def fiftyville():
    b = SqlBank("fiftyville", "fiftyville.db")
    b.ask("What is the full name of Fiftyville's airport?",
          "SELECT full_name FROM airports WHERE city = 'Fiftyville';", minutes=0.5, skills=["WHERE"])
    b.ask("How many passengers were on the earliest flight out of Fiftyville on July 29, 2020?",
          "SELECT COUNT(*) FROM passengers WHERE flight_id = (\n  SELECT id FROM flights\n"
          "  WHERE year = 2020 AND month = 7 AND day = 29\n"
          "    AND origin_airport_id = (SELECT id FROM airports WHERE city = 'Fiftyville')\n"
          "  ORDER BY hour, minute LIMIT 1);", minutes=2.5, skills=["subqueries", "ORDER BY"])
    b.ask("How many interviews recorded on July 28, 2020 mention the courthouse?",
          "SELECT COUNT(*) FROM interviews\nWHERE year = 2020 AND month = 7 AND day = 28 AND transcript LIKE '%courthouse%';",
          minutes=1, skills=["LIKE", "WHERE"])
    b.ask("Which ATM location had the most transactions on July 28, 2020?",
          "SELECT atm_location, COUNT(*) AS n FROM atm_transactions\nWHERE year = 2020 AND month = 7 AND day = 28\n"
          "GROUP BY atm_location\nORDER BY n DESC\nLIMIT 2;", fmt=first(lambda r: f"{r[0]} ({r[1]} transactions)"),
          minutes=1.5, skills=["GROUP BY", "WHERE"])
    return b.items


def pcards():
    b = SqlBank("pcards", "pcards_2014.db")
    b.ask("How many different vendors did OSU cardholders buy from in 2014?",
          "SELECT COUNT(DISTINCT Vendor) FROM pcards;", minutes=0.5, skills=["DISTINCT"])
    b.ask("On average, how many transactions did each cardholder make in 2014? (1 decimal)",
          "SELECT ROUND(1.0 * COUNT(*) / COUNT(DISTINCT FullName), 1) FROM pcards;", minutes=1.5,
          skills=["COUNT", "DISTINCT"])
    b.ask("Which cardholder bought from the largest number of different merchant categories (MCC)?",
          "SELECT FullName, COUNT(DISTINCT MCC) AS Categories\nFROM pcards\nGROUP BY FullName\n"
          "ORDER BY Categories DESC\nLIMIT 2;", fmt=first(lambda r: f"{r[0]} ({r[1]} categories)"), minutes=2,
          skills=["GROUP BY", "DISTINCT"])
    b.ask("How many cardholders made only one transaction in 2014?",
          "SELECT COUNT(*) FROM (\n  SELECT FullName FROM pcards\n  GROUP BY FullName\n  HAVING COUNT(*) = 1\n);",
          minutes=2, skills=["GROUP BY", "HAVING"])
    b.ask("What share of total 2014 spending went to the ten vendors with the highest spending? (1 decimal)",
          "SELECT ROUND(100.0 * SUM(Spent) / (SELECT SUM(Amount) FROM pcards), 1) FROM (\n"
          "  SELECT Vendor, SUM(Amount) AS Spent\n  FROM pcards\n  GROUP BY Vendor\n  ORDER BY Spent DESC\n  LIMIT 10\n);",
          fmt=lambda r: f"{r[0][0]}%", minutes=3, skills=["subqueries", "GROUP BY", "percentages"])
    b.ask("How many purchases (excluding returns) were for less than $1.00?",
          "SELECT COUNT(*) FROM pcards WHERE Amount > 0 AND Amount < 1;", minutes=1, skills=["WHERE", "returns"])
    b.ask("On how many cardholder-days were there more than 10 transactions?",
          "SELECT COUNT(*) FROM (\n  SELECT FullName, TransactionDate\n  FROM pcards\n  GROUP BY FullName, TransactionDate\n"
          "  HAVING COUNT(*) > 10\n);", minutes=2.5, skills=["GROUP BY", "HAVING", "internal controls"])
    b.ask("Which merchant category (MCC) has the most returns (negative amounts)?",
          "SELECT MCC, COUNT(*) AS Returns\nFROM pcards\nWHERE Amount < 0\nGROUP BY MCC\nORDER BY Returns DESC\nLIMIT 2;",
          fmt=first(lambda r: f"{r[0]} ({r[1]} returns)"), minutes=2, skills=["returns", "GROUP BY"])
    b.ask("Vendor names are not standardised. How many distinct vendor names contain 'STAPLES'?",
          "SELECT COUNT(DISTINCT Vendor) FROM pcards WHERE UPPER(Vendor) LIKE '%STAPLES%';", minutes=1.5,
          skills=["LIKE", "UPPER", "data quality"])
    b.ask("What is the average amount of a return in 2014? (2 decimals)",
          "SELECT ROUND(AVG(Amount), 2) FROM pcards WHERE Amount < 0;", fmt=lambda r: money(r[0][0]), minutes=1,
          skills=["AVG", "returns"])
    return b.items


def all_questions():
    return chinook() + songs() + movies() + fiftyville() + pcards()
