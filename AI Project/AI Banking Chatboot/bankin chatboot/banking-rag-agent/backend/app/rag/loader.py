"""Document loading for PDF and TXT files."""

import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document


def load_document(file_path: str) -> List[Document]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    ext = path.suffix.lower()
    if ext == ".pdf":
        loader = PyPDFLoader(str(path))
        documents = loader.load()
    elif ext == ".txt":
        loader = TextLoader(str(path), encoding="utf-8")
        documents = loader.load()
    else:
        raise ValueError(f"Unsupported file type: {ext}. Only PDF and TXT are supported.")

    if not documents:
        raise ValueError(f"Document is empty or could not be parsed: {file_path}")

    for doc in documents:
        doc.metadata["source"] = path.name
        doc.metadata["filename"] = path.name
        if "page" not in doc.metadata and ext == ".pdf":
            doc.metadata.setdefault("page", 0)

    return documents


def validate_document(file_path: str, max_size_mb: int = 20) -> None:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError("File not found")

    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(f"File exceeds maximum size of {max_size_mb}MB")

    ext = path.suffix.lower()
    if ext not in {".pdf", ".txt"}:
        raise ValueError("Only PDF and TXT files are supported")
