"""Run: python ch06.py [starter|solution]. Exact, inspectable retrieval fixture."""
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class Passage:
    id: str
    tenant: str
    text: str


DOCS = [
    Passage("policy:v2:p2", "A", "INV-042 duplicate settlement requires ledger review."),
    Passage("billing:v1:p1", "A", "Invoice invoice billing copy receipt."),
    Passage("manual:v1:p3", "A", "Currency mismatch requires correcting the currency."),
    Passage("secret:v1:p1", "B", "INV-042 private waiver."),
]


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())


def concepts(text: str) -> set[str]:
    # Small transparent stand-in for a learned semantic retriever.
    text = text.lower().replace("charged twice", "duplicate settlement")
    return set(tokens(text))


def answer(query: str, hybrid: bool) -> tuple[str, list[str]]:
    allowed = [p for p in DOCS if p.tenant == "A"]
    q = set(tokens(query))
    def lexical(p: Passage) -> float:
        words = Counter(tokens(p.text))
        return sum(math.log(1 + len(allowed) / (1 + sum(t in tokens(d.text) for d in allowed)))
                   * min(words[t], 2) for t in q)
    def semantic(p: Passage) -> float:
        a, b = concepts(query), concepts(p.text)
        return len(a & b) / max(1, len(a | b))
    ranks: Counter[str] = Counter()
    for scorer in ([lexical, semantic] if hybrid else [lexical]):
        for rank, p in enumerate(sorted(allowed, key=scorer, reverse=True), 1):
            if scorer(p) > 0:
                ranks[p.id] += 1 / (60 + rank)
    candidates = [key for key, _ in ranks.most_common()]
    if not candidates:
        return "insufficient evidence", []
    first = next(p for p in allowed if p.id == candidates[0])
    return first.text, candidates  # Extractive answer has an exact supporting quote.


def run(strict: bool) -> None:
    result, ids = answer("charged twice", strict)
    print(result, ids)
    assert bool(ids) == strict
    assert answer("INV-042", strict)[1][0] == "policy:v2:p2"
    assert not answer("weather forecast", strict)[1]

if __name__ == "__main__":
    run("starter" not in sys.argv)
