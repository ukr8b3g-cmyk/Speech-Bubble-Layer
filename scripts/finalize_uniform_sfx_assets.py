"""Finalize recolorable comic assets from generated raster sources.

Generated Japanese SFX keep their original silhouette while becoming white
alpha masks, so the editor's single comic-yellow swatch controls every asset.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

from outline_safe_sfx import outline_safe_rgba


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "web" / "assets" / "sfx"
SOURCE_DIR = ROOT / "tmp" / "imagegen"

FIXED_COLOR_SFX = (
    "dokkunn-vertical-gpt-v1",
    "bubyuu-vertical-gpt-v1",
    "sore-dame-horizontal-gpt-v1",
    "nani-kore-horizontal-gpt-v1",
    "shii-horizontal-gpt-v1",
    "naisho-horizontal-gpt-v1",
    "ikisou-horizontal-gpt-v1",
    "joo-vertical-gpt-v1",
    "gokkun-vertical-gpt-v1",
    "pushaa-vertical-gpt-v1",
    "chira-vertical-gpt-v1",
    "woo-vertical-gpt-v1",
    "rerorero-vertical-gpt-v1",
    "haa-katakana-vertical-gpt-v1",
    "dokkunn-hiragana-vertical-gpt-v1",
)


def white_mask(alpha: Image.Image) -> Image.Image:
    white = Image.new("L", alpha.size, 255)
    return Image.merge("RGBA", (white, white, white, alpha))


def fit_square(alpha: Image.Image, size: int = 512, padding: int = 26) -> Image.Image:
    bbox = alpha.getbbox()
    if not bbox:
        raise RuntimeError("Generated an empty alpha mask")
    alpha = alpha.crop(bbox)
    limit = size - padding * 2
    scale = min(limit / alpha.width, limit / alpha.height)
    resized = alpha.resize(
        (max(1, round(alpha.width * scale)), max(1, round(alpha.height * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(resized, ((size - resized.width) // 2, (size - resized.height) // 2))
    return canvas


def colored_rgba_to_alpha(path: Path) -> Image.Image:
    """Keep the bright generated lettering and discard dark baked fringes."""
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    brightness = ImageOps.autocontrast(ImageOps.grayscale(image.convert("RGB")))
    bright_ink = brightness.point(lambda value: 0 if value < 38 else min(255, round((value - 38) * 2.0)))
    return fit_square(ImageChops.multiply(alpha, bright_ink))


def chroma_black_to_alpha(path: Path, key: tuple[int, int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    key_red, key_green, key_blue = key
    values = []
    for red, green, blue in image.getdata():
        distance = max(abs(red - key_red), abs(green - key_green), abs(blue - key_blue))
        values.append(0 if distance < 28 else min(255, round((distance - 28) * 4.2)))
    alpha = Image.new("L", image.size, 0)
    alpha.putdata(values)
    alpha = alpha.point(lambda value: 0 if value < 72 else value)
    return fit_square(alpha)


def filled_brush_heart(path: Path) -> Image.Image:
    """Fill the interior of the generated brush-outline heart."""
    outline = Image.open(path).convert("RGBA").getchannel("A")
    binary = outline.point(lambda value: 255 if value >= 24 else 0)
    closed = binary.filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.MinFilter(11))
    interior = ImageOps.invert(closed)
    ImageDraw.floodfill(interior, (0, 0), 0)
    filled = ImageChops.lighter(closed, interior)
    filled = ImageChops.lighter(filled, outline)
    return fit_square(filled)


def save(alpha: Image.Image, asset_id: str) -> None:
    outline_safe_rgba(alpha).save(
        ASSET_DIR / f"{asset_id}.webp",
        "WEBP",
        lossless=True,
        method=6,
    )


def main() -> None:
    for asset_id in FIXED_COLOR_SFX:
        save(colored_rgba_to_alpha(ASSET_DIR / f"{asset_id}.webp"), asset_id)

    save(
        chroma_black_to_alpha(
            SOURCE_DIR / "20260719" / "giri-small-tsu-vertical-source.png",
            (255, 0, 255),
        ),
        "giri-small-tsu-vertical-mask",
    )
    save(
        filled_brush_heart(SOURCE_DIR / "onomatopoeia" / "brush-heart.png"),
        "handdrawn-filled-heart-mask",
    )


if __name__ == "__main__":
    main()
