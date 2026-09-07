"""
Embedding model interface for RAG vector store.
Provides consistent embedding generation for documents and queries.
"""

from typing import List

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingModel:
    """Generates embeddings for text using sentence-transformers."""

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2") -> None:
        self.model_name = model_name
        self._model = None  # Lazy load

    def _load_model(self) -> None:
        """Load the embedding model (lazy initialization)."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                logger.warning("embeddings.model_not_available", model=self.model_name)

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        self._load_model()
        if self._model is None:
            return []
        embedding = self._model.encode([text])[0]
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        self._load_model()
        if self._model is None:
            return [[] for _ in texts]
        embeddings = self._model.encode(texts)
        return [e.tolist() for e in embeddings]
