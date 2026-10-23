"""Conversational query rewriting using chat history."""

from typing import List, Optional

import httpx

from app.config import get_settings


REWRITE_PROMPT = """You are a query rewriting assistant for a banking chatbot.
Given the conversation history and the latest user message, rewrite the latest message
into a standalone search query that preserves full context.

Rules:
- If the latest message is already standalone, return it unchanged.
- Resolve pronouns (it, that, this) using conversation history.
- Keep banking terminology accurate.
- Return ONLY the rewritten query, nothing else.

Conversation history:
{history}

Latest user message: {query}

Rewritten query:"""


async def rewrite_query(
    query: str,
    history: Optional[List[dict]] = None,
) -> str:
    if not history or len(history) < 2:
        return query

    history_text = ""
    for msg in history[-6:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_text += f"{role.capitalize()}: {content}\n"

    pronoun_patterns = [" it", " that", " this", " them", " those", " same"]
    needs_rewrite = any(p in query.lower() for p in pronoun_patterns) or len(query.split()) < 6

    if not needs_rewrite:
        return query

    settings = get_settings()
    if not settings.llm_api_key:
        return _rule_based_rewrite(query, history)

    prompt = REWRITE_PROMPT.format(history=history_text.strip(), query=query)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 150,
                },
            )
            response.raise_for_status()
            data = response.json()
            rewritten = data["choices"][0]["message"]["content"].strip()
            return rewritten if rewritten else query
    except Exception:
        return _rule_based_rewrite(query, history)


def _rule_based_rewrite(query: str, history: List[dict]) -> str:
    last_user_msgs = [m["content"] for m in history if m.get("role") == "user"]
    if not last_user_msgs:
        return query

    prev = last_user_msgs[-2] if len(last_user_msgs) >= 2 else last_user_msgs[-1]
    query_lower = query.lower()

    if any(w in query_lower for w in ["it", "that", "this", "same"]):
        if "loan" in prev.lower():
            if "document" in query_lower:
                if "home" in prev.lower():
                    return "What documents are required for a home loan?"
                if "personal" in prev.lower():
                    return "What documents are required for a personal loan?"
                if "education" in prev.lower():
                    return "What documents are required for an education loan?"
                return f"What documents are required? Context: {prev}"
            if "eligibility" in query_lower or "eligible" in query_lower:
                return f"What is the eligibility criteria? Context: {prev}"
        return f"{query} (regarding: {prev})"

    return query
