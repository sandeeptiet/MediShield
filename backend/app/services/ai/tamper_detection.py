"""Error Level Analysis (ELA) — lightweight image-forgery signal.

How it works: re-save the image at a known JPEG quality, diff the re-saved
image against the original, and look at the magnitude of differences across
regions. Pristine images compress evenly, so the diff is uniform and dim.
Edited regions tend to compress differently from their surroundings and stand
out as bright patches.

This is not a definitive forgery detector — it's a screening signal. Returns
a 0..1 score plus the bounding boxes of the strongest suspicious regions for
the UI to highlight.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import TypedDict

import cv2
import numpy as np
from PIL import Image


class TamperResult(TypedDict):
    tamper_score: float       # 0.0 clean, 1.0 strongly suggestive of tampering
    suspicious_regions: list[dict[str, int]]   # [{x, y, w, h}] in image coords
    notes: str


def compute_ela(
    image_path: str | Path,
    *,
    quality: int = 90,
    suspicious_threshold: int = 35,
    min_region_area: int = 200,
) -> TamperResult:
    """Run ELA on a local image file.

    Args:
        image_path: path to image (jpg/png/etc).
        quality: JPEG re-save quality. 90 is the standard default for ELA.
        suspicious_threshold: pixel-diff intensity above which a pixel is "bright".
        min_region_area: ignore connected components smaller than this.
    """
    path = Path(image_path)
    if not path.exists():
        return {
            "tamper_score": 0.0,
            "suspicious_regions": [],
            "notes": f"image not found: {path}",
        }

    try:
        original = Image.open(path).convert("RGB")
    except Exception as exc:  # corrupt file, unsupported format, etc.
        return {
            "tamper_score": 0.0,
            "suspicious_regions": [],
            "notes": f"unreadable image: {exc}",
        }

    # Re-save at the target quality, in-memory.
    buf = io.BytesIO()
    original.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")

    a = np.asarray(original, dtype=np.int16)
    b = np.asarray(recompressed, dtype=np.int16)
    diff = np.abs(a - b).astype(np.uint8)
    gray = cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY)

    # Normalize so the brightest pixel becomes 255.
    max_val = int(gray.max())
    if max_val > 0:
        gray = cv2.convertScaleAbs(gray, alpha=255.0 / max_val)

    # Overall score: mean brightness of the top 5% of pixels.
    flat = gray.flatten()
    if flat.size == 0:
        return {"tamper_score": 0.0, "suspicious_regions": [], "notes": "empty image"}
    cutoff = max(1, int(flat.size * 0.05))
    top = np.partition(flat, -cutoff)[-cutoff:]
    tamper_score = float(top.mean()) / 255.0

    # Suspicious regions: connected components in the thresholded diff.
    _, mask = cv2.threshold(gray, suspicious_threshold, 255, cv2.THRESH_BINARY)
    n_labels, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)

    regions: list[dict[str, int]] = []
    for i in range(1, n_labels):
        x, y, w, h, area = stats[i]
        if area >= min_region_area:
            regions.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})

    regions.sort(key=lambda r: r["w"] * r["h"], reverse=True)
    return {
        "tamper_score": round(tamper_score, 4),
        "suspicious_regions": regions[:10],
        "notes": f"max_diff={max_val}, region_count={len(regions)}",
    }


__all__ = ["compute_ela", "TamperResult"]
