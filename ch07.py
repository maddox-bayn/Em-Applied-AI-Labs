"""Run: python ch07.py [starter|solution]. Tiny supervised low-rank adapter."""
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np


def save(root: Path, step: int, a: np.ndarray, b: np.ndarray) -> None:
    stage = root / f"stage-{step}"
    stage.mkdir()
    np.savez(stage / "adapter.npz", a=a, b=b)
    (stage / "state.json").write_text(json.dumps({"step": step, "base": "sql-router-v1"}))
    os.rename(stage, root / f"checkpoint-{step}")  # One filesystem; one writer.


def resume(root: Path, complete: bool) -> tuple[int, np.ndarray, np.ndarray]:
    dirs = sorted(root.glob("checkpoint-*"), key=lambda p: int(p.name.split("-")[1]), reverse=True)
    for path in dirs:
        if complete and not all((path / f).is_file() for f in ["state.json", "adapter.npz"]):
            continue
        state = json.loads((path / "state.json").read_text())
        if state["base"] != "sql-router-v1":
            raise ValueError("incompatible base")
        with np.load(path / "adapter.npz") as data:
            return state["step"], data["a"], data["b"]
    raise FileNotFoundError("no compatible checkpoint")


def train(a: np.ndarray, b: np.ndarray, steps: int) -> None:
    # Frozen base has zero logits. Two input features select one of two SQL templates.
    x = np.eye(2)
    y = np.eye(2)
    for _ in range(steps):
        logits = x @ a @ b
        probs = np.exp(logits - logits.max(axis=1, keepdims=True))
        probs /= probs.sum(axis=1, keepdims=True)
        grad = x.T @ (probs - y) / len(x)
        da, db = grad @ b.T, a.T @ grad
        a -= 0.5 * da
        b -= 0.5 * db


def run(strict: bool) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        a = np.array([[0.1], [-0.1]])
        b = np.zeros((1, 2))
        train(a, b, 10)
        save(root, 10, a, b)
        (root / "checkpoint-11").mkdir()  # Simulate interrupted older publisher.
        try:
            step, left, right = resume(root, strict)
        except FileNotFoundError:
            if strict:
                raise
            print("starter selected an incomplete checkpoint")
            return
        train(left, right, 10)
        train(a, b, 10)
        np.testing.assert_allclose(left @ right, a @ b)
        assert (left @ right).argmax(axis=1).tolist() == [0, 1]
        print("resumed", step, "through", step + 10)

if __name__ == "__main__":
    run("starter" not in sys.argv)
