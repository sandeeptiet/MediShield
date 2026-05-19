"""MediShield FastAPI entrypoint."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.database import get_db
from app.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import PrometheusMiddleware
from app.core.tracing import configure_tracing

configure_logging()
configure_tracing()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("medishield.startup", model=settings.anthropic_model)
    # TODO (Phase 4+): warm up embedding model, reranker, Qdrant collection.
    yield
    logger.info("medishield.shutdown")


app = FastAPI(
    title="MediShield AI",
    description="Multi-agent claims intake & triage platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(PrometheusMiddleware)
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
def readyz(db: Session = Depends(get_db)) -> dict[str, object]:
    """Top-level readiness probe — matches the Kubernetes probe path."""
    from app.api.v1.endpoints.health import ready as ready_impl
    return ready_impl(db=db)
