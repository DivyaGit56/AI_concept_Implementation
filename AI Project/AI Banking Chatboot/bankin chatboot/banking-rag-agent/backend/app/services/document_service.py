"""Document ingestion and indexing service."""

import os
import shutil
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.database.mongodb import get_collection
from app.rag.chunker import chunk_documents, clean_documents
from app.rag.loader import load_document, validate_document
from app.rag.vector_store import get_vector_store
from app.utils.helpers import generate_id, utc_now


async def ingest_document(
    file_path: str,
    filename: str,
    category: str,
    uploaded_by: Optional[str] = None,
) -> dict:
    settings = get_settings()
    validate_document(file_path, settings.max_upload_size_mb)

    doc_id = generate_id("doc_")
    dest_dir = Path(settings.upload_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{doc_id}_{filename}"
    shutil.copy2(file_path, dest_path)

    documents_col = get_collection("documents")
    record = {
        "_id": doc_id,
        "filename": filename,
        "category": category,
        "upload_date": utc_now(),
        "chunk_count": 0,
        "status": "processing",
        "file_path": str(dest_path),
        "file_size": os.path.getsize(dest_path),
        "uploaded_by": uploaded_by,
    }
    await documents_col.insert_one(record)

    try:
        raw_docs = load_document(str(dest_path))
        cleaned = clean_documents(raw_docs)
        if not cleaned:
            raise ValueError("Document contains no usable text after cleaning")

        for doc in cleaned:
            doc.metadata["category"] = category
            doc.metadata["document_id"] = doc_id

        chunks = chunk_documents(cleaned)
        vector_store = get_vector_store()
        chunk_count = vector_store.add_documents(chunks, doc_id)

        await documents_col.update_one(
            {"_id": doc_id},
            {"$set": {"chunk_count": chunk_count, "status": "indexed"}},
        )

        record["chunk_count"] = chunk_count
        record["status"] = "indexed"
        return record

    except Exception as exc:
        await documents_col.update_one(
            {"_id": doc_id},
            {"$set": {"status": "failed", "error": str(exc)}},
        )
        raise


async def delete_document(doc_id: str) -> bool:
    documents_col = get_collection("documents")
    doc = await documents_col.find_one({"_id": doc_id})
    if not doc:
        return False

    file_path = doc.get("file_path")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    get_vector_store().delete_by_document_id(doc_id)
    await documents_col.delete_one({"_id": doc_id})
    return True


async def reindex_document(doc_id: str) -> dict:
    documents_col = get_collection("documents")
    doc = await documents_col.find_one({"_id": doc_id})
    if not doc:
        raise ValueError("Document not found")

    file_path = doc.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise ValueError("Document file not found on disk")

    get_vector_store().delete_by_document_id(doc_id)

    raw_docs = load_document(file_path)
    cleaned = clean_documents(raw_docs)
    for d in cleaned:
        d.metadata["category"] = doc.get("category", "Other")
        d.metadata["document_id"] = doc_id

    chunks = chunk_documents(cleaned)
    chunk_count = get_vector_store().add_documents(chunks, doc_id)

    await documents_col.update_one(
        {"_id": doc_id},
        {"$set": {"chunk_count": chunk_count, "status": "indexed", "upload_date": utc_now()}},
    )
    doc["chunk_count"] = chunk_count
    doc["status"] = "indexed"
    return doc


async def list_documents() -> list:
    cursor = get_collection("documents").find().sort("upload_date", -1)
    return await cursor.to_list(length=500)
