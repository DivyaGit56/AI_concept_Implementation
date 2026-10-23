"""RAG retrieval pipeline with reranking and threshold filtering."""

from dataclasses import dataclass
from typing import List, Optional

from langchain_core.documents import Document

from app.config import get_settings
from app.rag.reranker import rerank_documents
from app.rag.vector_store import get_vector_store
from app.schemas.schemas import QueryCategory, SourceCitation


@dataclass
class RetrievalResult:
    documents: List[Document]
    scores: List[float]
    sources: List[SourceCitation]
    sufficient: bool
    avg_score: float


CATEGORY_FILTER_MAP = {
    QueryCategory.KYC: {"category": "KYC"},
    QueryCategory.LOAN: {"category": "Loan"},
    QueryCategory.CREDIT_CARD: {"category": "Credit Card"},
    QueryCategory.DEBIT_CARD: {"category": "Debit Card"},
    QueryCategory.BANKING_CHARGES: {"category": "Banking Charges"},
    QueryCategory.FUND_TRANSFER: {"category": "Fund Transfer"},
    QueryCategory.INTEREST_RATES: {"category": "Interest Rates"},
    QueryCategory.COMPLAINTS: {"category": "Complaints"},
    QueryCategory.ACCOUNT: {"category": "Account"},
}


def _doc_to_source(doc: Document, score: float) -> SourceCitation:
    meta = doc.metadata or {}
    page = meta.get("page")
    if page is not None:
        try:
            page = int(page) + 1
        except (TypeError, ValueError):
            page = None
    return SourceCitation(
        filename=meta.get("filename") or meta.get("source") or "Unknown",
        section=meta.get("section"),
        page=page,
        relevance_score=round(float(score), 4),
    )


def retrieve_context(
    query: str,
    category: Optional[QueryCategory] = None,
) -> RetrievalResult:
    settings = get_settings()
    vector_store = get_vector_store()

    filter_dict = None
    if category and category in CATEGORY_FILTER_MAP:
        filter_dict = CATEGORY_FILTER_MAP[category]

    try:
        if filter_dict:
            raw_docs = vector_store.similarity_search(
                query, k=settings.top_k_retrieval, filter_dict=filter_dict
            )
            if len(raw_docs) < 2:
                raw_docs = vector_store.similarity_search(query, k=settings.top_k_retrieval)
        else:
            raw_docs = vector_store.similarity_search(query, k=settings.top_k_retrieval)
    except Exception:
        raw_docs = vector_store.similarity_search(query, k=settings.top_k_retrieval)

    if not raw_docs:
        return RetrievalResult([], [], [], False, 0.0)

    reranked = rerank_documents(query, raw_docs, top_k=settings.top_k_rerank)
    docs = [doc for doc, _ in reranked]
    scores = [float(score) for _, score in reranked]

    best_score = max(scores) if scores else 0.0
    normalized_best = _normalize_score(best_score)
    sufficient = normalized_best >= settings.relevance_threshold and len(docs) > 0
    sources = [_doc_to_source(doc, score) for doc, score in reranked]

    return RetrievalResult(
        documents=docs,
        scores=scores,
        sources=sources,
        sufficient=sufficient,
        avg_score=normalized_best,
    )


def _normalize_score(score: float) -> float:
    import math
    return 1 / (1 + math.exp(-score))
