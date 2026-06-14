"""Pydantic schemas for chat."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    document_ids: Optional[List[int]] = None


class ChatResponse(BaseModel):
    message_id: int
    session_id: int
    answer: str
    sources: List[dict]
    context_used: int


class SessionResponse(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
