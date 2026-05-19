"""Shared pytest fixtures."""
import os

# Make sure secrets-dependent code paths don't trip during unit tests.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("MYSQL_URL", "sqlite:///:memory:")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("LANGSMITH_TRACING", "false")
