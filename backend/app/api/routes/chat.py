"""RAG Chat API routes."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, SessionResponse
from app.services.ai.rag_pipeline import rag_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/sessions", response_model=SessionResponse, summary="Create Chat Session")
async def create_session(
    title: str = "New Conversation",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new RAG chat session."""
    session = ChatSession(user_id=current_user.id, title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", summary="List Chat Sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all chat sessions for the current user."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(desc(ChatSession.updated_at))
        .limit(20)
    )
    sessions = result.scalars().all()
    return {"sessions": sessions}


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse, summary="Send Message")
async def send_message(
    session_id: int,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message and receive an AI response using RAG.
    
    The AI:
    1. Retrieves relevant document chunks
    2. Uses context to answer accurately
    3. Cites sources with relevance scores
    """
    # Verify session ownership
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    await db.flush()
    
    # Fetch conversation history for context
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .limit(10)
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in history_result.scalars().all()
    ]
    
    # RAG: Retrieve context
    contexts = rag_pipeline.retrieve_context(
        query=request.message,
        document_ids=request.document_ids,
    )
    
    # Generate answer
    result = rag_pipeline.generate_answer(
        query=request.message,
        contexts=contexts,
        conversation_history=history,
    )
    
    # Save AI response
    ai_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=result["answer"],
        sources=result["sources"],
    )
    db.add(ai_msg)
    
    # Update session title if first message
    if len(history) <= 1:
        session.title = request.message[:80]
    
    await db.commit()
    
    return {
        "message_id": ai_msg.id,
        "session_id": session_id,
        "answer": result["answer"],
        "sources": result["sources"],
        "context_used": result["context_used"],
    }


@router.get("/sessions/{session_id}/messages", summary="Get Messages")
async def get_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all messages in a chat session."""
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return {"messages": messages, "session": session}
