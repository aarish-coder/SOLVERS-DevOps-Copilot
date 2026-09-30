from pathlib import Path
import json
from typing import Any


RUNTIME_DIR = Path(__file__).resolve().parents[2] / "data" / "runtime"


def execute_action(
    incident_id: str,
    action: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute a simulated remediation action.

    This does NOT modify a real production system.
    It changes the simulated runtime state used by the demo.
    """

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    action_type = action.get("action")
    target = action.get("target")

    runtime_state = {
        "incident_id": incident_id,
        "action_id": action.get("action_id"),
        "action": action_type,
        "target": target,
        "executed": False,
        "message": "",
    }

    # =========================================================
    # ROLLBACK
    # =========================================================

    if action_type == "rollback":

        from_version = action.get("from_version")
        to_version = action.get("to_version")

        runtime_state.update({
            "executed": True,
            "message": (
                f"Simulated rollback of {target} "
                f"from {from_version} to {to_version} completed."
            ),
            "system_state": {
                "deployment": {
                    "service": target,
                    "current_version": to_version,
                    "previous_version": from_version,
                    "status": "stable",
                },
                "service_status": {
                    "service": target,
                    "status": "healthy",
                    "error_rate_percent": 3,
                    "latency_ms": 700,
                    "db_failures_per_minute": 0,
                    "cpu_percent": 48,
                    "memory_percent": 54,
                    "dependency_status": {
                        "database": "healthy",
                        "payment_gateway": "healthy",
                    },
                },
            },
        })

    # =========================================================
    # RESTART CONNECTION POOL
    # =========================================================

    elif action_type == "restart_connection_pool":

        runtime_state.update({
            "executed": True,
            "message": (
                f"Simulated database connection pool restart "
                f"for {target} completed."
            ),
            "system_state": {
                "service_status": {
                    "service": target,
                    "status": "healthy",
                    "error_rate_percent": 5,
                    "latency_ms": 1100,
                    "db_failures_per_minute": 1,
                    "cpu_percent": 50,
                    "memory_percent": 56,
                    "dependency_status": {
                        "database": "healthy",
                        "payment_gateway": "healthy",
                    },
                }
            },
        })

    # =========================================================
    # RETRY DATABASE CONNECTIONS
    # =========================================================

    elif action_type == "retry_database_connections":

        runtime_state.update({
            "executed": True,
            "message": (
                f"Simulated database connection retry for "
                f"{target} completed."
            ),
            "system_state": {
                "service_status": {
                    "service": target,
                    "status": "degraded",
                    "error_rate_percent": 35,
                    "latency_ms": 2400,
                    "db_failures_per_minute": 12,
                    "cpu_percent": 57,
                    "memory_percent": 61,
                    "dependency_status": {
                        "database": "degraded",
                        "payment_gateway": "healthy",
                    },
                }
            },
        })

    else:
        runtime_state["message"] = (
            f"Unsupported action: {action_type}"
        )

    # Save simulated post-action state
    runtime_file = RUNTIME_DIR / f"{incident_id}.json"

    with open(runtime_file, "w", encoding="utf-8") as file:
        json.dump(runtime_state, file, indent=2)

    return runtime_state