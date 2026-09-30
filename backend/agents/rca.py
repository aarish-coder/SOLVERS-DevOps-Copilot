from typing import Any


def analyze_root_cause(evidence: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze incident evidence and generate explainable root-cause hypotheses.
    """

    logs = evidence.get("logs", [])
    deployments = evidence.get("deployments", [])
    service_status = evidence.get("service_status", {})
    previous_incidents = evidence.get("previous_incidents", [])

    hypotheses = []

    # =========================================================
    # HYPOTHESIS 1: DEPLOYMENT-INDUCED DATABASE CONNECTION ISSUE
    # =========================================================

    deployment_score = 0.0
    deployment_evidence = []

    if deployments:
        deployment = deployments[0]
        version = deployment.get("version", "unknown")
        deployment_time = deployment.get("timestamp", "")

        deployment_score += 0.30

        deployment_evidence.append(
            f"Recent deployment detected: {version}"
        )

        # Check deployment changes
        changes = deployment.get("changes", [])

        for change in changes:
            change_lower = change.lower()

            if "database" in change_lower or "connection" in change_lower:
                deployment_score += 0.25
                deployment_evidence.append(
                    f"Deployment included a database-related change: {change}"
                )

        # Check whether errors appeared after deployment
        if deployment_time:
            post_deployment_errors = [
                log
                for log in logs
                if log.get("level") == "ERROR"
                and log.get("timestamp", "") > deployment_time
            ]

            if post_deployment_errors:
                deployment_score += 0.25
                deployment_evidence.append(
                    "Database and application errors appeared after the deployment."
                )

    # Historical support
    matching_history = []

    for incident in previous_incidents:
        root_cause = incident.get("root_cause", "").lower()

        if "database" in root_cause:
            matching_history.append(incident)

    if matching_history:
        deployment_score += 0.15
        deployment_evidence.append(
            f"Found {len(matching_history)} similar database-related historical incident(s)."
        )

    deployment_score = min(deployment_score, 1.0)

    hypotheses.append({
        "cause": "Recent deployment introduced a database connection problem",
        "confidence": round(deployment_score, 2),
        "supporting_evidence": deployment_evidence,
    })

    # =========================================================
    # HYPOTHESIS 2: DATABASE DEPENDENCY FAILURE
    # =========================================================

    database_score = 0.0
    database_evidence = []

    dependency_status = service_status.get("dependency_status", {})

    if dependency_status.get("database") == "unhealthy":
        database_score += 0.45
        database_evidence.append(
            "Database dependency is currently unhealthy."
        )

    db_failures = service_status.get("db_failures_per_minute", 0)

    if db_failures > 0:
        database_score += 0.25
        database_evidence.append(
            f"Database failures detected at {db_failures} per minute."
        )

    database_logs = [
        log
        for log in logs
        if "database" in log.get("message", "").lower()
    ]

    if database_logs:
        database_score += 0.20
        database_evidence.append(
            "Application logs contain database connection failures."
        )

    database_score = min(database_score, 1.0)

    hypotheses.append({
        "cause": "Database dependency failure",
        "confidence": round(database_score, 2),
        "supporting_evidence": database_evidence,
    })

    # =========================================================
    # HYPOTHESIS 3: HISTORICAL INCIDENT PATTERN
    # =========================================================

    history_score = 0.0
    history_evidence = []

    for incident in previous_incidents:

        root_cause = incident.get("root_cause", "").lower()
        action = incident.get("action_taken", "").lower()
        result = incident.get("result", "").lower()

        if "database" in root_cause:
            history_score += 0.20
            history_evidence.append(
                f"Similar previous incident: {incident.get('incident_id')}"
            )

        if "rollback" in action and result == "resolved":
            history_score += 0.15
            history_evidence.append(
                f"Previous successful remediation: {incident.get('action_taken')}"
            )

    history_score = min(history_score, 1.0)

    hypotheses.append({
        "cause": "Historical database-related incident pattern",
        "confidence": round(history_score, 2),
        "supporting_evidence": history_evidence,
    })

    # =========================================================
    # SORT HYPOTHESES
    # =========================================================

    hypotheses.sort(
        key=lambda item: item["confidence"],
        reverse=True
    )

    probable = hypotheses[0]

    # =========================================================
    # SEVERITY
    # =========================================================

    error_rate = service_status.get("error_rate_percent", 0)

    if error_rate >= 50:
        severity = "critical"
    elif error_rate >= 20:
        severity = "high"
    elif error_rate >= 5:
        severity = "medium"
    else:
        severity = "low"

    return {
        "incident_id": evidence.get("incident_id"),
        "severity": severity,
        "probable_cause": probable["cause"],
        "confidence": probable["confidence"],
        "reasoning": probable["supporting_evidence"],
        "hypotheses": hypotheses,
    }