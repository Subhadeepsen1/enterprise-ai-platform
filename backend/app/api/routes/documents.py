"""Document processing API routes."""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.config import settings
from app.core.security import get_current_user, require_any_role
from app.db.database import get_db
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.user import User
from app.models.workflow_model import WorkflowExecution
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.services.document.processor import document_processor
from app.services.ai.rag_pipeline import rag_pipeline
from app.services.workflow.engine import workflow_engine

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
}


@router.post("/upload", response_model=DocumentResponse, summary="Upload & Process Document")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a business document for intelligent processing.
    
    Supported formats: PDF, DOCX, TXT
    
    Processing pipeline:
    1. File validation & storage
    2. Text extraction
    3. Document classification
    4. Entity extraction
    5. Risk analysis
    6. Vector indexing for RAG
    7. Workflow creation
    """
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' not supported. Use PDF, DOCX, or TXT.",
        )
    
    # Read and validate file size
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit",
        )
    
    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create document record
    doc = Document(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        status=DocumentStatus.PROCESSING,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    await db.flush()
    
    try:
        # === AI Processing Pipeline ===
        
        # 1. Extract text
        raw_text = document_processor.extract_text_from_file(file_path, file.content_type)
        cleaned_text = document_processor.clean_text(raw_text)
        
        # 2. Classify document
        doc_type, confidence = document_processor.classify_document(cleaned_text)
        
        # 3. Extract entities
        entities = document_processor.extract_entities(cleaned_text, doc_type)
        
        # 4. Risk analysis
        risk_data = document_processor.analyze_risk(cleaned_text, entities, doc_type)
        
        # 5. Generate summary
        summary = document_processor.generate_summary(cleaned_text, doc_type, entities)
        
        # 6. Update document record
        doc.raw_text = raw_text[:50000]  # Cap stored text
        doc.cleaned_text = cleaned_text[:50000]
        doc.document_type = DocumentType(doc_type)
        doc.confidence_score = confidence
        doc.extracted_entities = entities
        doc.risk_score = risk_data["risk_score"]
        doc.risk_level = risk_data["risk_level"]
        doc.risk_factors = risk_data["risk_factors"]
        doc.summary = summary
        doc.status = DocumentStatus.PROCESSED
        doc.processed_at = datetime.now(timezone.utc)
        
        # 7. Vector indexing for RAG
        try:
            vector_id = rag_pipeline.index_document(
                document_id=doc.id,
                text=cleaned_text,
                metadata={
                    "filename": file.filename,
                    "doc_type": doc_type,
                    "uploaded_by": str(current_user.id),
                },
            )
            doc.vector_store_id = vector_id
            doc.is_indexed = True
        except Exception as e:
            logger.warning(f"Vector indexing failed for doc {doc.id}: {e}")
        
        # 8. Create workflow
        missing_fields = workflow_engine.detect_missing_fields(doc_type, entities)
        wf_result = workflow_engine.generate_recommendation(
            risk_score=risk_data["risk_score"],
            risk_factors=risk_data["risk_factors"],
            doc_type=doc_type,
            entities=entities,
            missing_fields=missing_fields,
        )
        
        workflow = WorkflowExecution(
            document_id=doc.id,
            status=wf_result["workflow_status"],
            ai_recommendation=wf_result["recommendation"],
            risk_score=risk_data["risk_score"],
            confidence=wf_result["confidence"],
            missing_fields=missing_fields,
            action_items=wf_result["action_items"],
            recommendation_reason=wf_result["reason"],
        )
        db.add(workflow)
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        doc.status = DocumentStatus.FAILED
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document processing failed: {str(e)}",
        )
    
    await db.commit()
    await db.refresh(doc)
    
    logger.info(f"Document processed: {file.filename} | Type: {doc_type} | Risk: {risk_data['risk_score']}")
    return doc


@router.get("/", response_model=DocumentListResponse, summary="List Documents")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    doc_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents with pagination and filtering."""
    query = select(Document).order_by(desc(Document.created_at))
    
    # Non-admins see only their documents
    if current_user.role == "employee":
        query = query.where(Document.uploaded_by == current_user.id)
    
    if doc_type:
        query = query.where(Document.document_type == doc_type)
    if status:
        query = query.where(Document.status == status)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return {
        "items": documents,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{document_id}", response_model=DocumentResponse, summary="Get Document")
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed information about a specific document."""
    doc = await db.get(Document, document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if current_user.role == "employee" and doc.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return doc


@router.delete("/{document_id}", summary="Delete Document")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """Delete a document and its associated data."""
    doc = await db.get(Document, document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if current_user.role == "employee" and doc.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Remove file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    await db.delete(doc)
    await db.commit()
    
    return {"message": "Document deleted successfully"}
