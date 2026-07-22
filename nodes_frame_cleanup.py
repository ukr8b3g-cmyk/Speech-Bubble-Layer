"""Frame asset mask generation and alpha cleanup nodes for ComfyUI.

The nodes in this module intentionally depend only on packages already used by
ComfyUI-Speech-Bubble: Pillow, NumPy and Torch.  They are designed as the final
cleanup stage after BiRefNet/ViTMatte, and also provide a solid-colour chroma
key fallback for generated frame assets.
"""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import torch
from PIL import Image, ImageColor, ImageFilter


def _parse_rgb(value: str, fallback: str = "#ffffff") -> np.ndarray:
    try:
        rgb = ImageColor.getrgb(str(value or fallback))[:3]
    except (TypeError, ValueError):
        rgb = ImageColor.getrgb(fallback)[:3]
    return np.asarray(rgb, dtype=np.float32) / 255.0


def _to_numpy_image_batch(image: torch.Tensor) -> np.ndarray:
    array = image.detach().cpu().numpy().astype(np.float32, copy=False)
    return np.clip(array[..., :3], 0.0, 1.0)


def _to_numpy_mask_batch(mask: torch.Tensor) -> np.ndarray:
    array = mask.detach().cpu().numpy().astype(np.float32, copy=False)
    if array.ndim == 4:
        array = array[..., 0]
    return np.clip(array, 0.0, 1.0)


def _tensor_like(array: np.ndarray, reference: torch.Tensor) -> torch.Tensor:
    return torch.from_numpy(np.ascontiguousarray(array, dtype=np.float32)).to(
        device=reference.device,
        dtype=reference.dtype,
    )


def _batch_align(array: np.ndarray, batch: int) -> np.ndarray:
    if array.shape[0] == batch:
        return array
    if array.shape[0] == 1 and batch > 1:
        return np.repeat(array, batch, axis=0)
    raise ValueError(f"Batch size mismatch: expected {batch}, got {array.shape[0]}")


def _estimate_background(rgb: np.ndarray, alpha: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    """Estimate a uniform source background from transparent/edge pixels."""
    candidates = alpha <= 0.03
    if np.count_nonzero(candidates) < 16:
        border = np.zeros_like(alpha, dtype=bool)
        border[: max(1, alpha.shape[0] // 64), :] = True
        border[-max(1, alpha.shape[0] // 64) :, :] = True
        border[:, : max(1, alpha.shape[1] // 64)] = True
        border[:, -max(1, alpha.shape[1] // 64) :] = True
        candidates = border
    pixels = rgb[candidates]
    if not len(pixels):
        return fallback
    return np.median(pixels, axis=0).astype(np.float32)


def _pil_gray(array: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(np.rint(array * 255.0), 0, 255).astype(np.uint8), mode="L")


def _morph_alpha(alpha: np.ndarray, amount: float) -> np.ndarray:
    """Erode (positive) or dilate (negative) alpha with fractional blending."""
    if abs(amount) < 1e-6:
        return alpha
    whole = int(math.floor(abs(amount)))
    fraction = abs(amount) - whole
    current = alpha.astype(np.float32, copy=True)
    filter_type = ImageFilter.MinFilter if amount > 0 else ImageFilter.MaxFilter
    for _ in range(whole):
        current = np.asarray(_pil_gray(current).filter(filter_type(3)), dtype=np.float32) / 255.0
    if fraction > 1e-6:
        next_alpha = np.asarray(_pil_gray(current).filter(filter_type(3)), dtype=np.float32) / 255.0
        current = current * (1.0 - fraction) + next_alpha * fraction
    return np.clip(current, 0.0, 1.0)


def _feather_alpha(alpha: np.ndarray, radius: float) -> np.ndarray:
    if radius <= 1e-6:
        return alpha
    return np.asarray(
        _pil_gray(alpha).filter(ImageFilter.GaussianBlur(float(radius))),
        dtype=np.float32,
    ) / 255.0


def _neighbor_slices(height: int, width: int) -> Iterable[tuple[slice, slice, slice, slice]]:
    # target_y, target_x, source_y, source_x.  Explicit slices avoid np.roll wrap-around.
    for dy, dx in (
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    ):
        ty0, ty1 = max(0, -dy), min(height, height - dy)
        tx0, tx1 = max(0, -dx), min(width, width - dx)
        sy0, sy1 = ty0 + dy, ty1 + dy
        sx0, sx1 = tx0 + dx, tx1 + dx
        yield slice(ty0, ty1), slice(tx0, tx1), slice(sy0, sy1), slice(sx0, sx1)


def _alpha_bleed(rgb: np.ndarray, alpha: np.ndarray, radius: int) -> np.ndarray:
    """Extend foreground RGB into transparent pixels without changing alpha."""
    radius = max(0, int(radius))
    if radius == 0:
        return rgb
    output = rgb.astype(np.float32, copy=True)
    known = alpha > 1.0 / 255.0
    height, width = alpha.shape
    for _ in range(radius):
        sums = np.zeros_like(output)
        counts = np.zeros((height, width), dtype=np.float32)
        for ty, tx, sy, sx in _neighbor_slices(height, width):
            neighbor_known = known[sy, sx]
            sums[ty, tx] += output[sy, sx] * neighbor_known[..., None]
            counts[ty, tx] += neighbor_known
        fill = (~known) & (counts > 0)
        if not np.any(fill):
            break
        output[fill] = sums[fill] / counts[fill, None]
        known[fill] = True
    return np.clip(output, 0.0, 1.0)


def _decontaminate(rgb: np.ndarray, alpha: np.ndarray, background: np.ndarray) -> np.ndarray:
    """Undo compositing against a uniform background for semi-transparent edges."""
    safe_alpha = np.maximum(alpha[..., None], 1.0 / 255.0)
    foreground = (rgb - background[None, None, :] * (1.0 - alpha[..., None])) / safe_alpha
    # Keep fully opaque pixels exactly as supplied and only solve transition pixels.
    transition = (alpha > 0.0) & (alpha < 0.999)
    result = rgb.copy()
    result[transition] = foreground[transition]
    return np.clip(result, 0.0, 1.0)


def _despill(rgb: np.ndarray, alpha: np.ndarray, background: np.ndarray, strength: float) -> np.ndarray:
    """Reduce residual source-background hue along the transition edge."""
    strength = max(0.0, min(1.0, float(strength)))
    if strength <= 0:
        return rgb
    edge = np.clip((1.0 - alpha) * 2.0, 0.0, 1.0)[..., None] * strength
    # Project the residual toward neutral luminance instead of blindly darkening it.
    luminance = np.sum(rgb * np.array([0.2126, 0.7152, 0.0722], dtype=np.float32), axis=-1, keepdims=True)
    background_luma = float(np.sum(background * np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)))
    neutral_background = np.full_like(rgb, background_luma)
    residual = background[None, None, :] - neutral_background
    return np.clip(rgb - residual * edge, 0.0, 1.0)


class FrameChromaKeyMask:
    """Build a soft alpha mask from a flat generation background."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "background_color": ("STRING", {"default": "#ffffff"}),
                "tolerance": ("FLOAT", {"default": 0.035, "min": 0.0, "max": 1.0, "step": 0.001}),
                "softness": ("FLOAT", {"default": 0.08, "min": 0.001, "max": 1.0, "step": 0.001}),
                "edge_cleanup": ("FLOAT", {"default": 0.0, "min": -3.0, "max": 3.0, "step": 0.1}),
                "feather": ("FLOAT", {"default": 0.25, "min": 0.0, "max": 3.0, "step": 0.05}),
            }
        }

    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("mask",)
    FUNCTION = "execute"
    CATEGORY = "image/speech_bubble/frame_tools"

    def execute(self, image, background_color, tolerance, softness, edge_cleanup, feather):
        batch = _to_numpy_image_batch(image)
        background = _parse_rgb(background_color)
        masks = []
        tolerance = max(0.0, float(tolerance))
        softness = max(1e-6, float(softness))
        for rgb in batch:
            # Maximum-channel distance is stable for neutral and saturated key colours.
            distance = np.max(np.abs(rgb - background[None, None, :]), axis=-1)
            alpha = np.clip((distance - tolerance) / softness, 0.0, 1.0)
            alpha = alpha * alpha * (3.0 - 2.0 * alpha)  # smoothstep
            alpha = _morph_alpha(alpha, float(edge_cleanup))
            alpha = _feather_alpha(alpha, float(feather))
            masks.append(alpha)
        return (_tensor_like(np.stack(masks, axis=0), image),)


class FrameAlphaCleanup:
    """Clean matte fringes and extend valid RGB into transparent pixels."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "background_mode": (["auto", "white", "black", "custom"], {"default": "auto"}),
                "background_color": ("STRING", {"default": "#ffffff"}),
                "decontaminate": ("BOOLEAN", {"default": True}),
                "despill_strength": ("FLOAT", {"default": 0.25, "min": 0.0, "max": 1.0, "step": 0.05}),
                "edge_cleanup": ("FLOAT", {"default": 0.4, "min": -3.0, "max": 3.0, "step": 0.1}),
                "feather": ("FLOAT", {"default": 0.2, "min": 0.0, "max": 3.0, "step": 0.05}),
                "alpha_bleed": ("INT", {"default": 3, "min": 0, "max": 16, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("clean_image", "clean_mask")
    FUNCTION = "execute"
    CATEGORY = "image/speech_bubble/frame_tools"

    def execute(
        self,
        image,
        mask,
        background_mode,
        background_color,
        decontaminate,
        despill_strength,
        edge_cleanup,
        feather,
        alpha_bleed,
    ):
        rgb_batch = _to_numpy_image_batch(image)
        alpha_batch = _batch_align(_to_numpy_mask_batch(mask), rgb_batch.shape[0])
        custom_background = _parse_rgb(background_color)
        fixed_background = {
            "white": np.ones(3, dtype=np.float32),
            "black": np.zeros(3, dtype=np.float32),
            "custom": custom_background,
        }.get(str(background_mode))

        cleaned_images = []
        cleaned_masks = []
        for rgb, source_alpha in zip(rgb_batch, alpha_batch):
            alpha = _morph_alpha(source_alpha, float(edge_cleanup))
            alpha = _feather_alpha(alpha, float(feather))
            alpha = np.clip(alpha, 0.0, 1.0)
            background = fixed_background
            if background is None:
                background = _estimate_background(rgb, source_alpha, custom_background)
            clean_rgb = rgb
            if bool(decontaminate):
                clean_rgb = _decontaminate(clean_rgb, alpha, background)
            clean_rgb = _despill(clean_rgb, alpha, background, float(despill_strength))
            clean_rgb = _alpha_bleed(clean_rgb, alpha, int(alpha_bleed))
            cleaned_images.append(clean_rgb)
            cleaned_masks.append(alpha)

        return (
            _tensor_like(np.stack(cleaned_images, axis=0), image),
            _tensor_like(np.stack(cleaned_masks, axis=0), mask),
        )


NODE_CLASS_MAPPINGS = {
    "FrameChromaKeyMask": FrameChromaKeyMask,
    "FrameAlphaCleanup": FrameAlphaCleanup,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FrameChromaKeyMask": "Frame Chroma Key Mask",
    "FrameAlphaCleanup": "Frame Alpha Cleanup",
}
