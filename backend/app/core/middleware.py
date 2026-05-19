"""HTTP middleware — Prometheus latency + request log."""
from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.core.metrics import http_request_duration, http_requests

logger = get_logger(__name__)


def _route_label(request: Request) -> str:
    """Use the route template (e.g. /cases/{case_id}) rather than the literal path.

    This keeps cardinality bounded — without it every unique case_id becomes a
    new Prometheus label value and metric storage explodes.
    """
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip the metrics endpoint itself.
        if request.url.path == "/metrics":
            return await call_next(request)

        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
        except Exception:
            elapsed = time.perf_counter() - start
            route = _route_label(request)
            http_requests.labels(method=request.method, route=route, status_code="500").inc()
            http_request_duration.labels(method=request.method, route=route).observe(elapsed)
            logger.exception("http.request.error", method=request.method, route=route)
            raise

        elapsed = time.perf_counter() - start
        route = _route_label(request)
        http_requests.labels(
            method=request.method, route=route, status_code=str(status_code)
        ).inc()
        http_request_duration.labels(method=request.method, route=route).observe(elapsed)

        logger.info(
            "http.request",
            method=request.method,
            route=route,
            status=status_code,
            elapsed_ms=int(elapsed * 1000),
        )
        return response
