"""Local embedding + reranker — Qwen3-Embedding-0.6B + bge-reranker-v2-m3.

Both are loaded lazily on first use and cached as module-level singletons.
"""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import CrossEncoder, SentenceTransformer

from app.core.logging import get_logger

logger = get_logger(__name__)

EMBED_MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    logger.info("embedder.loading", model=EMBED_MODEL_NAME)
    model = SentenceTransformer(EMBED_MODEL_NAME)
    logger.info("embedder.ready", dim=model.get_sentence_embedding_dimension())
    return model


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    logger.info("reranker.loading", model=RERANKER_MODEL_NAME)
    model = CrossEncoder(RERANKER_MODEL_NAME)
    logger.info("reranker.ready")
    return model


def embed(texts: list[str]) -> list[list[float]]:
    """Encode a list of texts. Returns dense vectors."""
    model = get_embedder()
    return model.encode(texts, normalize_embeddings=True).tolist()


def rerank(query: str, candidates: list[str], top_k: int = 5) -> list[tuple[int, float]]:
    """Return [(original_index, score)] sorted by score, descending."""
    if not candidates:
        return []
    model = get_reranker()
    pairs = [(query, c) for c in candidates]
    scores = model.predict(pairs)
    ranked = sorted(enumerate(scores), key=lambda kv: kv[1], reverse=True)
    return ranked[:top_k]


__all__ = ["get_embedder", "get_reranker", "embed", "rerank"]
