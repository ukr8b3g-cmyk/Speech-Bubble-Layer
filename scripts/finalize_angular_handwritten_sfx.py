"""Finalize the approved angular handwritten SFX batch as white alpha masks."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from outline_safe_sfx import outline_safe_rgba


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "tmp" / "imagegen" / "20260719" / "angular_handwritten_sfx"
OUTPUT_DIR = ROOT / "web" / "assets" / "sfx"

ASSETS = {
    "nuron-angular-vertical-mask": "nuron-angular-vertical-transparent.png",
    "dochu-exclamation-angular-vertical-mask": "dochu-exclamation-angular-vertical-transparent.png",
    "giu-long-angular-vertical-mask": "giu-long-angular-vertical-transparent.png",
    "hiku-small-tsu-angular-vertical-mask": "hiku-small-tsu-angular-vertical-transparent.png",
    "giu-angular-vertical-mask": "giu-angular-vertical-transparent.png",
    "zuru-angular-vertical-mask": "zuru-angular-vertical-transparent.png",
    "dokun-hiragana-angular-vertical-mask": "dokun-hiragana-angular-vertical-transparent.png",
    "dokun-hiragana-angular-horizontal-mask": "dokun-hiragana-angular-horizontal-transparent.png",
    "zubu-small-tsu-angular-vertical-mask": "zubu-small-tsu-angular-vertical-transparent.png",
}


def fit_square(alpha: Image.Image, size: int = 512, padding: int = 28) -> Image.Image:
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


def white_mask(alpha: Image.Image) -> Image.Image:
    white = Image.new("L", alpha.size, 255)
    return Image.merge("RGBA", (white, white, white, alpha))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for asset_id, source_name in ASSETS.items():
        source = Image.open(SOURCE_DIR / source_name).convert("RGBA")
        output = outline_safe_rgba(source.getchannel("A"))
        output.save(OUTPUT_DIR / f"{asset_id}.webp", "WEBP", lossless=True, method=6)
        print(f"Wrote {asset_id}.webp")


if __name__ == "__main__":
    main()
