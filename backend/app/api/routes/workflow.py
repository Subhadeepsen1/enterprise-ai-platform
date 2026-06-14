"""Workflow management API routes."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.security import get_current_user, require_manager_or_admin
from app.db.database import get_db
from app.models.workflow_model import WorkflowExecution, WorkflowStatus
from app.models.document import Document
from app.models.user import User
from app.schemas.workflow import WorkflowResponse, WorkflowUpdateRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", summary="List Workflows")
async def list_workflows(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List workflow executions with filtering."""
    query = (
        select(WorkflowExecution)
        .join(Document)
        .order_by(desc(WorkflowExecution.created_at))
    )
    
    if current_user.role == "employee":
        query = query.where(Document.uploaded_by == current_user.id)
    
    if status:
        query = query.where(WorkflowExecution.status == status)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    workflows = result.scalars().all()
    
    return {"items": workflows, "page": page, "page_size": page_size}


@router.get("/{workflow_id}", response_model=WorkflowResponse, summary="Get Workflow")
async def get_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed workflow execution information."""
    wf = await db.get(WorkflowExecution, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.patch("/{workflow_id}", response_model=WorkflowResponse, summary="Update Workflow")
async def update_workflow(
    workflow_id: int,
    update: WorkflowUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
):
    """
    Update workflow status (Manager/Admin only).
    Used for manual approval, rejection, or escalation.
    """
    wf = await db.get(WorkflowExecution, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    wf.status = WorkflowStatus(update.status)
    wf.approval_notes = update.notes
    wf.approved_by = current_user.id
    wf.updated_at = datetime.now(timezone.utc)
    
    if update.status in ["approved", "rejected"]:
        wf.resolved_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(wf)
    
    logger.info(f"Workflow {workflow_id} updated to {update.status} by {current_user.username}")
    return wf


@router.get("/document/{document_id}", response_model=WorkflowResponse, summary="Get Workflow by Document")
async def get_workflow_by_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the workflow execution for a specific document."""
    result = await db.execute(
        select(WorkflowExecution).where(WorkflowExecution.document_id == document_id)
    )
    wf = result.scalar_one_or_none()
    
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found for this document")
    
    return wf
