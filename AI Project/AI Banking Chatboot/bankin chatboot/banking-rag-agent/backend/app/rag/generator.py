"""Grounded LLM answer generation with hallucination prevention."""

from typing import List, Optional, Tuple

import httpx
from langchain_core.documents import Document

from app.config import get_settings
from app.schemas.schemas import SourceCitation

NO_INFO_MESSAGE = "I couldn't find this information in the available banking documents."

SYSTEM_PROMPT = """You are a professional banking customer support assistant for DemoBank.
You MUST answer questions ONLY using the provided context from official banking documents.

STRICT RULES:
1. Use ONLY information explicitly stated in the context below.
2. NEVER invent interest rates, fees, loan limits, eligibility criteria, or regulations.
3. NEVER provide account balances, transaction details, or personal customer information.
4. If the context does not contain enough information to answer, respond EXACTLY with:
   "I couldn't find this information in the available banking documents."
5. Cite document names naturally in your answer (e.g., "According to the Personal Loan Policy...").
6. Be concise, professional, and helpful.
7. For troubleshooting, provide step-by-step guidance ONLY from the context.

Context from banking documents:
{context}"""

USER_PROMPT = """Customer question: {query}

Provide a helpful answer based ONLY on the context above. If insufficient context, use the exact fallback message."""


def build_context(documents: List[Document]) -> str:
    if not documents:
        return "No relevant documents found."

    parts = []
    for i, doc in enumerate(documents, 1):
        meta = doc.metadata or {}
        filename = meta.get("filename") or meta.get("source") or "Unknown"
        section = meta.get("section", "")
        page = meta.get("page")
        page_str = f", Page {int(page) + 1}" if page is not None else ""
        section_str = f", Section: {section}" if section else ""
        header = f"[Source {i}: {filename}{section_str}{page_str}]"
        parts.append(f"{header}\n{doc.page_content}")

    return "\n\n---\n\n".join(parts)


async def generate_answer(
    query: str,
    documents: List[Document],
    sufficient: bool,
) -> Tuple[str, bool]:
    if not sufficient or not documents:
        return NO_INFO_MESSAGE, False

    settings = get_settings()
    context = build_context(documents)

    if not settings.llm_api_key:
        return _fallback_answer(query, documents), True

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
                        {"role": "user", "content": USER_PROMPT.format(query=query)},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 800,
                },
            )
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip()

            if _is_hallucination_risk(answer, documents):
                return NO_INFO_MESSAGE, False

            return answer, True
    except Exception:
        return _fallback_answer(query, documents), True


def _fallback_answer(query: str, documents: List[Document]) -> str:
    if not documents:
        return NO_INFO_MESSAGE

    meta = documents[0].metadata or {}
    filename = meta.get("filename", "banking document")
    snippet = documents[0].page_content[:600].strip()
    return (
        f"According to {filename}, here is the relevant information:\n\n"
        f"{snippet}"
    )


def _is_hallucination_risk(answer: str, documents: List[Document]) -> bool:
    if NO_INFO_MESSAGE.lower() in answer.lower():
        return False

    context_text = " ".join(d.page_content.lower() for d in documents)
    suspicious_patterns = [
        r"\d+\.\d+%", r"rs\.?\s*\d+", r"inr\s*\d+",
    ]
    import re
    for pattern in suspicious_patterns:
        matches = re.findall(pattern, answer.lower())
        for match in matches:
            if match not in context_text:
                return True
    return False


def format_sources(sources: List[SourceCitation]) -> List[SourceCitation]:
    seen = set()
    unique = []
    for src in sources:
        key = (src.filename, src.page, src.section)
        if key not in seen:
            seen.add(key)
            unique.append(src)
    return unique
