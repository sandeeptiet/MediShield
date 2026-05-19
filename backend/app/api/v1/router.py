"""Aggregates v1 endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, cases, health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
