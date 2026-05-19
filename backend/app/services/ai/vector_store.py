"""Qdrant client + helpers for the policy_chunks collection."""
from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.config import settings
from app.core.logging import get_logger
from app.services.ai.embeddings import embed, get_embedder

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_qdrant() -> QdrantClient:
    logger.info("qdrant.connecting", url=settings.qdrant_url)
    return QdrantClient(url=settings.qdrant_url)


def ensure_collection(name: str | None = None) -> str:
    """Create the policy_chunks collection if missing. Returns the name used."""
    name = name or settings.qdrant_collection
    client = get_qdrant()
    existing = {c.name for c in client.get_collections().collections}
    if name not in existing:
        dim = get_embedder().get_sentence_embedding_dimension()
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        logger.info("qdrant.collection.created", name=name, dim=dim)
    return name


def upsert_chunks(
    chunks: list[dict[str, Any]],
    *,
    text_key: str = "text",
    collection: str | None = None,
) -> int:
    """Embed and upsert chunks. Each chunk dict becomes the payload.

    Required key: `text_key`. All other keys are stored as payload metadata
    (e.g. policy_id, section, page).
    """
    if not chunks:
        return 0
    name = ensure_collection(collection)
    texts = [c[text_key] for c in chunks]
    vectors = embed(texts)

    points = [
        PointStruct(id=str(uuid.uuid4()), vector=vec, payload=chunk)
        for vec, chunk in zip(vectors, chunks, strict=True)
    ]
    get_qdrant().upsert(collection_name=name, points=points)
    logger.info("qdrant.upserted", collection=name, count=len(points))
    return len(points)


def search(
    query: str,
    *,
    top_k: int = 20,
    filter_eq: dict[str, Any] | None = None,
    collection: str | None = None,
) -> list[dict[str, Any]]:
    """Embed `query`, search Qdrant, return [{score, payload}]."""
    name = collection or settings.qdrant_collection
    vec = embed([query])[0]
    qfilter = None
    if filter_eq:
        qfilter = Filter(
            must=[
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_eq.items()
            ]
        )

    hits = get_qdrant().search(
        collection_name=name,
        query_vector=vec,
        limit=top_k,
        query_filter=qfilter,
    )
    return [{"score": h.score, "payload": h.payload} for h in hits]


__all__ = ["get_qdrant", "ensure_collection", "upsert_chunks", "search"]
