from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.agents.investigator import investigate_incident
from backend.agents.rca import analyze_root_cause
from backend.agents.action_planner import plan_actions
from backend.agents.safety_gate import evaluate_action
from backend.agents.executor import execute_action
from backend.agents.verifier import verify_recovery

from backend.services.incident_service import build_incident_report
from backend.services.memory_service import save_incident_memory

from backend.models.schemas import (
    IncidentRequest,
    ActionApprovalRequest,
    ActionExecutionRequest,
)


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="SOLVERS",
    description="Safety-Gated AI Incident Response System",
    version="1.0.0",
)


# =========================================================
# PATHS
# =========================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_DIR / "frontend"


# =========================================================
# FRONTEND STATIC FILES
# =========================================================

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)


# =========================================================
# HUMAN APPROVAL STATE
# =========================================================

# Stores explicit human approvals during the current
# server session.
approved_actions: dict[str, str] = {}


# =========================================================
# ROOT / HEALTH
# =========================================================

@app.get("/")
def root():
    """
    Serve the SOLVERS frontend.
    """

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "project": "SOLVERS",
    }


# =========================================================
# STAGE 1 — INVESTIGATION
# =========================================================

@app.post("/incidents/investigate")
def investigate(request: IncidentRequest):
    """
    Collect evidence from multiple operational sources.
    """

    evidence = investigate_incident(
        request.incident_id
    )

    if not any([
        evidence["logs"],
        evidence["deployments"],
        evidence["service_status"],
        evidence["previous_incidents"],
    ]):
        raise HTTPException(
            status_code=404,
            detail=(
                f"No evidence found for incident "
                f"'{request.incident_id}'"
            ),
        )

    return {
        "status": "investigation_complete",
        "incident_id": request.incident_id,
        "evidence": evidence,
    }


# =========================================================
# STAGE 2 — ROOT CAUSE ANALYSIS
# =========================================================

@app.post("/incidents/analyze")
def analyze(request: IncidentRequest):
    """
    Investigation + Root Cause Analysis.
    """

    evidence = investigate_incident(
        request.incident_id
    )

    if not any([
        evidence["logs"],
        evidence["deployments"],
        evidence["service_status"],
        evidence["previous_incidents"],
    ]):
        raise HTTPException(
            status_code=404,
            detail=(
                f"No evidence found for incident "
                f"'{request.incident_id}'"
            ),
        )

    analysis = analyze_root_cause(
        evidence
    )

    return {
        "status": "analysis_complete",
        "incident_id": request.incident_id,
        "evidence": evidence,
        "analysis": analysis,
    }


# =========================================================
# STAGE 3 — ACTION PLANNING
# =========================================================

@app.post("/incidents/plan")
def plan_incident_action(request: IncidentRequest):
    """
    Investigation + RCA + Action Planning.
    """

    evidence = investigate_incident(
        request.incident_id
    )

    if not any([
        evidence["logs"],
        evidence["deployments"],
        evidence["service_status"],
        evidence["previous_incidents"],
    ]):
        raise HTTPException(
            status_code=404,
            detail=(
                f"No evidence found for incident "
                f"'{request.incident_id}'"
            ),
        )

    analysis = analyze_root_cause(
        evidence
    )

    action_plan = plan_actions(
        analysis=analysis,
        evidence=evidence,
    )

    return {
        "status": "action_plan_ready",
        "incident_id": request.incident_id,
        "analysis": analysis,
        "action_plan": action_plan,
    }


# =========================================================
# STAGE 4 — SAFETY GATE
# =========================================================

@app.post("/incidents/safety")
def safety_check(request: IncidentRequest):
    """
    Investigation + RCA + Action Planning
    + Safety Gate.
    """

    evidence = investigate_incident(
        request.incident_id
    )

    if not any([
        evidence["logs"],
        evidence["deployments"],
        evidence["service_status"],
        evidence["previous_incidents"],
    ]):
        raise HTTPException(
            status_code=404,
            detail=(
                f"No evidence found for incident "
                f"'{request.incident_id}'"
            ),
        )

    analysis = analyze_root_cause(
        evidence
    )

    action_plan = plan_actions(
        analysis=analysis,
        evidence=evidence,
    )

    recommended_action_id = action_plan.get(
        "recommended_action_id"
    )

    selected_action = next(
        (
            action
            for action in action_plan.get(
                "actions",
                []
            )
            if action.get(
                "action_id"
            ) == recommended_action_id
        ),
        None,
    )

    if not selected_action:
        raise HTTPException(
            status_code=500,
            detail=(
                "No recommended action "
                "could be selected."
            ),
        )

    safety_result = evaluate_action(
        action=selected_action,
        evidence=evidence,
    )

    return {
        "status": "safety_check_complete",
        "incident_id": request.incident_id,
        "analysis": analysis,
        "selected_action": selected_action,
        "safety": safety_result,
    }


# =========================================================
# STAGE 5 — HUMAN APPROVAL
# =========================================================

@app.post("/incidents/approve")
def approve_action(
    request: ActionApprovalRequest
):
    """
    Record explicit human approval
    for a remediation action.
    """

    approved_actions[
        request.incident_id
    ] = request.action_id

    return {
        "status": "approved",
        "incident_id": request.incident_id,
        "action_id": request.action_id,
        "message": (
            "Human approval recorded. "
            "Action may now be executed."
        ),
    }


# =========================================================
# STAGE 6 — EXECUTION
# =========================================================

@app.post("/incidents/execute")
def execute_approved_action(
    request: ActionExecutionRequest
):
    """
    Execute an approved remediation action.
    """

    approved_action = approved_actions.get(
        request.incident_id
    )

    if approved_action != request.action_id:
        raise HTTPException(
            status_code=403,
            detail=(
                "Action has not received "
                "human approval."
            ),
        )

    # ---------------------------------------------
    # Rebuild current evidence
    # ---------------------------------------------

    evidence = investigate_incident(
        request.incident_id
    )

    # ---------------------------------------------
    # Re-run RCA
    # ---------------------------------------------

    analysis = analyze_root_cause(
        evidence
    )

    # ---------------------------------------------
    # Rebuild action plan
    # ---------------------------------------------

    action_plan = plan_actions(
        analysis=analysis,
        evidence=evidence,
    )

    # ---------------------------------------------
    # Find approved action
    # ---------------------------------------------

    selected_action = next(
        (
            action
            for action in action_plan.get(
                "actions",
                []
            )
            if action.get(
                "action_id"
            ) == request.action_id
        ),
        None,
    )

    if not selected_action:
        raise HTTPException(
            status_code=404,
            detail=(
                "Approved action "
                "could not be found."
            ),
        )

    # ---------------------------------------------
    # Re-check safety immediately before execution
    # ---------------------------------------------

    safety_result = evaluate_action(
        action=selected_action,
        evidence=evidence,
    )

    if safety_result["decision"] == "BLOCKED":
        raise HTTPException(
            status_code=403,
            detail={
                "message": (
                    "Safety gate blocked execution."
                ),
                "safety": safety_result,
            },
        )

    # ---------------------------------------------
    # Execute simulated remediation
    # ---------------------------------------------

    execution = execute_action(
        incident_id=request.incident_id,
        action=selected_action,
    )

    return {
        "status": "execution_complete",
        "incident_id": request.incident_id,
        "action": selected_action,
        "safety": safety_result,
        "execution": execution,
    }


# =========================================================
# STAGE 7 — RECOVERY VERIFICATION
# =========================================================

@app.get("/incidents/{incident_id}/verify")
def verify_incident_recovery(
    incident_id: str
):
    """
    Independently verify whether remediation
    restored the service.
    """

    verification = verify_recovery(
        incident_id
    )

    return {
        "status": "verification_complete",
        **verification,
    }


# =========================================================
# STAGE 8 — INCIDENT REPORT
# =========================================================

@app.get("/incidents/{incident_id}/report")
def get_incident_report(
    incident_id: str
):
    """
    Build the final incident report
    from the completed workflow.
    """

    # ---------------------------------------------
    # Investigation
    # ---------------------------------------------

    evidence = investigate_incident(
        incident_id
    )

    if not any([
        evidence["logs"],
        evidence["deployments"],
        evidence["service_status"],
        evidence["previous_incidents"],
    ]):
        raise HTTPException(
            status_code=404,
            detail=(
                f"No evidence found for incident "
                f"'{incident_id}'"
            ),
        )

    # ---------------------------------------------
    # RCA
    # ---------------------------------------------

    analysis = analyze_root_cause(
        evidence
    )

    # ---------------------------------------------
    # Action Plan
    # ---------------------------------------------

    action_plan = plan_actions(
        analysis=analysis,
        evidence=evidence,
    )

    recommended_action_id = action_plan.get(
        "recommended_action_id"
    )

    selected_action = next(
        (
            action
            for action in action_plan.get(
                "actions",
                []
            )
            if action.get(
                "action_id"
            ) == recommended_action_id
        ),
        None,
    )

    if not selected_action:
        raise HTTPException(
            status_code=404,
            detail=(
                "No remediation action found."
            ),
        )

    # ---------------------------------------------
    # Safety
    # ---------------------------------------------

    safety = evaluate_action(
        action=selected_action,
        evidence=evidence,
    )

    # ---------------------------------------------
    # Load execution result
    # ---------------------------------------------

    runtime_execution_file = (
        PROJECT_DIR
        / "data"
        / "runtime"
        / f"{incident_id}.json"
    )

    execution = {}

    if runtime_execution_file.exists():
        import json

        with open(
            runtime_execution_file,
            "r",
            encoding="utf-8",
        ) as file:
            execution = json.load(file)

    # ---------------------------------------------
    # Verification
    # ---------------------------------------------

    verification = verify_recovery(
        incident_id
    )

    # ---------------------------------------------
    # Build report
    # ---------------------------------------------

    report = build_incident_report(
        incident_id=incident_id,
        evidence=evidence,
        analysis=analysis,
        action=selected_action,
        safety=safety,
        execution=execution,
        verification=verification,
    )

    # ---------------------------------------------
    # Save successful incident memory
    # ---------------------------------------------

    if verification.get("recovered"):
        save_incident_memory(
            incident_id=incident_id,
            analysis=analysis,
            action=selected_action,
            execution=execution,
            verification=verification,
        )

    return {
        "status": "report_generated",
        "report": report,
    }