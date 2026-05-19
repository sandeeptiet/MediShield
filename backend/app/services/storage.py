"""Local file storage for uploaded case documents.

Layout:
    {UPLOAD_DIR}/{case_id}/{sanitized_filename}

For OpenShift / production this swaps to S3 / MinIO with the same interface.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import BinaryIO

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_ALLOWED_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")


def _sanitize(filename: str) -> str:
    name = _ALLOWED_FILENAME.sub("_", filename.strip()) or "upload.bin"
    return name[:200]


def save_upload(case_id: str, filename: str, stream: BinaryIO) -> Path:
    """Persist an uploaded file stream and return its absolute path."""
    safe = _sanitize(filename)
    target_dir = Path(settings.upload_dir) / case_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / safe
    with target.open("wb") as out:
        shutil.copyfileobj(stream, out)
    logger.info("storage.saved", case_id=case_id, path=str(target), size=target.stat().st_size)
    return target.resolve()


def case_dir(case_id: str) -> Path:
    return (Path(settings.upload_dir) / case_id).resolve()


__all__ = ["save_upload", "case_dir"]
