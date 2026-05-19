"""Claude Sonnet 4.6 client wrapper.

Centralizes Anthropic SDK setup so every agent shares the same retry,
timeout, and observability config.
"""
# from anthropic import Anthropic
# from app.config import settings
#
# _client: Anthropic | None = None
#
#
# def get_claude() -> Anthropic:
#     global _client
#     if _client is None:
#         _client = Anthropic(api_key=settings.anthropic_api_key)
#     return _client
