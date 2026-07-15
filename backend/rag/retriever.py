"""
RAG Retriever — semantic search over Qdrant vector store.
Combines vector similarity with optional keyword filtering.
"""
import logging
from typing import List, Dict, Any, Optional

from backend.config import settings
from backend.database.qdrant import search_vectors_async, get_async_client
from backend.rag.embeddings import embed_single

logger = logging.getLogger(__name__)


class RetrievedChunk:
    """A single retrieved document chunk with metadata."""

    def __init__(self, text: str, score: float, metadata: Dict[str, Any]):
        self.text = text
        self.score = score
        self.metadata = metadata
        self.document_id = metadata.get("document_id", "")
        self.filename = metadata.get("original_filename", "unknown")
        self.chunk_index = metadata.get("chunk_index", 0)

    def to_context_string(self) -> str:
        return (
            f"[Source: {self.filename} | Relevance: {self.score:.2f}]\n"
            f"{self.text}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "score": self.score,
            "document_id": self.document_id,
            "filename": self.filename,
            "chunk_index": self.chunk_index,
        }


async def retrieve_relevant_chunks(
    query: str,
    user_id: Optional[str] = None,
    top_k: int = 5,
    min_score: float = 0.3,
    collection_name: str = None,
) -> List[RetrievedChunk]:
    """
    Perform semantic search against Qdrant.
    Returns top-k chunks above the minimum similarity threshold.
    """
    collection_name = collection_name or settings.QDRANT_COLLECTION

    if not query.strip():
        return []

    # Embed the query
    query_vector = embed_single(query)

    try:
        results = await search_vectors_async(
            query_vector=query_vector,
            top_k=top_k,
            filter_user_id=user_id,
            collection_name=collection_name,
        )

        chunks = []
        for hit in results:
            if hit.score < min_score:
                continue
            payload = hit.payload or {}
            chunks.append(
                RetrievedChunk(
                    text=payload.get("text", ""),
                    score=hit.score,
                    metadata=payload,
                )
            )

        logger.info(f"Retrieved {len(chunks)} chunks for query: '{query[:50]}...'")
        return chunks

    except Exception as e:
        logger.error(f"Qdrant search failed: {e}")
        return []


async def build_rag_context(
    query: str,
    user_id: Optional[str] = None,
    top_k: int = 5,
    max_tokens: int = 3000,
) -> str:
    """
    Retrieve relevant chunks and format them into a single context string
    for injection into LLM prompts.
    """
    chunks = await retrieve_relevant_chunks(query=query, user_id=user_id, top_k=top_k)

    if not chunks:
        return "No relevant enterprise documents found for this query."

    context_parts = []
    total_chars = 0
    char_limit = max_tokens * 4  # Rough char-to-token estimate

    for i, chunk in enumerate(chunks):
        chunk_text = chunk.to_context_string()
        if total_chars + len(chunk_text) > char_limit:
            break
        context_parts.append(f"[Chunk {i+1}]\n{chunk_text}")
        total_chars += len(chunk_text)

    return "\n\n---\n\n".join(context_parts)


async def get_knowledge_base_stats(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Return stats about the user's knowledge base."""
    from backend.database.qdrant import get_collection_info_async
    info = await get_collection_info_async()
    return {
        "collection": info.get("name"),
        "total_vectors": info.get("vectors_count", 0),
        "status": info.get("status", "unknown"),
    }
