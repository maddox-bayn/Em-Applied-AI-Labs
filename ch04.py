"""Run: python ch04.py [starter|solution]. Requires Pydantic 2."""
import sys
from collections.abc import Callable
from decimal import Decimal
from time import monotonic
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Invoice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    currency: Literal["USD", "NGN"]
    total: Decimal = Field(max_digits=14, decimal_places=2)
    items: list[Decimal] = Field(min_length=1)
    page: int = Field(ge=1)


def fixture(total: str) -> str:
    import json
    return json.dumps(dict(currency="NGN", total=total, items=["60", "40"], page=1))


def extract(call: Callable[[float], str], page_count: int, strict: bool) -> str:
    deadline = monotonic() + 2
    for _ in range(2):
        remaining = deadline - monotonic()
        if remaining <= 0:
            break
        try:
            inv = Invoice.model_validate_json(call(remaining))
            if monotonic() > deadline:
                break
        except TimeoutError:
            continue
        except ValidationError:
            return "review: invalid structure"
        if strict and (inv.page > page_count or sum(inv.items) != inv.total):
            return "review: evidence mismatch"
        return "accepted"
    return "review: provider deadline"


def run(strict: bool) -> None:
    assert extract(lambda _: fixture("100"), 1, strict) == "accepted"
    result = extract(lambda _: fixture("109"), 1, strict)
    assert result == ("review: evidence mismatch" if strict else "accepted")
    attempts = 0
    def offline(_: float) -> str:
        nonlocal attempts
        attempts += 1
        raise TimeoutError
    assert extract(offline, 1, strict) == "review: provider deadline" and attempts == 2
    print(result, "outage attempts", attempts)

if __name__ == "__main__":
    run("starter" not in sys.argv)
