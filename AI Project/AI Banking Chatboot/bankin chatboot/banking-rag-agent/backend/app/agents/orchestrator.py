"""AI agent orchestrator: routes queries to RAG or banking tools."""

import re
from typing import List, Optional, Tuple

from app.agents.tools import (
    create_support_ticket,
    get_account_balance,
    get_customer_profile,
    get_loan_status,
    get_recent_transactions,
)
from app.rag.generator import format_sources, generate_answer
from app.rag.query_classifier import classify_query
from app.rag.query_rewriter import rewrite_query
from app.rag.retriever import retrieve_context
from app.schemas.schemas import QueryCategory, SourceCitation


TOOL_PATTERNS = {
    "balance": [r"my balance", r"account balance", r"how much.*account", r"available balance"],
    "transactions": [r"my transaction", r"recent transaction", r"transaction history", r"last transaction"],
    "profile": [r"my profile", r"customer profile", r"my details", r"my information"],
    "loan_status": [r"my loan", r"loan status", r"emi status", r"outstanding loan"],
    "ticket": [r"create ticket", r"raise ticket", r"support ticket", r"not resolved", r"still not working"],
}


def _detect_tool(query: str) -> Optional[str]:
    q = query.lower()
    for tool, patterns in TOOL_PATTERNS.items():
        if any(re.search(p, q) for p in patterns):
            return tool
    return None


async def process_query(
    query: str,
    user_email: str,
    history: Optional[List[dict]] = None,
    force_rag: bool = False,
) -> Tuple[str, List[SourceCitation], str, str, float]:
    rewritten = await rewrite_query(query, history)
    category, cat_confidence = classify_query(rewritten)

    if not force_rag and category == QueryCategory.ACCOUNT_DATA:
        tool = _detect_tool(rewritten)
        if tool == "balance":
            return get_account_balance(user_email), [], "tool", "balance", cat_confidence
        if tool == "transactions":
            return get_recent_transactions(user_email), [], "tool", "transactions", cat_confidence
        if tool == "profile":
            return get_customer_profile(user_email), [], "tool", "profile", cat_confidence
        if tool == "loan_status":
            return get_loan_status(user_email), [], "tool", "loan_status", cat_confidence

    retrieval = retrieve_context(rewritten, category if category != QueryCategory.ACCOUNT_DATA else None)
    answer, grounded = await generate_answer(rewritten, retrieval.documents, retrieval.sufficient)
    sources = format_sources(retrieval.sources) if grounded else []

    tool = _detect_tool(rewritten)
    if tool == "ticket" or _needs_ticket_creation(query, answer):
        ticket = create_support_ticket(user_email, query, category.value if category else "General")
        answer += (
            f"\n\nYour support request has been created successfully.\n"
            f"**Ticket ID: {ticket['ticket_id']}**"
        )

    return answer, sources, "rag", category.value, retrieval.avg_score


def _needs_ticket_creation(query: str, answer: str) -> bool:
    q = query.lower()
    unresolved = any(w in q for w in ["not working", "still facing", "not resolved", "help me"])
    troubleshooting = "step" in answer.lower() or "try" in answer.lower()
    return unresolved and troubleshooting
