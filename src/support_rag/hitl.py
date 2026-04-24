from __future__ import annotations


def format_escalation_message(reason: str) -> str:
    return (
        "This query has been escalated to a human support agent.\n"
        f"Escalation reason: {reason}\n"
        "Suggested next step: collect account details, verify customer identity, and respond manually."
    )
