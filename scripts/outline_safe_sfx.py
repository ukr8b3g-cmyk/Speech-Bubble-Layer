"""Shared outline-safe cleanup for opaque SFX/onomatopoeia masks.

The processor deliberately creates a narrow antialias band around a solid
black glyph.  This keeps a later editor outline from becoming a second soft
fringe while retaining the source silhouette.
"""

from __future__ import annotations

import ast
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np
from PIL import Image


DEFAULT_PARAMS: dict[str, float | int] = {
    "crop_pad": 18,
    "work_scale": 4,
    "sigma": 6.2,
    "blur2_sigma": 7.2,
    "unsharp_amount": 3.7,
    "unsharp_subtract": -2.7,
    "contrast_offset": 34.0,
    "contrast_gain": 1.55,
    "threshold": 138,
    "edge_width": 0.65,
    "inside_solid_cutoff": 1.0,
    "final_scale": 2,
}


def _uint8(value: np.ndarray) -> np.ndarray:
    return np.clip(value, 0, 255).astype(np.uint8)


def _source_to_alpha(source: Image.Image) -> np.ndarray:
    """Return a white-ink alpha mask from a raster source.

    Existing runtime masks have useful alpha, while source/reference images
    often have an opaque white background.  Prefer alpha only when it really
    contains transparency; otherwise derive it from the grayscale image.
    """

    image = source.convert("RGBA")
    rgba = np.asarray(image, dtype=np.uint8)
    alpha = rgba[:, :, 3]
    if np.any(alpha < 250):
        return alpha.copy()
    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    return _uint8(255.0 - gray.astype(np.float32))


def _remove_small_noise(alpha: np.ndarray, min_area: int = 3) -> np.ndarray:
    cleaned = alpha.copy()
    peak = int(cleaned.max())
    if 0 < peak < 192:
        cleaned = _uint8(cleaned.astype(np.float32) * (255.0 / peak))
    cleaned[cleaned < 8] = 0
    binary = (cleaned >= 16).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    keep = np.zeros_like(binary)
    for label in range(1, count):
        if int(stats[label, cv2.CC_STAT_AREA]) >= min_area:
            keep[labels == label] = 1
    # Keep the antialias pixels immediately around an accepted component.
    keep_region = cv2.dilate(keep, np.ones((3, 3), dtype=np.uint8))
    cleaned[keep_region == 0] = 0
    return cleaned


def _crop_with_padding(alpha: np.ndarray, pad: int) -> np.ndarray:
    points = cv2.findNonZero(alpha)
    if points is None:
        raise ValueError("The source contains no visible glyph")
    x, y, width, height = cv2.boundingRect(points)
    # Add the requested padding even when the source glyph touches an image
    # edge; clipping the crop would leave the final glyph flush to the edge.
    return np.pad(
        alpha[y : y + height, x : x + width],
        ((pad, pad), (pad, pad)),
        mode="constant",
        constant_values=0,
    )


def outline_safe_alpha(
    source: Image.Image | np.ndarray,
    params: dict[str, float | int] | None = None,
) -> np.ndarray:
    """Build the final two-times alpha mask used by SFX assets."""

    settings = {**DEFAULT_PARAMS, **(params or {})}
    if isinstance(source, Image.Image):
        alpha = _source_to_alpha(source) if source.mode != "L" else np.asarray(source, dtype=np.uint8)
    else:
        alpha = np.asarray(source, dtype=np.uint8)
    alpha = _remove_small_noise(alpha)
    cropped = _crop_with_padding(alpha, int(settings["crop_pad"]))

    work_scale = int(settings["work_scale"])
    final_scale = int(settings["final_scale"])
    work = cv2.resize(
        cropped,
        (max(1, cropped.shape[1] * work_scale), max(1, cropped.shape[0] * work_scale)),
        interpolation=cv2.INTER_LANCZOS4,
    ).astype(np.float32)
    blurred = cv2.GaussianBlur(
        work,
        (0, 0),
        sigmaX=float(settings["sigma"]),
        sigmaY=float(settings["sigma"]),
    )
    blur2 = cv2.GaussianBlur(
        blurred,
        (0, 0),
        sigmaX=float(settings["blur2_sigma"]),
        sigmaY=float(settings["blur2_sigma"]),
    )
    sharpened = cv2.addWeighted(
        blurred,
        float(settings["unsharp_amount"]),
        blur2,
        float(settings["unsharp_subtract"]),
        0,
    )
    sharpened = np.clip(
        (sharpened - float(settings["contrast_offset"]))
        * float(settings["contrast_gain"]),
        0,
        255,
    )

    solid = (sharpened >= float(settings["threshold"])).astype(np.uint8) * 255
    inside = cv2.distanceTransform(solid, cv2.DIST_L2, 3)
    outside = cv2.distanceTransform(255 - solid, cv2.DIST_L2, 3)
    # Use float64 here: an all-solid/all-transparent distance transform can
    # contain a very large sentinel value in float32.  It is harmless after
    # clipping, but must not emit an overflow warning during the division.
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        sdf = inside.astype(np.float64) - outside.astype(np.float64)
        edge_width = max(0.05, float(settings["edge_width"]))
        final_hi = np.clip((sdf / edge_width + 0.5) * 255.0, 0, 255)
    if not np.isfinite(final_hi).all():
        final_hi = np.where(
            np.isfinite(final_hi),
            final_hi,
            np.where(solid > 0, 255.0, 0.0),
        )
    final_hi[inside >= float(settings["inside_solid_cutoff"])] = 255

    target_width = max(1, round(final_hi.shape[1] / final_scale))
    target_height = max(1, round(final_hi.shape[0] / final_scale))
    return cv2.resize(
        _uint8(final_hi),
        (target_width, target_height),
        interpolation=cv2.INTER_LANCZOS4,
    )


def outline_safe_rgba(
    source: Image.Image | np.ndarray,
    params: dict[str, float | int] | None = None,
) -> Image.Image:
    alpha = outline_safe_alpha(source, params)
    rgb = np.zeros((alpha.shape[0], alpha.shape[1], 3), dtype=np.uint8)
    return Image.fromarray(np.dstack((rgb, alpha)), "RGBA")


def white_background_preview(mask: Image.Image) -> Image.Image:
    alpha = np.asarray(mask.getchannel("A"), dtype=np.uint8)
    gray = 255 - alpha
    return Image.fromarray(np.repeat(gray[:, :, None], 3, axis=2), "RGB")


def _atomic_save(image: Image.Image, path: Path, image_format: str, **kwargs: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.stem}-", suffix=path.suffix, dir=path.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        image.save(temp_path, image_format, **kwargs)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def save_outline_safe_asset(
    source_path: Path,
    webp_path: Path,
    png_path: Path | None = None,
    preview_path: Path | None = None,
    params: dict[str, float | int] | None = None,
) -> dict[str, Any]:
    with Image.open(source_path) as source:
        source_size = list(source.size)
        mask = outline_safe_rgba(source, params)
    _atomic_save(mask, webp_path, "WEBP", lossless=True, method=6)
    if png_path is not None:
        _atomic_save(mask, png_path, "PNG", compress_level=9)
    if preview_path is not None:
        _atomic_save(white_background_preview(mask), preview_path, "PNG", compress_level=9)
    alpha = np.asarray(mask.getchannel("A"), dtype=np.uint8)
    return {
        "sourceSize": source_size,
        "outputSize": list(mask.size),
        "visiblePixels": int(np.count_nonzero(alpha)),
        "solidPixels": int(np.count_nonzero(alpha == 255)),
        "parameters": {**DEFAULT_PARAMS, **(params or {})},
    }


def load_symbol_asset_ids(nodes_path: Path) -> set[str]:
    """Read the node's symbol registry without importing ComfyUI modules."""

    try:
        tree = ast.parse(nodes_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    for node in ast.walk(tree):
        targets: Iterable[ast.expr] = ()
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = (node.target,)
        if any(isinstance(target, ast.Name) and target.id == "_SYMBOL_SFX_ASSETS" for target in targets):
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                return set()
            return {str(item) for item in value if isinstance(item, str)}
    return set()


_EXCLUDED_NAME_PARTS = (
    "arrow",
    "star",
    "sparkle",
    "scribble",
    "rough-circle",
    "sweat",
    "anger",
    "emphasis-lines",
    "shock-lines",
    "tension-lines",
    "worry-squiggle",
    "breath-puff",
    "dizzy",
    "hot-spring",
    "bandage",
    "music",
    "sleep",
    "lightning",
    "motion",
    "suit-",
    "heart",
    "bubble",
    "cloud",
    "hexagon",
    "oval",
    "tail",
    "frame",
    "stamp",
    "symbol",
    "pink-",
    "brush-",
    "glossy",
    "flying",
    "outline",
    "hollow",
    "open-",
)


def exclusion_reason(asset_id: str, symbol_ids: set[str]) -> str | None:
    if asset_id in symbol_ids:
        return "registered symbol asset"
    lowered = asset_id.lower()
    if lowered in {"exclamation-mask", "question-mask"}:
        return "standalone symbol asset"
    for part in _EXCLUDED_NAME_PARTS:
        if part in lowered:
            return f"symbol/non-solid asset name: {part}"
    return None


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
