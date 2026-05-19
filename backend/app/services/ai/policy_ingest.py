"""Policy PDF → chunks → embeddings → Qdrant.

One-time-per-policy ingestion: Docling parses the PDF preserving section
structure, we chunk it by section (with a sane fallback to ~600-token windows),
embed with Qwen3, and upsert into Qdrant with rich payload metadata.

Run via:
    python -m scripts.ingest_policies path/to/policies/

For agents at query time, this is the read side handled by `vector_store.search`.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.services.ai.vector_store import upsert_chunks

logger = get_logger(__name__)

CHUNK_TARGET_CHARS = 1800   # ~600 tokens
CHUNK_OVERLAP_CHARS = 200


def _split_long(text: str, *, target: int = CHUNK_TARGET_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    """Fallback splitter when a section is too long for a single chunk."""
    if len(text) <= target:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + target)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def _docling_sections(pdf_path: Path) -> list[dict[str, str]]:
    """Parse PDF with Docling and return [{section, text}].

    If Docling isn't installed or fails on the file, fall back to plain-text
    extraction so the ingestion still produces something useful.
    """
    try:
        from docling.document_converter import DocumentConverter
    except Exception as exc:  # pragma: no cover — Docling missing in some envs
        logger.warning("docling.unavailable", error=str(exc))
        return _fallback_plain_text(pdf_path)

    try:
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        markdown = result.document.export_to_markdown()
    except Exception as exc:
        logger.warning("docling.failed", path=str(pdf_path), error=str(exc))
        return _fallback_plain_text(pdf_path)

    # Split the exported markdown on ATX headings.
    parts: list[dict[str, str]] = []
    current_section = "root"
    buf: list[str] = []
    for line in markdown.splitlines():
        m = re.match(r"^#+\s+(.*)", line)
        if m:
            if buf:
                parts.append({"section": current_section, "text": "\n".join(buf).strip()})
                buf = []
            current_section = m.group(1).strip() or "untitled"
        else:
            buf.append(line)
    if buf:
        parts.append({"section": current_section, "text": "\n".join(buf).strip()})

    return [p for p in parts if p["text"]]


def _fallback_plain_text(pdf_path: Path) -> list[dict[str, str]]:
    """Last-resort: read with PyPDF if available, else give up gracefully."""
    try:
        import pypdf  # noqa: F401 — not in deps, but try anyway
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        if not text.strip():
            return []
        return [{"section": "full_document", "text": text}]
    except Exception:
        logger.error("pdf_fallback.failed", path=str(pdf_path))
        return []


def ingest_policy_pdf(
    pdf_path: str | Path,
    *,
    policy_id: str | None = None,
    policy_name: str | None = None,
) -> int:
    """Chunk + embed + upsert one policy PDF into Qdrant.

    Returns the number of chunks upserted.
    """
    path = Path(pdf_path)
    policy_id = policy_id or path.stem
    policy_name = policy_name or path.stem.replace("_", " ").title()

    logger.info("policy.ingest.start", policy_id=policy_id, path=str(path))
    sections = _docling_sections(path)
    if not sections:
        logger.warning("policy.ingest.empty", policy_id=policy_id)
        return 0

    chunks: list[dict[str, Any]] = []
    for sec in sections:
        for piece in _split_long(sec["text"]):
            chunks.append(
                {
                    "text": piece,
                    "section": sec["section"],
                    "policy_id": policy_id,
                    "policy_name": policy_name,
                    "source_file": path.name,
                }
            )

    count = upsert_chunks(chunks)
    logger.info("policy.ingest.done", policy_id=policy_id, chunks=count)
    return count


def ingest_directory(directory: str | Path) -> dict[str, int]:
    """Ingest every PDF in a directory. Returns {filename: chunk_count}."""
    root = Path(directory)
    results: dict[str, int] = {}
    for pdf in sorted(root.glob("*.pdf")):
        results[pdf.name] = ingest_policy_pdf(pdf)
    return results


__all__ = ["ingest_policy_pdf", "ingest_directory"]
