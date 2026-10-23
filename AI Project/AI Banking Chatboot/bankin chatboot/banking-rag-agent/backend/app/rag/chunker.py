"""Text cleaning and chunking for RAG."""

import re
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.utils.helpers import clean_text


def clean_documents(documents: List[Document]) -> List[Document]:
    cleaned = []
    for doc in documents:
        content = clean_text(doc.page_content)
        if len(content) < 20:
            continue
        cleaned.append(
            Document(page_content=content, metadata=dict(doc.metadata))
        )
    return cleaned


def extract_section(text: str) -> str | None:
    patterns = [
        r"(?:^|\n)([A-Z][A-Za-z\s&/-]{3,50})(?:\n|$)",
        r"(?:Section|SECTION)\s*[:.]?\s*(.+?)(?:\n|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text[:500])
        if match:
            section = match.group(1).strip()
            if 3 < len(section) < 60:
                return section
    return None


def chunk_documents(documents: List[Document]) -> List[Document]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks = splitter.split_documents(documents)
    enriched = []
    for i, chunk in enumerate(chunks):
        metadata = dict(chunk.metadata)
        metadata["chunk_index"] = i
        section = extract_section(chunk.page_content)
        if section:
            metadata["section"] = section
        enriched.append(Document(page_content=chunk.page_content, metadata=metadata))
    return enriched
