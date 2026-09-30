from typing import Any


def build_incident_report(
    incident_id: str,
    evidence: dict[str, Any],
    analysis: dict[str, Any],
    action: dict[str, Any],
    safety: dict[str, Any],
    execution: dict[str, Any],
    verification: dict[str, Any],
) -> dict[str, Any]:
    """
    Build the final human-readable incident report.
    """

    return {
        "incident_id": incident_id,
        "summary": {
            "severity": analysis.get("severity"),
            "probable_cause": analysis.get("probable_cause"),
            "confidence": analysis.get("confidence"),
            "final_status": (
                "RESOLVED"
                if verification.get("recovered")
                else "UNRESOLVED"
            ),
        },
        "investigation": {
            "sources_checked": evidence.get("sources_checked", []),
            "reasoning": analysis.get("reasoning", []),
            "hypotheses": analysis.get("hypotheses", []),
        },
        "remediation": {
            "action": action,
            "safety": safety,
            "execution": execution,
        },
        "verification": verification,
    }