"""Run the CPU fixture chain and assert each user-visible boundary."""
from ch04 import extract, fixture
from ch06 import answer
from ch08 import run as replay_action
from ch09 import run as release_gate
from ch10 import run as trace_incident
from ch11 import run as restore_release


def audit() -> None:
    assert extract(lambda _:fixture("109"),1,True).startswith("review")
    _, ids = answer("INV-042",True)
    assert ids[0] == "policy:v2:p2" and "secret:v1:p1" not in ids
    replay_action(True)
    assert not release_gate(True)
    trace_incident(True)
    restore_release(True)
    print("CPU boundary audit passed")

if __name__ == "__main__":
    audit()
