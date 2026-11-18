"""Run: python ch05.py [starter|solution]."""
import sqlite3
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    page: int
    heading: str
    text: str


def schema(db: sqlite3.Connection) -> None:
    db.executescript("""
        CREATE TABLE chunks(tenant TEXT, doc TEXT, rev INTEGER, page INTEGER,
                            heading TEXT, body TEXT, PRIMARY KEY(tenant,doc,rev,page,heading));
        CREATE TABLE active(tenant TEXT, doc TEXT, rev INTEGER, PRIMARY KEY(tenant,doc));
    """)


def publish(db: sqlite3.Connection, tenant: str, rev: int, chunks: list[Chunk],
            interrupt: bool = False) -> None:
    with db:
        # Serialize publishers and reject late arrivals from an older build.
        db.execute("BEGIN IMMEDIATE")
        current = db.execute("SELECT rev FROM active WHERE tenant=? AND doc='refund'",
                             (tenant,)).fetchone()
        if current and current[0] >= rev:
            return
        if not chunks or any(not c.text.strip() for c in chunks):
            raise ValueError("empty revision")
        for c in chunks:
            db.execute("INSERT INTO chunks VALUES (?,?,?,?,?,?)",
                       (tenant, "refund", rev, c.page, c.heading, c.text))
        if interrupt:
            raise InterruptedError
        db.execute("INSERT OR REPLACE INTO active VALUES (?,?,?)", (tenant, "refund", rev))
        db.execute("DELETE FROM chunks WHERE tenant=? AND doc=? AND rev < ?",
                   (tenant, "refund", rev))


def visible(db: sqlite3.Connection, tenant: str, use_scope: bool) -> list[str]:
    sql = "SELECT body FROM chunks JOIN active USING(tenant,doc,rev)"
    return [r[0] for r in db.execute(sql + (" WHERE tenant=?" if use_scope else ""),
                                     (tenant,) if use_scope else ())]


def run(strict: bool) -> None:
    db = sqlite3.connect(":memory:")
    schema(db)
    def page(text: str) -> list[Chunk]:
        return [Chunk(2, "Refund limits (NGN)", text)]
    publish(db, "A", 1, page("500 NGN"))
    publish(db, "B", 1, page("private exception"))
    try:
        publish(db, "A", 2, page("750 NGN"), interrupt=True)
    except InterruptedError:
        pass
    assert visible(db, "A", True) == ["500 NGN"]
    publish(db, "A", 2, page("750 NGN"))
    publish(db, "A", 1, page("late obsolete update"))
    rows = visible(db, "A", strict)
    assert ("private exception" in rows) == (not strict)
    print(rows)
    db.close()

if __name__ == "__main__":
    run("starter" not in sys.argv)
