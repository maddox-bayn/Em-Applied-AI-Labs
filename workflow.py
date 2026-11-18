"""Chapter 8. python workflow.py. Requires langgraph."""
import hashlib
from typing import Literal, TypedDict
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    patch: str
    approved_digest: str
    decision: str


def check(state: State) -> dict[str,str]:
    digest = hashlib.sha256(state["patch"].encode()).hexdigest()
    return {"decision":"simulate" if digest == state["approved_digest"] else "request_approval"}


def destination(state: State) -> Literal["simulate","request_approval"]:
    return "simulate" if state["decision"] == "simulate" else "request_approval"


def run() -> None:
    graph = StateGraph(State)
    graph.add_node("check",check)
    graph.add_node("simulate",lambda s: {"decision":"approved for simulator"})
    graph.add_node("request_approval",lambda s: {"decision":"paused for human"})
    graph.add_edge(START,"check")
    graph.add_conditional_edges("check",destination)
    graph.add_edge("simulate",END)
    graph.add_edge("request_approval",END)
    result = graph.compile().invoke({"patch":"change", "approved_digest":"", "decision":""})
    assert result["decision"] == "paused for human"

if __name__ == "__main__":
    run()
