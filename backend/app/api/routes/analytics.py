"""Business Analytics Dashboard API routes."""

import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.security import get_current_user, require_manager_or_admin
from app.db.database import get_db
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.workflow_model import WorkflowExecution, WorkflowStatus
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/overview", summary="Dashboard Overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aggregated dashboard metrics:
    - Document counts by type and status
    - Workflow statistics
    - Risk distribution
    - AI confidence averages
    """
    # Base filter
    doc_filter = []
    wf_filter = []
    
    if current_user.role == "employee":
        doc_filter.append(Document.uploaded_by == current_user.id)
    
    # Total documents
    total_docs = (await db.execute(
        select(func.count(Document.id)).where(*doc_filter)
    )).scalar() or 0
    
    # Documents by type
    type_counts_result = await db.execute(
        select(Document.document_type, func.count(Document.id))
        .where(*doc_filter)
        .group_by(Document.document_type)
    )
    docs_by_type = {str(row[0]): row[1] for row in type_counts_result.fetchall()}
    
    # Documents by status
    status_counts_result = await db.execute(
        select(Document.status, func.count(Document.id))
        .where(*doc_filter)
        .group_by(Document.status)
    )
    docs_by_status = {str(row[0]): row[1] for row in status_counts_result.fetchall()}
    
    # Workflow stats
    wf_result = await db.execute(
        select(WorkflowExecution.status, func.count(WorkflowExecution.id))
        .group_by(WorkflowExecution.status)
    )
    workflows_by_status = {str(row[0]): row[1] for row in wf_result.fetchall()}
    
    # Average confidence score
    avg_confidence = (await db.execute(
        select(func.avg(Document.confidence_score)).where(*doc_filter)
    )).scalar() or 0
    
    # Average risk score
    avg_risk = (await db.execute(
        select(func.avg(Document.risk_score)).where(*doc_filter)
    )).scalar() or 0
    
    # High risk documents
    high_risk_count = (await db.execute(
        select(func.count(Document.id))
        .where(Document.risk_score >= 70, *doc_filter)
    )).scalar() or 0
    
    # Pending approvals
    pending_approvals = (await db.execute(
        select(func.count(WorkflowExecution.id))
        .where(WorkflowExecution.status.in_(["pending", "in_review", "escalated"]))
    )).scalar() or 0
    
    return {
        "summary": {
            "total_documents": total_docs,
            "pending_approvals": pending_approvals,
            "high_risk_count": high_risk_count,
            "avg_confidence_score": round(float(avg_confidence or 0) * 100, 1),
            "avg_risk_score": round(float(avg_risk or 0), 1),
        },
        "documents_by_type": docs_by_type,
        "documents_by_status": docs_by_status,
        "workflows_by_status": workflows_by_status,
    }


@router.get("/trends", summary="Monthly Trends")
async def get_trends(
    months: int = 6,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get monthly document processing trends for the past N months."""
    start_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
    
    result = await db.execute(
        select(
            func.date_trunc("month", Document.created_at).label("month"),
            func.count(Document.id).label("count"),
            func.avg(Document.risk_score).label("avg_risk"),
        )
        .where(Document.created_at >= start_date)
        .group_by("month")
        .order_by("month")
    )
    
    trends = [
        {
            "month": row.month.strftime("%Y-%m") if row.month else "N/A",
            "document_count": row.count,
            "avg_risk_score": round(float(row.avg_risk or 0), 1),
        }
        for row in result.fetchall()
    ]
    
    return {"trends": trends, "period_months": months}


@router.get("/risk-distribution", summary="Risk Score Distribution")
async def get_risk_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get risk score distribution across all documents."""
    ranges = [
        ("low", 0, 20),
        ("medium", 20, 40),
        ("high", 40, 70),
        ("critical", 70, 101),
    ]
    
    distribution = {}
    for label, low, high in ranges:
        count = (await db.execute(
            select(func.count(Document.id))
            .where(
                and_(
                    Document.risk_score >= low,
                    Document.risk_score < high,
                    Document.risk_score.isnot(None),
                )
            )
        )).scalar() or 0
        distribution[label] = count
    
    return {"risk_distribution": distribution}


@router.get("/recent-activity", summary="Recent Activity")
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent document processing activity."""
    result = await db.execute(
        select(Document)
        .order_by(Document.created_at.desc())
        .limit(limit)
    )
    docs = result.scalars().all()
    
    return {
        "recent_documents": [
            {
                "id": d.id,
                "filename": d.original_filename,
                "document_type": str(d.document_type),
                "status": str(d.status),
                "risk_score": d.risk_score,
                "risk_level": d.risk_level,
                "confidence_score": d.confidence_score,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ]
    }
