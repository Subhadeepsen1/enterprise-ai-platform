"""Workflow execution database model."""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class WorkflowStatus(str, enum.Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    ON_HOLD = "on_hold"


class ApprovalRecommendation(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    MANUAL_REVIEW = "manual_review"


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, unique=True)

    # Workflow state
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus), default=WorkflowStatus.PENDING, nullable=False
    )
    ai_recommendation: Mapped[ApprovalRecommendation] = mapped_column(
        Enum(ApprovalRecommendation), nullable=True
    )

    # AI Analysis
    risk_score: Mapped[float] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    missing_fields: Mapped[list] = mapped_column(JSON, nullable=True)
    action_items: Mapped[list] = mapped_column(JSON, nullable=True)
    compliance_issues: Mapped[list] = mapped_column(JSON, nullable=True)
    recommendation_reason: Mapped[str] = mapped_column(Text, nullable=True)

    # Assignment
    assigned_to: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_by: Mapped[int] = mapped_column(Integer, nullable=True)
    approval_notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="workflow")
    assigned_to_user: Mapped["User"] = relationship("User", back_populates="workflows")

    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, status={self.status}, doc_id={self.document_id})>"
