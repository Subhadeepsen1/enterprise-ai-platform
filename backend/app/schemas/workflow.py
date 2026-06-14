"""Pydantic schemas for workflow."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.workflow_model import WorkflowStatus, ApprovalRecommendation


class WorkflowResponse(BaseModel):
    id: int
    document_id: int
    status: WorkflowStatus
    ai_recommendation: Optional[ApprovalRecommendation]
    risk_score: Optional[float]
    confidence: Optional[float]
    missing_fields: Optional[List[str]]
    action_items: Optional[List[dict]]
    compliance_issues: Optional[List[dict]]
    recommendation_reason: Optional[str]
    assigned_to: Optional[int]
    approved_by: Optional[int]
    approval_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}


class WorkflowUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None
