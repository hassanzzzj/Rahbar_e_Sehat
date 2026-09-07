"""
RAG document ingestion pipeline.
Loads clinical protocols and facility data into the vector store.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from app.core.logging import get_logger
from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import FAISSVectorStore

logger = get_logger(__name__)

# Chunking configuration
CHUNK_SIZE = 500  # characters per chunk
CHUNK_OVERLAP = 50  # characters of overlap between chunks


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks for embedding.

    Args:
        text: Input text to chunk
        chunk_size: Target size per chunk in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence boundary
        if end < len(text):
            # Look for sentence-ending punctuation within the last 100 chars
            search_region = text[max(start, end - 100):end]
            sentence_breaks = [i for i, c in enumerate(search_region) if c in '.!?\n']
            if sentence_breaks:
                # Use the last sentence break
                end = max(start, end - 100) + sentence_breaks[-1] + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap
        if start >= len(text):
            break

    return chunks


def _load_document(file_path: Path) -> Optional[Dict]:
    """
    Load a single document from disk.

    Args:
        file_path: Path to the document file

    Returns:
        Document dict with content and metadata, or None if unsupported
    """
    suffix = file_path.suffix.lower()

    if suffix in {'.md', '.txt'}:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract metadata from filename or frontmatter
        metadata = {
            'source': file_path.name,
            'protocol_type': _infer_protocol_type(file_path.name),
        }

        return {'content': content, 'metadata': metadata}

    logger.warning("ingestion.unsupported_format", file=str(file_path))
    return None


def _infer_protocol_type(filename: str) -> str:
    """
    Infer the protocol type from the filename.

    Args:
        filename: Document filename

    Returns:
        Protocol type string
    """
    name_lower = filename.lower()
    if 'emergency' in name_lower or 'urgent' in name_lower:
        return 'emergency'
    elif 'triage' in name_lower:
        return 'triage'
    elif 'pediatric' in name_lower or 'child' in name_lower:
        return 'pediatric'
    elif 'pregnancy' in name_lower or 'maternal' in name_lower:
        return 'maternal'
    elif 'chronic' in name_lower:
        return 'chronic'
    return 'general'


def ingest_clinical_protocols(
    source_dir: str,
    vector_store: Optional[FAISSVectorStore] = None,
    embedding_model: Optional[EmbeddingModel] = None,
) -> int:
    """
    Ingest clinical protocol documents into the vector store.

    Args:
        source_dir: Directory containing protocol documents (.md or .txt)
        vector_store: Optional vector store instance (creates new if None)
        embedding_model: Optional embedding model instance

    Returns:
        Number of document chunks ingested
    """
    source_path = Path(source_dir)
    if not source_path.exists() or not source_path.is_dir():
        logger.error("ingestion.invalid_source_dir", path=source_dir)
        return 0

    store = vector_store or FAISSVectorStore()
    embedder = embedding_model or EmbeddingModel()

    # Find all document files
    files = [
        f for f in source_path.iterdir()
        if f.is_file() and f.suffix.lower() in {'.md', '.txt'}
    ]

    if not files:
        logger.warning("ingestion.no_documents_found", path=source_dir)
        return 0

    total_chunks = 0

    for file_path in files:
        doc = _load_document(file_path)
        if not doc:
            continue

        # Chunk the document
        chunks = _chunk_text(doc['content'])
        if not chunks:
            logger.warning("ingestion.empty_document", file=file_path.name)
            continue

        # Generate embeddings for chunks
        embeddings = embedder.embed_batch(chunks)
        if not embeddings or any(not e for e in embeddings):
            logger.error("ingestion.embedding_failed", file=file_path.name)
            continue

        # Create document entries with chunk metadata
        documents = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            doc_entry = {
                'content': chunk,
                'metadata': {
                    **doc['metadata'],
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                },
            }
            documents.append(doc_entry)

        # Add to vector store
        count = store.add_documents(embeddings, documents)
        total_chunks += count

        logger.info(
            "ingestion.document_processed",
            file=file_path.name,
            chunks=count,
        )

    # Persist the vector store
    store.save()

    logger.info("ingestion.complete", total_chunks=total_chunks)
    return total_chunks


def ingest_facility_data(facility_file: str) -> int:
    """
    Ingest facility directory data from a JSON file.

    Args:
        facility_file: Path to facility data JSON file

    Returns:
        Number of facility records ingested
    """
    import json

    file_path = Path(facility_file)
    if not file_path.exists():
        logger.error("ingestion.facility_file_not_found", path=facility_file)
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        logger.error("ingestion.facility_invalid_format", path=facility_file)
        return 0

    logger.info("ingestion.facility_data_loaded", count=len(data), path=facility_file)
    return len(data)
