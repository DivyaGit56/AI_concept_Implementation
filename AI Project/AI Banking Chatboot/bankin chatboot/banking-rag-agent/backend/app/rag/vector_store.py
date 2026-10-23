"""ChromaDB vector store management."""

import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from app.config import get_settings
from app.rag.embeddings import get_embedding_model


class VectorStoreManager:
    def __init__(self) -> None:
        settings = get_settings()
        os.makedirs(settings.vector_store_path, exist_ok=True)
        self.collection_name = "banking_documents"
        self._store: Optional[Chroma] = None

    @property
    def store(self) -> Chroma:
        if self._store is None:
            settings = get_settings()
            self._store = Chroma(
                collection_name=self.collection_name,
                embedding_function=get_embedding_model(),
                persist_directory=settings.vector_store_path,
                client_settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._store

    def add_documents(self, documents: List[Document], doc_id: str) -> int:
        if not documents:
            return 0

        ids = [f"{doc_id}_chunk_{doc.metadata.get('chunk_index', i)}" for i, doc in enumerate(documents)]
        for doc in documents:
            doc.metadata["document_id"] = doc_id

        self.store.add_documents(documents=documents, ids=ids)
        return len(documents)

    def similarity_search(
        self,
        query: str,
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        if filter_dict:
            return self.store.similarity_search(query, k=k, filter=filter_dict)
        return self.store.similarity_search(query, k=k)

    def similarity_search_with_scores(
        self,
        query: str,
        k: int = 10,
    ) -> List[tuple[Document, float]]:
        return self.store.similarity_search_with_score(query, k=k)

    def delete_by_document_id(self, doc_id: str) -> None:
        client = chromadb.PersistentClient(
            path=get_settings().vector_store_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        collection = client.get_or_create_collection(self.collection_name)
        results = collection.get(where={"document_id": doc_id})
        if results and results.get("ids"):
            collection.delete(ids=results["ids"])

    def get_document_count(self) -> int:
        try:
            client = chromadb.PersistentClient(
                path=get_settings().vector_store_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            collection = client.get_or_create_collection(self.collection_name)
            return collection.count()
        except Exception:
            return 0

    def health_check(self) -> bool:
        try:
            self.get_document_count()
            return True
        except Exception:
            return False


_vector_store: Optional[VectorStoreManager] = None


def get_vector_store() -> VectorStoreManager:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager()
    return _vector_store
