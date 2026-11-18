"""Run: python ch08.py [starter|solution]. Remote service simulated by a second DB."""
import hashlib
import sqlite3
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def execute(local: sqlite3.Connection, remote: sqlite3.Connection, patch: str,
            recover: bool, crash: bool = False) -> int:
    key = hashlib.sha256(patch.encode()).hexdigest()
    record = local.execute("SELECT state FROM actions WHERE digest=?", (key,)).fetchone()
    if record is None:
        raise PermissionError("unapproved patch")
    with remote:
        if recover:
            # The simulated destination itself enforces key uniqueness.
            remote.execute("INSERT INTO prs(digest) VALUES (?) ON CONFLICT(digest) DO NOTHING", (key,))
        else:
            remote.execute("INSERT INTO prs(digest) VALUES (?)", (key,))
        pr = remote.execute("SELECT id FROM prs WHERE digest=? ORDER BY id LIMIT 1", (key,)).fetchone()[0]
    if crash:
        raise InterruptedError("remote committed; receipt lost")
    with local:
        local.execute("UPDATE actions SET state='done' WHERE digest=?", (key,))
    return int(pr)


def run(strict: bool) -> None:
    with TemporaryDirectory() as tmp:
        local = sqlite3.connect(Path(tmp) / "state.db")
        remote = sqlite3.connect(Path(tmp) / "remote.db")
        local.execute("CREATE TABLE actions(digest TEXT PRIMARY KEY,state TEXT)")
        remote.execute("CREATE TABLE prs(id INTEGER PRIMARY KEY,digest TEXT)")
        if strict:
            remote.execute("CREATE UNIQUE INDEX once_per_action ON prs(digest)")
        patch = "repo=demo;base=abc;change=fix invoice parser"
        with local:
            local.execute("INSERT INTO actions VALUES (?, 'approved')",
                          (hashlib.sha256(patch.encode()).hexdigest(),))
        try:
            execute(local, remote, patch, strict, crash=True)
        except InterruptedError:
            pass
        local.close()
        local = sqlite3.connect(Path(tmp) / "state.db")
        execute(local, remote, patch, strict)
        assert remote.execute("SELECT count(*) FROM prs").fetchone()[0] == (1 if strict else 2)
        try:
            execute(local, remote, patch + " and disclose a secret", strict)
        except PermissionError:
            print("changed action blocked")
        else:
            raise AssertionError("executed an unapproved action")
        local.close()
        remote.close()

if __name__ == "__main__":
    run("starter" not in sys.argv)
