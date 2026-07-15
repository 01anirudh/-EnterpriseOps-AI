"""
Qdrant vector database client wrapper.
Handles collection management, upsert, and semantic search.
"""
import uuid
import logging
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct,
    Filter, FieldCondition, MatchValue,
    SearchRequest, ScoredPoint
)

from backend.config import settings

logger = logging.getLogger(__name__)

# Sync client for background workers
sync_client: Optional[QdrantClient] = None
# Async client for FastAPI
async_client: Optional[AsyncQdrantClient] = None


def get_sync_client() -> QdrantClient:
    global sync_client
    if sync_client is None:
        sync_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
    return sync_client


def get_async_client() -> AsyncQdrantClient:
    global async_client
    if async_client is None:
        async_client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
    return async_client


def ensure_collection_sync(collection_name: str = None) -> bool:
    """Create the vector collection if it does not exist (sync)."""
    collection_name = collection_name or settings.QDRANT_COLLECTION
    client = get_sync_client()
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIMENSION,
                distance=Distance.COSINE,
            ),
        )
        logger.info(f"Created Qdrant collection: {collection_name}")
    return True


async def ensure_collection_async(collection_name: str = None) -> bool:
    """Create the vector collection if it does not exist (async)."""
    collection_name = collection_name or settings.QDRANT_COLLECTION
    client = get_async_client()
    response = await client.get_collections()
    existing = [c.name for c in response.collections]
    if collection_name not in existing:
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIMENSION,
                distance=Distance.COSINE,
            ),
        )
        logger.info(f"Created Qdrant collection: {collection_name}")
    return True


def upsert_vectors_sync(
    vectors: List[List[float]],
    payloads: List[Dict[str, Any]],
    collection_name: str = None,
) -> List[str]:
    """Upsert a batch of vectors with metadata payloads. Returns list of point IDs."""
    collection_name = collection_name or settings.QDRANT_COLLECTION
    client = get_sync_client()
    ensure_collection_sync(collection_name)

    point_ids = [str(uuid.uuid4()) for _ in vectors]
    points = [
        PointStruct(id=pid, vector=vec, payload=payload)
        for pid, vec, payload in zip(point_ids, vectors, payloads)
    ]
    client.upsert(collection_name=collection_name, points=points)
    logger.info(f"Upserted {len(points)} vectors to {collection_name}")
    return point_ids


async def search_vectors_async(
    query_vector: List[float],
    top_k: int = 5,
    filter_user_id: Optional[str] = None,
    collection_name: str = None,
) -> List[ScoredPoint]:
    """Semantic search: returns top-k matching document chunks."""
    collection_name = collection_name or settings.QDRANT_COLLECTION
    client = get_async_client()

    search_filter = None
    if filter_user_id:
        search_filter = Filter(
            must=[FieldCondition(key="user_id", match=MatchValue(value=filter_user_id))]
        )

    results = await client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        query_filter=search_filter,
        limit=top_k,
        with_payload=True,
    )
    return results


def delete_vectors_by_document_sync(document_id: str, collection_name: str = None):
    """Remove all vectors associated with a specific document."""
    collection_name = collection_name or settings.QDRANT_COLLECTION
    client = get_sync_client()
    client.delete(
        collection_name=collection_name,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
    )
    logger.info(f"Deleted vectors for document {document_id}")


async def get_collection_info_async(collection_name: str = None) -> Dict[str, Any]:
    """Return collection stats."""
    collection_name = collection_name or settings.QDRANT_COLLECTION
    client = get_async_client()
    try:
        info = await client.get_collection(collection_name)
        return {
            "name": collection_name,
            "vectors_count": info.vectors_count,
            "status": str(info.status),
        }
    except Exception:
        return {"name": collection_name, "vectors_count": 0, "status": "not_found"}
