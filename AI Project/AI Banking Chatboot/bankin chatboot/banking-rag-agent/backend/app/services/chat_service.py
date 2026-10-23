"""Chat session and message management."""

from typing import List, Optional

from app.agents.orchestrator import process_query
from app.database.mongodb import get_collection
from app.schemas.schemas import SourceCitation
from app.utils.helpers import generate_id, truncate_text, utc_now


async def get_or_create_session(user_id: str, session_id: Optional[str] = None) -> dict:
    sessions = get_collection("chat_sessions")
    if session_id:
        session = await sessions.find_one({"_id": session_id, "user_id": user_id})
        if session:
            return session

    new_session = {
        "_id": generate_id("sess_"),
        "user_id": user_id,
        "title": "New Conversation",
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    await sessions.insert_one(new_session)
    return new_session


async def get_session_history(session_id: str, limit: int = 20) -> List[dict]:
    cursor = (
        get_collection("messages")
        .find({"session_id": session_id})
        .sort("timestamp", 1)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)


async def save_message(
    session_id: str,
    role: str,
    content: str,
    sources: Optional[List[SourceCitation]] = None,
) -> dict:
    message = {
        "_id": generate_id("msg_"),
        "session_id": session_id,
        "role": role,
        "content": content,
        "sources": [s.model_dump() for s in (sources or [])],
        "timestamp": utc_now(),
        "feedback": None,
    }
    await get_collection("messages").insert_one(message)

    if role == "user":
        await get_collection("chat_sessions").update_one(
            {"_id": session_id},
            {
                "$set": {
                    "title": truncate_text(content, 60),
                    "updated_at": utc_now(),
                }
            },
        )
    else:
        await get_collection("chat_sessions").update_one(
            {"_id": session_id},
            {"$set": {"updated_at": utc_now()}},
        )

    return message


async def handle_chat(
    user_id: str,
    user_email: str,
    message: str,
    session_id: Optional[str] = None,
) -> dict:
    session = await get_or_create_session(user_id, session_id)
    history = await get_session_history(session["_id"])

    await save_message(session["_id"], "user", message)

    history_for_rewrite = [{"role": m["role"], "content": m["content"]} for m in history]
    history_for_rewrite.append({"role": "user", "content": message})

    answer, sources, route, category, confidence = await process_query(
        message, user_email, history_for_rewrite
    )

    ai_message = await save_message(session["_id"], "assistant", answer, sources)

    return {
        "session_id": session["_id"],
        "message_id": ai_message["_id"],
        "answer": answer,
        "sources": sources,
        "query_category": category,
        "route": route,
        "confidence": confidence,
    }


async def list_user_sessions(user_id: str) -> List[dict]:
    sessions_col = get_collection("chat_sessions")
    messages_col = get_collection("messages")

    cursor = sessions_col.find({"user_id": user_id}).sort("updated_at", -1)
    sessions = await cursor.to_list(length=100)

    for session in sessions:
        count = await messages_col.count_documents({"session_id": session["_id"]})
        session["message_count"] = count

    return sessions


async def clear_session(session_id: str, user_id: str) -> bool:
    session = await get_collection("chat_sessions").find_one(
        {"_id": session_id, "user_id": user_id}
    )
    if not session:
        return False
    await get_collection("messages").delete_many({"session_id": session_id})
    await get_collection("chat_sessions").delete_one({"_id": session_id})
    return True
