"""Document management API routes."""

import os
import tempfile
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.auth.dependencies import get_current_admin, get_current_user
from app.schemas.schemas import DocumentResponse, DocumentUploadResponse
from app.services.document_service import delete_document, ingest_document, list_documents, reindex_document

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(default="Other"),
    admin: dict = Depends(get_current_admin),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".pdf", ".txt"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF and TXT files are supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file uploaded")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await ingest_document(
            file_path=tmp_path,
            filename=file.filename,
            category=category,
            uploaded_by=admin["_id"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ingestion failed: {exc}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return DocumentUploadResponse(
        id=result["_id"],
        filename=result["filename"],
        category=result["category"],
        chunk_count=result.get("chunk_count", 0),
        status=result["status"],
        message="Document uploaded and indexed successfully",
    )


@router.get("", response_model=List[DocumentResponse])
async def get_documents(current_user: dict = Depends(get_current_user)):
    docs = await list_documents()
    return [
        DocumentResponse(
            id=d["_id"],
            filename=d["filename"],
            category=d.get("category", "Other"),
            upload_date=d["upload_date"],
            chunk_count=d.get("chunk_count", 0),
            status=d.get("status", "unknown"),
            file_size=d.get("file_size"),
        )
        for d in docs
    ]


@router.delete("/{doc_id}")
async def remove_document(doc_id: str, admin: dict = Depends(get_current_admin)):
    deleted = await delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"message": "Document deleted and removed from vector store"}


@router.post("/{doc_id}/reindex", response_model=DocumentUploadResponse)
async def reindex(doc_id: str, admin: dict = Depends(get_current_admin)):
    try:
        result = await reindex_document(doc_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return DocumentUploadResponse(
        id=result["_id"],
        filename=result["filename"],
        category=result.get("category", "Other"),
        chunk_count=result.get("chunk_count", 0),
        status=result.get("status", "indexed"),
        message="Document re-indexed successfully",
    )
