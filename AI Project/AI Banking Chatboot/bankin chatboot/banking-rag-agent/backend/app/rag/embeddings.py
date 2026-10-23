"""HuggingFace embedding model wrapper."""

from functools import lru_cache
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings

from app.config import get_settings


@lru_cache
def get_embedding_model() -> HuggingFaceEmbeddings:
    settings = get_settings()
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    return model.embed_documents(texts)


def embed_query(query: str) -> List[float]:
    model = get_embedding_model()
    return model.embed_query(query)
