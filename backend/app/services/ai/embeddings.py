"""Qwen3 embedder + BGE reranker (local, via sentence-transformers).

Pre-loaded once at startup; reused across requests.
"""
# from sentence_transformers import SentenceTransformer, CrossEncoder
#
# _embedder: SentenceTransformer | None = None
# _reranker: CrossEncoder | None = None
#
#
# def get_embedder() -> SentenceTransformer:
#     global _embedder
#     if _embedder is None:
#         _embedder = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
#     return _embedder
#
#
# def get_reranker() -> CrossEncoder:
#     global _reranker
#     if _reranker is None:
#         _reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")
#     return _reranker
