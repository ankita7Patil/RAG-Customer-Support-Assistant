from __future__ import annotations

from typing import Literal, TypedDict


Intent = Literal["faq", "refund", "technical_issue", "human_request", "unknown"]


class AgentState(TypedDict, total=False):
    query: str
    intent: Intent
    retrieved_chunks: list[dict]
    answer: str
    confidence: float
    route: Literal["answer", "escalate"]
    escalated: bool
    escalation_reason: str
    human_response: str
