"""RAG (Retrieval-Augmented Generation) modules."""

from app.rag.embeddings import EmbeddingModel
from app.rag.ingestion import ingest_clinical_protocols
from app.rag.retriever import RAGRetriever
from app.rag.vector_store import FAISSVectorStore

__all__ = [
    "EmbeddingModel",
    "FAISSVectorStore",
    "RAGRetriever",
    "ingest_clinical_protocols",
]
