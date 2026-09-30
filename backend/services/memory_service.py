from pathlib import Path
import json
from typing import Any


MEMORY_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "memory"
)


def save_incident_memory(
    incident_id: str,
    analysis: dict[str, Any],
    action: dict[str, Any],
    execution: dict[str, Any],
    verification: dict[str, Any],
) -> dict[str, Any]:
    """
    Store the outcome of a completed incident response.

    This becomes reusable historical knowledge for future incidents.
    """

    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    memory = {
        "incident_id": incident_id,
        "probable_cause": analysis.get("probable_cause"),
        "confidence": analysis.get("confidence"),
        "severity": analysis.get("severity"),
        "action": {
            "action_id": action.get("action_id"),
            "action": action.get("action"),
            "target": action.get("target"),
        },
        "execution": {
            "executed": execution.get("executed"),
            "message": execution.get("message"),
        },
        "verification": {
            "recovered": verification.get("recovered"),
            "before": verification.get("before"),
            "after": verification.get("after"),
            "message": verification.get("message"),
        },
    }

    memory_file = MEMORY_DIR / f"{incident_id}.json"

    with open(memory_file, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=2)

    return memory