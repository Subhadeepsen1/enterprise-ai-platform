"""Document database model."""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey,
    Integer, JSON, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class DocumentType(str, enum.Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    REPORT = "report"
    POLICY = "policy"
    PURCHASE_ORDER = "purchase_order"
    UNKNOWN = "unknown"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Classification
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType), default=DocumentType.UNKNOWN, nullable=False
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False
    )

    # Extracted content
    raw_text: Mapped[str] = mapped_column(Text, nullable=True)
    cleaned_text: Mapped[str] = mapped_column(Text, nullable=True)
    extracted_entities: Mapped[dict] = mapped_column(JSON, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)

    # AI Scores
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=True)
    risk_factors: Mapped[list] = mapped_column(JSON, nullable=True)

    # Vector store reference
    vector_store_id: Mapped[str] = mapped_column(String(255), nullable=True)
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    uploaded_by_user: Mapped["User"] = relationship("User", back_populates="documents")
    workflow: Mapped["WorkflowExecution"] = relationship("WorkflowExecution", back_populates="document", uselist=False)

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.original_filename}, type={self.document_type})>"
