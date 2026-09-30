from typing import Any


def plan_actions(analysis: dict[str, Any], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Generate remediation actions based on the RCA result and
    current system evidence.
    """

    probable_cause = analysis.get("probable_cause", "").lower()
    service_status = evidence.get("service_status", {})
    deployments = evidence.get("deployments", [])

    actions = []

    # ---------------------------------------------------------
    # Action 1: Rollback recent deployment
    # ---------------------------------------------------------

    if "deployment" in probable_cause and deployments:
        deployment = deployments[0]

        current_version = deployment.get("version", "unknown")
        previous_version = deployment.get("previous_version", "unknown")
        service = deployment.get("service", "unknown")

        actions.append({
            "action_id": "ACT-ROLLBACK",
            "action": "rollback",
            "target": service,
            "from_version": current_version,
            "to_version": previous_version,
            "risk_level": "medium",
            "approval_required": True,
            "reason": (
                f"Rollback {service} from {current_version} to "
                f"{previous_version} because the incident began after "
                f"the recent deployment."
            ),
        })

    # ---------------------------------------------------------
    # Action 2: Restart connection pool
    # ---------------------------------------------------------

    if "database" in probable_cause:
        actions.append({
            "action_id": "ACT-RESTART-DB-POOL",
            "action": "restart_connection_pool",
            "target": service_status.get("service", "unknown"),
            "risk_level": "low",
            "approval_required": False,
            "reason": (
                "Restart the database connection pool to clear "
                "temporary connection failures."
            ),
        })

    # ---------------------------------------------------------
    # Action 3: Retry connections
    # ---------------------------------------------------------

    if "database" in probable_cause:
        actions.append({
            "action_id": "ACT-RETRY-DB",
            "action": "retry_database_connections",
            "target": service_status.get("service", "unknown"),
            "risk_level": "low",
            "approval_required": False,
            "reason": (
                "Retry database connections to determine whether "
                "the failure is temporary."
            ),
        })

    # ---------------------------------------------------------
    # Select recommended action
    # ---------------------------------------------------------

    recommended_action_id = None

    if "deployment" in probable_cause:
        recommended_action_id = "ACT-ROLLBACK"
    elif "database" in probable_cause and actions:
        recommended_action_id = actions[0]["action_id"]

    return {
        "recommended_action_id": recommended_action_id,
        "actions": actions,
    }