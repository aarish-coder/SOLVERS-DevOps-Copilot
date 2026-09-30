from backend.tools.log_tool import get_logs
from backend.tools.deployment_tool import get_deployments
from backend.tools.service_tool import get_service_status
from backend.tools.incident_history_tool import get_previous_incidents


def investigate_incident(incident_id: str) -> dict:
    """
    Collect evidence from multiple operational sources.
    """

    logs = get_logs(incident_id)
    deployments = get_deployments(incident_id)
    service_status = get_service_status(incident_id)
    previous_incidents = get_previous_incidents(incident_id)

    evidence = {
        "incident_id": incident_id,
        "sources_checked": [
            "application_logs",
            "deployment_history",
            "service_status",
            "previous_incidents",
        ],
        "logs": logs,
        "deployments": deployments,
        "service_status": service_status,
        "previous_incidents": previous_incidents,
    }

    return evidence