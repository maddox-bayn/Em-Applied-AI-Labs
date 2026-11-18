"""Run: python ch02.py [starter|solution]"""
import sys
from dataclasses import dataclass
from statistics import median
from time import perf_counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import confusion_matrix


@dataclass(frozen=True)
class Incident:
    day: int
    thread: int
    reason: str
    critical: int
    resolution: str  # Available only after an analyst closes the incident.


def fixture() -> list[Incident]:
    rows = []
    for day in range(120):
        label = int(day % 5 == 0)
        words = ("duplicate debit", "charged twice") if label else ("receipt missing", "invoice copy")
        reason = "billing question" if day % 7 == 0 else words[day % 2]
        for _ in range(2):  # Two messages from the same thread.
            rows.append(Incident(day, day, reason, label, "escalated" if label else "resolved"))
    return rows


def run(leaky: bool) -> None:
    rows = fixture()
    if leaky:
        train, valid, test = rows[::2], rows[1:161:2], rows[161::2]
    else:
        # Each thread has one opening message. Fit the vectorizer on training text only.
        opening = list({r.thread: r for r in reversed(rows)}.values())
        train = [r for r in opening if r.day < 70]
        valid = [r for r in opening if 70 <= r.day < 95]
        test = [r for r in opening if r.day >= 95]
        assert not ({r.thread for r in train} & {r.thread for r in valid + test})

    def features(records: list[Incident]) -> list[str]:
        return [r.reason + (" " + r.resolution if leaky else "") for r in records]

    model = make_pipeline(TfidfVectorizer(), LogisticRegression(random_state=7))
    model.fit(features(train), [r.critical for r in train])
    probabilities = model.predict_proba(features(valid))[:, 1]
    truth = np.array([r.critical for r in valid])
    def cost(threshold: float) -> int:
        flag = probabilities >= threshold
        return int(10 * np.sum((truth == 1) & ~flag) + np.sum((truth == 0) & flag))
    threshold = min([0.15, 0.25, 0.4, 0.5, 0.7], key=cost)
    predicted = model.predict_proba(features(test))[:, 1] >= threshold
    y = [r.critical for r in test]
    print("threshold", threshold, "matrix [TN FP; FN TP]", confusion_matrix(y, predicted, labels=[0,1]).tolist())
    print("always-routine missed", sum(y), "of", len(y))
    durations = []
    for _ in range(101):
        start = perf_counter()
        model.predict_proba(["duplicate debit"])
        durations.append((perf_counter() - start) * 1000)
    print("warm model ms, median/p95", round(median(durations[1:]), 3),
          round(float(np.percentile(durations[1:], 95)), 3))

if __name__ == "__main__":
    run("starter" in sys.argv)
