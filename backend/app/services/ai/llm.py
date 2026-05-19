"""Claude Sonnet 4.6 client wrapper — the single LLM entrypoint for all agents.

Provides three call shapes:
  - `complete_text`   — plain text prompt -> text response
  - `complete_vision` — text + base64-encoded image(s) -> text response
  - `complete_json`   — prompt + Pydantic schema -> validated structured output

All three centralize the model name, timeouts, and tracing config so individual
agents stay focused on their domain logic.
"""
from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any, TypeVar

from anthropic import Anthropic
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)

_client: Anthropic | None = None


def get_claude() -> Anthropic:
    """Return the singleton Anthropic client."""
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        _client = Anthropic(api_key=settings.anthropic_api_key)
        logger.info("anthropic.client.ready", model=settings.anthropic_model)
    return _client


# --- Image helpers ------------------------------------------------------


def _image_block(image_path: str | Path) -> dict[str, Any]:
    """Build an Anthropic content block from a local image file."""
    path = Path(image_path)
    mime, _ = mimetypes.guess_type(path.name)
    if mime is None or not mime.startswith("image/"):
        mime = "image/jpeg"
    data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": mime, "data": data},
    }


# --- Public call shapes -------------------------------------------------


def complete_text(
    *,
    system: str,
    user: str,
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> str:
    """Plain text in, plain text out."""
    client = get_claude()
    resp = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return _text_from_response(resp)


def complete_vision(
    *,
    system: str,
    user: str,
    image_paths: list[str | Path],
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> str:
    """Text + one-or-more images in, plain text out."""
    client = get_claude()
    content: list[dict[str, Any]] = [_image_block(p) for p in image_paths]
    content.append({"type": "text", "text": user})

    resp = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": content}],
    )
    return _text_from_response(resp)


def complete_json(
    *,
    system: str,
    user: str,
    schema: type[T],
    image_paths: list[str | Path] | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.0,
) -> T:
    """Force structured JSON output validated against a Pydantic schema.

    Uses Anthropic's tool-use API: we declare a single tool whose input_schema
    is the Pydantic model's JSON schema, then force_tool_choice that tool.
    """
    client = get_claude()
    tool_name = "emit_" + schema.__name__.lower()

    json_schema = schema.model_json_schema()
    # Anthropic tool input_schema must be an object; Pydantic already gives that.

    content: list[dict[str, Any]] = []
    if image_paths:
        content.extend(_image_block(p) for p in image_paths)
    content.append({"type": "text", "text": user})

    resp = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        tools=[
            {
                "name": tool_name,
                "description": f"Emit a {schema.__name__} object.",
                "input_schema": json_schema,
            }
        ],
        tool_choice={"type": "tool", "name": tool_name},
        messages=[{"role": "user", "content": content}],
    )

    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == tool_name:
            try:
                return schema.model_validate(block.input)
            except ValidationError as exc:
                logger.warning(
                    "claude.structured_output.validation_failed",
                    schema=schema.__name__,
                    errors=exc.errors(),
                    raw_input=json.dumps(block.input)[:1000],
                )
                raise

    raise RuntimeError(
        f"Claude did not emit a tool_use block for {tool_name}. "
        f"Got blocks: {[getattr(b, 'type', '?') for b in resp.content]}"
    )


# --- Helpers ------------------------------------------------------------


def _text_from_response(resp: Any) -> str:
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


__all__ = ["get_claude", "complete_text", "complete_vision", "complete_json"]
