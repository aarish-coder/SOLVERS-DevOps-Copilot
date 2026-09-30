const investigateBtn = document.getElementById("investigateBtn");
const approveBtn = document.getElementById("approveBtn");

const incidentIdInput = document.getElementById("incidentId");

let currentAction = null;


function showToast(message) {
    const toast = document.getElementById("toast");

    toast.textContent = message;
    toast.style.display = "block";

    setTimeout(() => {
        toast.style.display = "none";
    }, 2500);
}


function setStep(id, state) {
    const element = document.getElementById(id);

    element.classList.remove("active", "completed");

    if (state === "active") {
        element.classList.add("active");
    }

    if (state === "completed") {
        element.classList.add("completed");
    }
}


function setBadge(id, text) {
    document.getElementById(id).textContent = text;
}


function formatPercent(value) {
    if (value === undefined || value === null) {
        return "—";
    }

    return `${value}%`;
}


async function postJSON(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            typeof data.detail === "string"
                ? data.detail
                : JSON.stringify(data.detail)
        );
    }

    return data;
}


async function getJSON(url) {
    const response = await fetch(url);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            typeof data.detail === "string"
                ? data.detail
                : JSON.stringify(data.detail)
        );
    }

    return data;
}


function renderEvidence(evidence) {

    const grid = document.getElementById("evidenceGrid");

    const sourceNames = [
        "Application Logs",
        "Deployment History",
        "Service Health",
        "Previous Incidents"
    ];

    const sourceData = [
        evidence.logs,
        evidence.deployments,
        evidence.service_status,
        evidence.previous_incidents
    ];

    grid.innerHTML = sourceNames.map((name, index) => {

        const available =
            Array.isArray(sourceData[index])
                ? sourceData[index].length > 0
                : Object.keys(sourceData[index] || {}).length > 0;

        return `
            <div class="evidence-card">
                <strong>${name}</strong>
                <span>${available ? "✓ Collected" : "No data"}</span>
            </div>
        `;
    }).join("");
}


function renderHypotheses(hypotheses) {

    const container = document.getElementById("hypotheses");

    if (!hypotheses || hypotheses.length === 0) {
        container.textContent = "No hypotheses available.";
        return;
    }

    container.innerHTML = hypotheses.map(item => `
        <div class="hypothesis">
            <strong>${item.cause}</strong>
            <span>
                Confidence: ${(item.confidence * 100).toFixed(0)}%
            </span>
        </div>
    `).join("");
}


function renderReasoning(reasoning) {

    const container = document.getElementById("reasoning");

    if (!reasoning || reasoning.length === 0) {
        container.textContent = "No reasoning available.";
        return;
    }

    container.innerHTML = reasoning
        .map(item => `✓ ${item}`)
        .join("<br>");
}


async function investigateIncident() {

    const incidentId = incidentIdInput.value.trim();

    if (!incidentId) {
        showToast("Enter an incident ID.");
        return;
    }

    investigateBtn.disabled = true;
    investigateBtn.textContent = "Investigating...";

    try {

        /* ================================================
           1. INVESTIGATION + RCA
        ================================================= */

        setStep("step-investigation", "active");

        const analysisResult = await postJSON(
            "/incidents/analyze",
            {
                incident_id: incidentId,
                description:
                    "Payment service is returning a high number of 500 errors."
            }
        );

        setStep("step-investigation", "completed");
        setStep("step-rca", "completed");

        const evidence = analysisResult.evidence;
        const analysis = analysisResult.analysis;

        renderEvidence(evidence);
        renderReasoning(analysis.reasoning);
        renderHypotheses(analysis.hypotheses);

        document.getElementById("probableCause").textContent =
            analysis.probable_cause;

        document.getElementById("confidence").textContent =
            `${(analysis.confidence * 100).toFixed(0)}%`;

        document.getElementById("severity").textContent =
            analysis.severity.toUpperCase();

        document.getElementById("serviceName").textContent =
            evidence.service_status.service;

        document.getElementById("errorRate").textContent =
            formatPercent(
                evidence.service_status.error_rate_percent
            );

        document.getElementById("latency").textContent =
            `${evidence.service_status.latency_ms} ms`;

        setBadge("incidentStatus", analysis.severity.toUpperCase());


        /* ================================================
           2. ACTION PLAN
        ================================================= */

        setStep("step-action", "active");

        const planResult = await postJSON(
            "/incidents/plan",
            {
                incident_id: incidentId,
                description:
                    "Payment service is returning a high number of 500 errors."
            }
        );

        setStep("step-action", "completed");

        const actionPlan = planResult.action_plan;

        currentAction = actionPlan.actions.find(
            action =>
                action.action_id ===
                actionPlan.recommended_action_id
        );

        if (!currentAction) {
            throw new Error("No recommended action found.");
        }

        document.getElementById("actionName").textContent =
            `${currentAction.action.toUpperCase()} — ` +
            `${currentAction.from_version || ""} → ` +
            `${currentAction.to_version || ""}`;

        document.getElementById("actionReason").textContent =
            currentAction.reason;

        document.getElementById("riskLevel").textContent =
            currentAction.risk_level.toUpperCase();


        /* ================================================
           3. SAFETY GATE
        ================================================= */

        setStep("step-safety", "active");

        const safetyResult = await postJSON(
            "/incidents/safety",
            {
                incident_id: incidentId,
                description:
                    "Payment service is returning a high number of 500 errors."
            }
        );

        setStep("step-safety", "completed");

        const safety = safetyResult.safety;

        setBadge(
            "safetyDecision",
            safety.decision.replaceAll("_", " ")
        );

        const checks = document.getElementById("safetyChecks");

        checks.innerHTML = safety.checks
            .map(check => `
                <div class="check-item">
                    ✓ ${check}
                </div>
            `)
            .join("");

        document.getElementById("approvalMessage").textContent =
            safety.approval_required
                ? "Risky action detected. Human approval is required."
                : "Action is safe to execute automatically.";

        approveBtn.disabled = !safety.approval_required;

        setStep(
            "step-approval",
            safety.approval_required
                ? "active"
                : "completed"
        );

        showToast("Investigation and safety assessment complete.");

    } catch (error) {

        console.error(error);

        showToast(
            `Error: ${error.message}`
        );

    } finally {

        investigateBtn.disabled = false;
        investigateBtn.textContent = "Investigate Incident";
    }
}


/* ========================================================
   HUMAN APPROVAL + EXECUTION
======================================================== */

approveBtn.addEventListener("click", async () => {

    const incidentId = incidentIdInput.value.trim();

    if (!currentAction) {
        showToast("No action available.");
        return;
    }

    approveBtn.disabled = true;
    approveBtn.textContent = "EXECUTING...";

    try {

        /* HUMAN APPROVAL */

        await postJSON(
            "/incidents/approve",
            {
                incident_id: incidentId,
                action_id: currentAction.action_id
            }
        );

        setStep("step-approval", "completed");


        /* EXECUTION */

        setStep("step-execution", "active");

        await postJSON(
            "/incidents/execute",
            {
                incident_id: incidentId,
                action_id: currentAction.action_id
            }
        );

        setStep("step-execution", "completed");


        /* VERIFICATION */

        setStep("step-verification", "active");

        const verification = await getJSON(
            `/incidents/${incidentId}/verify`
        );

        setStep("step-verification", "completed");

        document.getElementById("beforeError").textContent =
            `${verification.before.error_rate_percent}%`;

        document.getElementById("beforeLatency").textContent =
            `${verification.before.latency_ms} ms`;

        document.getElementById("beforeDb").textContent =
            `${verification.before.db_failures_per_minute}/min`;

        document.getElementById("afterError").textContent =
            `${verification.after.error_rate_percent}%`;

        document.getElementById("afterLatency").textContent =
            `${verification.after.latency_ms} ms`;

        document.getElementById("afterDb").textContent =
            `${verification.after.db_failures_per_minute}/min`;

        setBadge(
            "recoveryStatus",
            verification.recovered
                ? "RECOVERED"
                : "FAILED"
        );

        document.getElementById("recoveryMessage").textContent =
            verification.message;


        /* REPORT */

        const reportResult = await getJSON(
            `/incidents/${incidentId}/report`
        );

        document.getElementById("report").textContent =
            JSON.stringify(reportResult.report, null, 2);

        showToast(
            verification.recovered
                ? "Incident resolved and recovery verified."
                : "Recovery failed."
        );

    } catch (error) {

        console.error(error);

        showToast(
            `Execution error: ${error.message}`
        );

        approveBtn.disabled = false;

    } finally {

        approveBtn.textContent = "APPROVE & EXECUTE";
    }
});


investigateBtn.addEventListener(
    "click",
    investigateIncident
);