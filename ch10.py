"""Run: python ch10.py [starter|solution]. Replay deterministic synthetic span durations."""
import sys
from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class Trace:
    id: int
    queue: int
    retrieve: int
    generate: int
    @property
    def total(self) -> int:
        return self.queue + self.retrieve + self.generate


def p95(values: list[int]) -> int:
    return sorted(values)[ceil(.95 * len(values)) - 1]


def replay(capacity: int) -> list[Trace]:
    # Simultaneous arrivals. Each worker holds its slot through both serial stages.
    return [Trace(i, (i // capacity) * 800, 200, 600) for i in range(30)]


def run(strict: bool) -> None:
    baseline, incident = replay(30), replay(10)
    recovery = replay(30 if strict else 10)
    for traces in [baseline, incident, recovery]:
        print("p95 total/wait/model ms", *(p95([getattr(t, k) for t in traces])
                                            for k in ["total", "queue", "generate"]))
    assert p95([t.total for t in recovery]) == (800 if strict else 2400)
    cache: dict[tuple[str, str, str], str] = {("A", "policy-2", "refund"): "NGN 750"}
    assert ("B", "policy-2", "refund") not in cache
    assert ("A", "policy-3", "refund") not in cache

if __name__ == "__main__":
    run("starter" not in sys.argv)
