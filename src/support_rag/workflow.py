from __future__ import annotations

from .config import AppConfig
from .hitl import format_escalation_message
from .retrieval import build_answer, detect_intent, retrieve_context, should_escalate
from .state import AgentState

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - optional dependency
    END = "END"
    START = "START"
    StateGraph = None


def _input_node(state: AgentState) -> AgentState:
    return state


def _process_node(state: AgentState, config: AppConfig) -> AgentState:
    state["intent"] = detect_intent(state["query"])
    state["retrieved_chunks"] = retrieve_context(state["query"], config)
    answer, confidence = build_answer(state["query"], state["retrieved_chunks"])
    state["answer"] = answer
    state["confidence"] = confidence
    escalated, reason = should_escalate(
        state["intent"], state["confidence"], state["retrieved_chunks"]
    )
    state["escalated"] = escalated
    state["escalation_reason"] = reason
    state["route"] = "escalate" if escalated else "answer"
    return state


def _output_node(state: AgentState) -> AgentState:
    if state["route"] == "escalate":
        state["human_response"] = format_escalation_message(state["escalation_reason"])
    return state


def run_support_graph(query: str, config: AppConfig) -> AgentState:
    state: AgentState = {"query": query}

    if StateGraph:
        graph = StateGraph(AgentState)
        graph.add_node("input_node", _input_node)
        graph.add_node("process_node", lambda current: _process_node(current, config))
        graph.add_node("output_node", _output_node)
        graph.add_edge(START, "input_node")
        graph.add_edge("input_node", "process_node")
        graph.add_edge("process_node", "output_node")
        graph.add_edge("output_node", END)
        app = graph.compile()
        return app.invoke(state)

    state = _input_node(state)
    state = _process_node(state, config)
    state = _output_node(state)
    return state
