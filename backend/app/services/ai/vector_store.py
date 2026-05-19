"""Qdrant client + collection management for policy chunks."""
# from qdrant_client import QdrantClient
# from qdrant_client.models import Distance, VectorParams
#
# from app.config import settings
#
#
# def get_qdrant() -> QdrantClient:
#     return QdrantClient(url=settings.qdrant_url)
#
#
# def ensure_collection(client: QdrantClient, name: str, dim: int) -> None:
#     if name not in [c.name for c in client.get_collections().collections]:
#         client.create_collection(
#             collection_name=name,
#             vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
#         )
