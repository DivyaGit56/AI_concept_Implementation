"""Chat API routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.schemas.schemas import ChatRequest, ChatResponse, ChatSessionResponse, MessageResponse, SourceCitation
from app.services.chat_service import (
    clear_session,
    get_session_history,
    handle_chat,
    list_user_sessions,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, current_user: dict = Depends(get_current_user)):
    if not payload.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    try:
        result = await handle_chat(
            user_id=current_user["_id"],
            user_email=current_user["email"],
            message=payload.message.strip(),
            session_id=payload.session_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Chat service temporarily unavailable: {exc}",
        )

    return ChatResponse(
        session_id=result["session_id"],
        message_id=result["message_id"],
        answer=result["answer"],
        sources=[SourceCitation(**s) if isinstance(s, dict) else s for s in result["sources"]],
        query_category=result.get("query_category"),
        route=result.get("route", "rag"),
        confidence=result.get("confidence"),
    )


@router.get("/history", response_model=List[ChatSessionResponse])
async def chat_history(current_user: dict = Depends(get_current_user)):
    sessions = await list_user_sessions(current_user["_id"])
    return [
        ChatSessionResponse(
            id=s["_id"],
            title=s.get("title", "Conversation"),
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            message_count=s.get("message_count", 0),
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def session_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    from app.database.mongodb import get_collection

    session = await get_collection("chat_sessions").find_one(
        {"_id": session_id, "user_id": current_user["_id"]}
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    messages = await get_session_history(session_id)
    return [
        MessageResponse(
            id=m["_id"],
            role=m["role"],
            content=m["content"],
            sources=[SourceCitation(**s) for s in m.get("sources", [])],
            timestamp=m["timestamp"],
            feedback=m.get("feedback"),
        )
        for m in messages
    ]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    deleted = await clear_session(session_id, current_user["_id"])
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"message": "Session cleared successfully"}
