from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from outline_safe_sfx import DEFAULT_PARAMS, outline_safe_rgba, white_background_preview


def test_outline_safe_mask_is_solid_inside_and_transparent_outside() -> None:
    source = Image.new("RGB", (80, 60), "white")
    ImageDraw.Draw(source).polygon([(20, 12), (60, 18), (48, 48), (24, 44)], fill="black")
    output = outline_safe_rgba(source)
    alpha = np.asarray(output.getchannel("A"), dtype=np.uint8)
    assert output.mode == "RGBA"
    assert output.width > 80 and output.height > 60
    assert alpha.max() == 255
    assert alpha.min() == 0
    assert np.count_nonzero(alpha == 255) > np.count_nonzero((alpha > 0) & (alpha < 255))
    assert np.asarray(output.getchannel("R"), dtype=np.uint8)[alpha > 0].max() == 0


def test_preview_is_black_glyph_on_white_background() -> None:
    source = Image.new("RGB", (32, 32), "white")
    ImageDraw.Draw(source).ellipse((8, 8, 24, 24), fill="black")
    output = outline_safe_rgba(source)
    preview = white_background_preview(output)
    pixels = np.asarray(preview, dtype=np.uint8)
    assert preview.mode == "RGB"
    assert pixels.min() == 0
    assert pixels.max() == 255


def test_reference_parameters_are_kept() -> None:
    assert DEFAULT_PARAMS["crop_pad"] == 18
    assert DEFAULT_PARAMS["sigma"] == 6.2
    assert DEFAULT_PARAMS["blur2_sigma"] == 7.2
    assert DEFAULT_PARAMS["threshold"] == 138
    assert DEFAULT_PARAMS["edge_width"] == 0.65
    assert DEFAULT_PARAMS["final_scale"] == 2

