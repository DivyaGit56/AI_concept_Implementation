"""Admin analytics and feedback API routes."""

from collections import Counter
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_admin, get_current_user
from app.database.mongodb import get_collection
from app.rag.vector_store import get_vector_store
from app.schemas.schemas import AnalyticsResponse, FeedbackCreate, FeedbackResponse, HealthResponse
from app.utils.helpers import generate_id, utc_now

router = APIRouter(tags=["Admin & Feedback"])


@router.get("/admin/analytics", response_model=AnalyticsResponse)
async def analytics(admin: dict = Depends(get_current_admin)):
    db = get_collection("users").database

    total_users = await db["users"].count_documents({})
    total_sessions = await db["chat_sessions"].count_documents({})
    total_messages = await db["messages"].count_documents({})
    total_documents = await db["documents"].count_documents({})
    total_tickets = await db["support_tickets"].count_documents({})
    open_tickets = await db["support_tickets"].count_documents({"status": "open"})
    feedback_positive = await db["feedback"].count_documents({"rating": "up"})
    feedback_negative = await db["feedback"].count_documents({"rating": "down"})

    user_msgs = await db["messages"].find({"role": "user"}).sort("timestamp", -1).limit(500).to_list(500)
    questions = [m["content"][:100] for m in user_msgs]
    freq = Counter(questions).most_common(10)

    docs = await db["documents"].find().to_list(100)
    cat_counts = Counter(d.get("category", "Other") for d in docs)

    return AnalyticsResponse(
        total_users=total_users,
        total_sessions=total_sessions,
        total_messages=total_messages,
        total_documents=total_documents,
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        feedback_positive=feedback_positive,
        feedback_negative=feedback_negative,
        top_categories=[{"category": k, "count": v} for k, v in cat_counts.most_common()],
        frequent_questions=[{"question": q, "count": c} for q, c in freq],
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(payload: FeedbackCreate, current_user: dict = Depends(get_current_user)):
    message = await get_collection("messages").find_one({"_id": payload.message_id})
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    feedback_id = generate_id("fb_")
    record = {
        "_id": feedback_id,
        "message_id": payload.message_id,
        "user_id": current_user["_id"],
        "rating": payload.rating,
        "comment": payload.comment,
        "timestamp": utc_now(),
    }
    await get_collection("feedback").insert_one(record)
    await get_collection("messages").update_one(
        {"_id": payload.message_id},
        {"$set": {"feedback": payload.rating}},
    )

    return FeedbackResponse(
        id=feedback_id,
        message_id=payload.message_id,
        rating=payload.rating,
        comment=payload.comment,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    db_ok = "ok"
    try:
        await get_collection("users").database.command("ping")
    except Exception:
        db_ok = "error"

    vector_ok = "ok" if get_vector_store().health_check() else "error"

    from app.config import get_settings
    llm_ok = "configured" if get_settings().llm_api_key else "not_configured"

    overall = "healthy" if db_ok == "ok" and vector_ok == "ok" else "degraded"

    return HealthResponse(
        status=overall,
        database=db_ok,
        vector_store=vector_ok,
        llm=llm_ok,
    )
