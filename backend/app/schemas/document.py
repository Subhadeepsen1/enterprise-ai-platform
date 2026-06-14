"""Pydantic schemas for documents."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.document import DocumentType, DocumentStatus


class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    file_size: int
    mime_type: str
    document_type: DocumentType
    status: DocumentStatus
    summary: Optional[str]
    extracted_entities: Optional[dict]
    confidence_score: Optional[float]
    risk_score: Optional[float]
    risk_level: Optional[str]
    risk_factors: Optional[list]
    is_indexed: bool
    uploaded_by: int
    created_at: datetime
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
