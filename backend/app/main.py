"""MediShield FastAPI entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.v1.router import api_router
from app.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("medishield.startup", model=settings.anthropic_model)
    # TODO (Phase 3+): warm up embedding model, reranker, Qdrant collection.
    yield
    logger.info("medishield.shutdown")


app = FastAPI(
    title="MediShield AI",
    description="Multi-agent claims intake & triage platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/metrics", make_asgi_app())
app.include_router(api_router, prefix="/api/v1")


@app.get("/healthz", tags=["health"])
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", tags=["health"])
def readyz() -> dict[str, str]:
    # TODO (Phase 2+): verify DB + Qdrant + Anthropic reachability.
    return {"status": "ready"}
