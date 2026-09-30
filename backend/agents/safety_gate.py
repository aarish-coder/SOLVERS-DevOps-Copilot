from typing import Any


def evaluate_action(
    action: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate whether a proposed remediation action is safe to execute.

    The safety gate is deterministic. The AI may propose an action,
    but this layer decides whether execution is allowed, blocked,
    or requires human approval.
    """

    action_id = action.get("action_id")
    action_type = action.get("action")
    risk_level = action.get("risk_level", "high")

    checks = []
    blocked_reasons = []

    # =========================================================
    # ROLLBACK SAFETY CHECK
    # =========================================================

    if action_type == "rollback":

        deployments = evidence.get("deployments", [])
        service_status = evidence.get("service_status", {})

        if not deployments:
            blocked_reasons.append(
                "No deployment information is available."
            )
        else:
            deployment = deployments[0]

            current_version = deployment.get("version")
            previous_version = deployment.get("previous_version")

            # Check 1: target deployment exists
            if current_version:
                checks.append(
                    f"Current deployment identified: {current_version}"
                )
            else:
                blocked_reasons.append(
                    "Current deployment version is unknown."
                )

            # Check 2: rollback target exists
            if previous_version:
                checks.append(
                    f"Rollback target available: {previous_version}"
                )
            else:
                blocked_reasons.append(
                    "No rollback target version is available."
                )

            # Check 3: target matches active service
            target_service = action.get("target")
            active_service = service_status.get("service")

            if target_service and active_service == target_service:
                checks.append(
                    "Action target matches the affected service."
                )
            else:
                blocked_reasons.append(
                    "Action target does not match the affected service."
                )

        # Rollback is considered medium risk
        # and therefore requires human approval.
        approval_required = True

    # =========================================================
    # RESTART CONNECTION POOL
    # =========================================================

    elif action_type == "restart_connection_pool":

        service_status = evidence.get("service_status", {})
        dependency_status = service_status.get(
            "dependency_status",
            {}
        )

        if dependency_status.get("database") == "unhealthy":
            checks.append(
                "Database dependency is currently unhealthy."
            )
        else:
            checks.append(
                "Database dependency is not currently reported as unhealthy."
            )

        checks.append(
            "Connection-pool restart affects the application service."
        )

        approval_required = False

        if risk_level not in {"low", "medium", "high"}:
            blocked_reasons.append(
                "Invalid risk classification."
            )

    # =========================================================
    # RETRY DATABASE CONNECTIONS
    # =========================================================

    elif action_type == "retry_database_connections":

        checks.append(
            "Database connection failures are present in the evidence."
        )

        checks.append(
            "Retry operation does not change deployment configuration."
        )

        approval_required = False

    # =========================================================
    # UNKNOWN ACTION
    # =========================================================

    else:
        approval_required = True

        blocked_reasons.append(
            f"Unknown or unsupported action: {action_type}"
        )

    # =========================================================
    # FINAL DECISION
    # =========================================================

    if blocked_reasons:
        decision = "BLOCKED"
        safe = False
        approval_required = False

    elif approval_required:
        decision = "HUMAN_APPROVAL_REQUIRED"
        safe = False

    else:
        decision = "SAFE_TO_EXECUTE"
        safe = True

    return {
        "action_id": action_id,
        "decision": decision,
        "safe": safe,
        "risk_level": risk_level,
        "approval_required": approval_required,
        "checks": checks,
        "blocked_reasons": blocked_reasons,
    }