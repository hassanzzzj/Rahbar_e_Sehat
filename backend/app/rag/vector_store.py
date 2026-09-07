"""
FAISS-backed vector store for clinical protocol retrieval.
Provides efficient similarity search over embedded documents.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.core.logging import get_logger

logger = get_logger(__name__)


class FAISSVectorStore:
    """In-memory FAISS index with disk persistence."""

    def __init__(self, dimension: int = 384, store_path: Optional[str] = None) -> None:
        """
        Initialize the vector store.

        Args:
            dimension: Embedding vector dimension (384 for MiniLM-L12-v2)
            store_path: Optional path for persisting the index to disk
        """
        self.dimension = dimension
        self.store_path = Path(store_path) if store_path else None
        self._index = None
        self._documents: List[Dict] = []  # Parallel list of document metadata
        self._load_faiss()

    def _load_faiss(self) -> None:
        """Load FAISS library (lazy import to handle environments without it)."""
        try:
            import faiss
            self._faiss = faiss
            self._index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine with normalized vectors)
            logger.info("vector_store.faiss_loaded", dimension=self.dimension)
        except ImportError:
            logger.warning("vector_store.faiss_not_available")
            self._faiss = None

    def add_documents(
        self, embeddings: List[List[float]], documents: List[Dict]
    ) -> int:
        """
        Add documents to the vector store.

        Args:
            embeddings: List of embedding vectors
            documents: List of document dicts with 'content' and 'metadata' keys

        Returns:
            Number of documents added
        """
        if self._index is None:
            logger.error("vector_store.not_initialized")
            return 0

        if len(embeddings) != len(documents):
            raise ValueError("Embeddings and documents must have the same length")

        # Normalize embeddings for cosine similarity
        vectors = np.array(embeddings, dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        normalized = vectors / (norms + 1e-10)

        self._index.add(normalized)
        self._documents.extend(documents)

        logger.info("vector_store.documents_added", count=len(documents))
        return len(documents)

    def search(
        self, query_embedding: List[float], top_k: int = 3
    ) -> List[Tuple[Dict, float]]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return

        Returns:
            List of (document, score) tuples sorted by similarity
        """
        if self._index is None or self._index.ntotal == 0:
            return []

        # Normalize query vector
        query = np.array([query_embedding], dtype=np.float32)
        norm = np.linalg.norm(query, axis=1, keepdims=True)
        normalized_query = query / (norm + 1e-10)

        # Search
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(normalized_query, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self._documents):
                results.append((self._documents[idx], float(score)))

        return results

    def save(self) -> None:
        """Persist the index and documents to disk."""
        if self.store_path is None or self._index is None:
            return

        self.store_path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_path = self.store_path / "index.faiss"
        self._faiss.write_index(self._index, str(index_path))

        # Save documents as JSON
        docs_path = self.store_path / "documents.json"
        with open(docs_path, "w", encoding="utf-8") as f:
            json.dump(self._documents, f, ensure_ascii=False, indent=2)

        logger.info("vector_store.saved", path=str(self.store_path))

    def load(self) -> bool:
        """Load the index and documents from disk."""
        if self.store_path is None or not self.store_path.exists():
            return False

        if self._faiss is None:
            return False

        index_path = self.store_path / "index.faiss"
        docs_path = self.store_path / "documents.json"

        if not index_path.exists() or not docs_path.exists():
            return False

        self._index = self._faiss.read_index(str(index_path))
        with open(docs_path, "r", encoding="utf-8") as f:
            self._documents = json.load(f)

        logger.info(
            "vector_store.loaded",
            path=str(self.store_path),
            document_count=len(self._documents),
        )
        return True

    @property
    def document_count(self) -> int:
        """Return the number of documents in the store."""
        return len(self._documents)
