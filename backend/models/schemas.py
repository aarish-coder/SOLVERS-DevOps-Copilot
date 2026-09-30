from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IncidentRequest(BaseModel):
    incident_id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class EvidenceItem(BaseModel):
    source: str
    timestamp: Optional[str] = None
    data: Dict[str, Any] = {}


class Hypothesis(BaseModel):
    cause: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    supporting_evidence: List[str] = []


class IncidentAnalysis(BaseModel):
    incident_id: str
    severity: str
    probable_cause: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: List[EvidenceItem] = []
    hypotheses: List[Hypothesis] = []


class ActionProposal(BaseModel):
    action_id: str
    action: str
    target: str
    risk_level: str
    approval_required: bool
    reason: str


class SafetyCheckResult(BaseModel):
    action_id: str
    safe: bool
    risk_level: str
    approval_required: bool
    checks: List[str] = []
    blocked_reasons: List[str] = []


class ExecutionResult(BaseModel):
    action_id: str
    executed: bool
    message: str


class VerificationResult(BaseModel):
    incident_id: str
    recovered: bool
    before: Dict[str, Any] = {}
    after: Dict[str, Any] = {}
    message: str


class IncidentResponse(BaseModel):
    incident_id: str
    status: str
    analysis: Optional[IncidentAnalysis] = None
    action: Optional[ActionProposal] = None
    safety: Optional[SafetyCheckResult] = None
    execution: Optional[ExecutionResult] = None
    verification: Optional[VerificationResult] = None
    
class ActionApprovalRequest(BaseModel):
    incident_id: str = Field(..., min_length=1)
    action_id: str = Field(..., min_length=1)


class ActionExecutionRequest(BaseModel):
    incident_id: str = Field(..., min_length=1)
    action_id: str = Field(..., min_length=1)