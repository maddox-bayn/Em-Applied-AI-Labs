import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier


def run(mode: str) -> tuple[int, int]:
    if mode not in {"starter", "solution"}:
        raise ValueError("choose starter or solution")
    with TemporaryDirectory() as directory:
        path = Path(directory) / "events.db"
        with closing(sqlite3.connect(path)) as db:
            db.executescript("""
                CREATE TABLE events(id INTEGER PRIMARY KEY, key TEXT NOT NULL);
                CREATE TABLE jobs(event_id INTEGER PRIMARY KEY REFERENCES events(id));
            """)
            if mode == "solution":
                db.execute("CREATE UNIQUE INDEX event_key ON events(key)")
        gate = Barrier(20)

        def deliver(_: int) -> None:
            with closing(sqlite3.connect(path, timeout=15)) as db:
                db.execute("PRAGMA foreign_keys=ON")
                if mode == "starter":
                    seen = db.execute("SELECT id FROM events WHERE key=?", ("evt-42",)).fetchone()
                    gate.wait(timeout=10)  # All twenty reads complete before any insert.
                    if seen is not None:
                        return
                    sql = "INSERT INTO events(key) VALUES (?) RETURNING id"
                else:
                    gate.wait(timeout=10)
                    sql = ("INSERT INTO events(key) VALUES (?) "
                           "ON CONFLICT(key) DO NOTHING RETURNING id")
                with db:  # Event and job share a transaction.
                    row = db.execute(sql, ("evt-42",)).fetchone()
                    if row is not None:
                        db.execute("INSERT INTO jobs(event_id) VALUES (?)", (row[0],))

        with ThreadPoolExecutor(max_workers=20) as pool:
            list(pool.map(deliver, range(20)))
        with closing(sqlite3.connect(path)) as db:
            events = db.execute("SELECT count(*) FROM events").fetchone()[0]
            jobs = db.execute("SELECT count(*) FROM jobs").fetchone()[0]
            return events, jobs


if __name__ == "__main__":
    mode = sys.argv[1]
    result = run(mode)
    print(f"{mode}: events={result[0]}, jobs={result[1]}")
    assert result == ((20, 20) if mode == "starter" else (1, 1))
