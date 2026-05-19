"""LangSmith tracing setup.

LangChain reads LANGCHAIN_* environment variables on import. We mirror our
typed settings into those env vars at startup so the rest of the code doesn't
need to know LangChain's variable names.
"""
from __future__ import annotations

import os

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def configure_tracing() -> None:
    if not settings.langsmith_tracing:
        logger.info("langsmith.disabled")
        return

    if not settings.langsmith_api_key:
        logger.warning("langsmith.misconfigured", reason="LANGSMITH_API_KEY missing")
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    # The LangSmith SDK also reads these:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project

    logger.info("langsmith.enabled", project=settings.langsmith_project)
