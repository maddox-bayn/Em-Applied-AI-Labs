"""Run: python ch09.py [starter|solution] [--gate]. --gate exits 1 on rejection."""
import json
import random
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    id: str
    critical: bool
    base: bool
    candidate: bool


def evaluate(rows: list[Case], strict: bool) -> bool:
    differences = [int(r.candidate)-int(r.base) for r in rows]
    rng = random.Random(7)
    boot = sorted(sum(rng.choices(differences, k=len(rows)))/len(rows) for _ in range(1000))
    regressions = [r.id for r in rows if r.critical and r.base and not r.candidate]
    allow = sum(differences) >= 0 and (not strict or not regressions)
    print(json.dumps({"cases":len(rows), "base_pass":sum(r.base for r in rows),
                      "candidate_pass":sum(r.candidate for r in rows),
                      "critical_cases":sum(r.critical for r in rows),
                      "critical_regressions":regressions,
                      "paired_delta_ci":[boot[25], boot[974]], "ship":allow}))
    return allow


def run(strict: bool) -> bool:
    rows = [Case(f"billing-{i:03}", i < 5, i < 90, i != 0) for i in range(100)]
    decision = evaluate(rows, strict)
    assert decision == (not strict)
    return decision

if __name__ == "__main__":
    passed = run("starter" not in sys.argv)
    sys.exit(int("--gate" in sys.argv and not passed))
