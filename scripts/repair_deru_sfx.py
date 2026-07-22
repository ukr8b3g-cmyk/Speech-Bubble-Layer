"""Regenerate the vertical でるっ！ mask without the swollen brush treatment."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "assets" / "sfx" / "deru-small-tsu-mask.webp"
FONT_PATH = Path(r"C:\Windows\Fonts\HGRGY.TTC")
FONT_INDEX = 1  # HGP行書体
CANVAS_SIZE = 512


def glyph_alpha(char: str, font_size: int) -> Image.Image:
    font = ImageFont.truetype(str(FONT_PATH), font_size, index=FONT_INDEX)
    probe = Image.new("L", (font_size * 3, font_size * 3), 0)
    box = ImageDraw.Draw(probe).textbbox((0, 0), char, font=font)
    layer = Image.new("L", (box[2] - box[0] + 24, box[3] - box[1] + 24), 0)
    ImageDraw.Draw(layer).text((12 - box[0], 12 - box[1]), char, font=font, fill=255)
    bbox = layer.getbbox()
    return layer.crop(bbox) if bbox else Image.new("L", (1, 1), 0)


def main() -> None:
    if not FONT_PATH.exists():
        raise FileNotFoundError(FONT_PATH)

    text = "でるっ！"
    chars = list(text)
    factors = [1.22, 1.08, 0.86, 0.74]
    gap = 8
    usable_height = 430 - gap * (len(chars) - 1)
    base_height = usable_height / sum(factors)
    rng = random.Random("deru-small-tsu-mask-repair")
    canvas = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
    y = 34

    for index, (char, factor) in enumerate(zip(chars, factors)):
        target_h = max(24, round(base_height * factor))
        glyph = glyph_alpha(char, max(120, round(target_h * 2.25)))
        aspect = glyph.width / max(1, glyph.height)
        target_w = max(24, round(target_h * aspect * (1.08 - index * 0.05)))
        glyph = glyph.resize((target_w, target_h), Image.Resampling.LANCZOS)
        glyph = glyph.rotate(rng.uniform(-3.0, 3.0), resample=Image.Resampling.BICUBIC, expand=True)
        x = round((CANVAS_SIZE - glyph.width) / 2 + rng.uniform(-7, 7))
        x = max(16, min(CANVAS_SIZE - glyph.width - 16, x))
        canvas.paste(glyph, (x, y), glyph)
        y += target_h + gap

    rgba = Image.merge("RGBA", (Image.new("L", canvas.size, 255),) * 3 + (canvas,))
    rgba.save(OUTPUT, "WEBP", lossless=True, method=6)
    print(f"{OUTPUT}: {rgba.width}x{rgba.height}")


if __name__ == "__main__":
    main()
