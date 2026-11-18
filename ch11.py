"""Run: python ch11.py [starter|solution]. Atomic release-manifest simulation."""
import sqlite3
import sys
from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class Release:
    id: str
    model: str
    encoder: str
    index_encoder: str
    prompt: str
    service_ms: int


def publish(db: sqlite3.Connection, r: Release) -> None:
    if r.encoder != r.index_encoder:
        raise ValueError("index uses incompatible embedding space")
    with db:
        db.execute("INSERT OR REPLACE INTO active VALUES (1,?,?,?,?,?)",
                   (r.id, r.model, r.encoder, r.index_encoder, r.prompt))


def load_test(r: Release, clients: int, slots: int) -> int:
    # All clients arrive together; one job per slot. Long document for every fifth request.
    free = [0] * slots
    ends = []
    for i in range(clients):
        worker = min(range(slots), key=free.__getitem__)
        free[worker] += r.service_ms * (3 if i % 5 == 0 else 1)
        ends.append(free[worker])
    return sorted(ends)[ceil(.95 * clients)-1]


def run(strict: bool) -> None:
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE active(slot INTEGER PRIMARY KEY,id,model,encoder,idx,prompt)")
    previous = Release("r1","router1","e1","e1","p1",40)
    next_release = Release("r2","router2","e2","e2","p2",160)
    publish(db, previous)
    pinned = db.execute("SELECT id,model,idx FROM active").fetchone()
    publish(db, next_release)
    budget = 1000
    for n in (1,10,100):
        print("clients", n, "baseline/canary p95 ms",
              load_test(previous,n,12), load_test(next_release,n,12))
    if load_test(next_release,100,12) > budget:
        if strict:
            publish(db, previous)
        else:
            with db:
                db.execute("UPDATE active SET model=?", (previous.model,))
    active = db.execute("SELECT id,model,idx FROM active").fetchone()
    assert (active == pinned) == strict
    print("in-flight snapshot", pinned, "new requests", active)
    db.close()

if __name__ == "__main__":
    run("starter" not in sys.argv)
