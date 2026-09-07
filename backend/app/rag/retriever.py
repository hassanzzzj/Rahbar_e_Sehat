"""
RAG retriever for clinical protocols and facility data.
Provides semantic search over the vector store.
"""

from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import get_logger
from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import FAISSVectorStore

logger = get_logger(__name__)


class RAGRetriever:
    """Retrieves relevant documents from the vector store."""

    def __init__(
        self,
        vector_store: Optional[FAISSVectorStore] = None,
        embedding_model: Optional[EmbeddingModel] = None,
        facility_store: Optional[Any] = None,
    ) -> None:
        """
        Initialize the retriever.

        Args:
            vector_store: FAISS vector store instance
            embedding_model: Embedding model instance
            facility_store: Optional facility data store for geo-search
        """
        self._vector_store = vector_store or FAISSVectorStore()
        self._embedding_model = embedding_model or EmbeddingModel()
        self._facility_store = facility_store

    async def retrieve_clinical_protocols(
        self, query: str, top_k: int = 3
    ) -> List[Dict]:
        """
        Retrieve relevant clinical protocols for a given symptom query.

        Args:
            query: Symptom description or triage query
            top_k: Number of documents to retrieve

        Returns:
            List of retrieved documents with content, score, and metadata
        """
        if not query or not query.strip():
            logger.warning("retriever.empty_query")
            return []

        # Generate query embedding
        query_embedding = self._embedding_model.embed_text(query)
        if not query_embedding:
            logger.warning("retriever.embedding_failed")
            return []

        # Search the vector store
        results = self._vector_store.search(query_embedding, top_k=top_k)

        # Format results
        documents = []
        for doc, score in results:
            documents.append({
                "content": doc.get("content", ""),
                "score": score,
                "source": doc.get("metadata", {}).get("source", "unknown"),
                "protocol_type": doc.get("metadata", {}).get("protocol_type", "general"),
                "metadata": doc.get("metadata", {}),
            })

        logger.info(
            "retriever.protocols_retrieved",
            query_length=len(query),
            result_count=len(documents),
        )
        return documents

    async def retrieve_facilities(
        self,
        latitude: float,
        longitude: float,
        facility_type: Optional[str] = None,
        max_distance_km: float = 50.0,
    ) -> List[Dict]:
        """
        Retrieve nearby facilities based on location and requirements.

        Args:
            latitude: Patient latitude
            longitude: Patient longitude
            facility_type: Optional filter by facility type
            max_distance_km: Maximum search radius

        Returns:
            List of facility records sorted by distance
        """
        from app.agents.facility_matching_agent import haversine_km

        facilities = await self._facility_store.get_facilities() if self._facility_store else []
        if not facilities:
            logger.info("retriever.no_facilities_loaded")
            return []

        results: List[tuple[float, Dict]] = []
        for fac in facilities:
            fac_lat = fac.get("latitude")
            fac_lng = fac.get("longitude")
            if fac_lat is None or fac_lng is None:
                continue

            if facility_type and fac.get("facility_type") != facility_type:
                continue

            distance = haversine_km(latitude, longitude, fac_lat, fac_lng)
            if distance > max_distance_km:
                continue

            record = {**fac, "distance_km": round(distance, 2)}
            results.append((distance, record))

        results.sort(key=lambda x: x[0])

        logger.info(
            "retriever.facilities_found",
            lat=latitude,
            lng=longitude,
            result_count=len(results),
        )
        return [record for _, record in results]

    def get_vector_store(self) -> FAISSVectorStore:
        """Return the underlying vector store for direct access."""
        return self._vector_store

    def get_embedding_model(self) -> EmbeddingModel:
        """Return the embedding model for direct access."""
        return self._embedding_model
