from pathlib import Path
import json
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RUNTIME_DIR = DATA_DIR / "runtime"
SERVICE_DIR = DATA_DIR / "services"


def verify_recovery(incident_id: str) -> dict[str, Any]:
    """
    Independently verify whether the simulated remediation
    actually restored the service.
    """

    original_file = SERVICE_DIR / f"{incident_id}.json"
    runtime_file = RUNTIME_DIR / f"{incident_id}.json"

    if not original_file.exists():
        return {
            "incident_id": incident_id,
            "recovered": False,
            "message": "Original service state not found.",
        }

    if not runtime_file.exists():
        return {
            "incident_id": incident_id,
            "recovered": False,
            "message": "No remediation execution found.",
        }

    try:
        with open(original_file, "r", encoding="utf-8") as file:
            before = json.load(file)

        with open(runtime_file, "r", encoding="utf-8") as file:
            runtime = json.load(file)

    except (json.JSONDecodeError, OSError) as exc:
        return {
            "incident_id": incident_id,
            "recovered": False,
            "message": f"Unable to verify recovery: {exc}",
        }

    after = (
        runtime
        .get("system_state", {})
        .get("service_status", {})
    )

    # Rollback stores deployment + service state.
    if not after:
        return {
            "incident_id": incident_id,
            "recovered": False,
            "before": before,
            "after": {},
            "message": "Post-remediation service state is unavailable.",
        }

    before_error_rate = before.get("error_rate_percent", 100)
    after_error_rate = after.get("error_rate_percent", 100)

    before_latency = before.get("latency_ms", 0)
    after_latency = after.get("latency_ms", 999999)

    before_db_failures = before.get("db_failures_per_minute", 0)
    after_db_failures = after.get("db_failures_per_minute", 999999)

    after_status = after.get("status", "unknown")

    # Independent recovery criteria
    recovered = (
        after_status == "healthy"
        and after_error_rate < before_error_rate
        and after_latency < before_latency
        and after_db_failures < before_db_failures
    )

    if recovered:
        message = "Recovery verified successfully."
    else:
        message = (
            "Recovery could not be verified. "
            "The incident should remain under investigation."
        )

    return {
        "incident_id": incident_id,
        "recovered": recovered,
        "before": {
            "status": before.get("status"),
            "error_rate_percent": before_error_rate,
            "latency_ms": before_latency,
            "db_failures_per_minute": before_db_failures,
        },
        "after": {
            "status": after_status,
            "error_rate_percent": after_error_rate,
            "latency_ms": after_latency,
            "db_failures_per_minute": after_db_failures,
        },
        "message": message,
    }