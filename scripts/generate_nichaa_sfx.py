"""Generate the horizontal Japanese SFX mask for ニチャア."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "assets" / "sfx" / "nichaa-mask.webp"
FONT_PATH = Path(r"C:\Windows\Fonts\HGRGY.TTC")
FONT_INDEX = 1  # HGP行書体
CANVAS_SIZE = (512, 300)


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

    chars = list("ニチャア")
    factors = [1.18, 1.08, 0.96, 0.82]
    rng = random.Random("nichaa-mask")
    canvas = Image.new("L", CANVAS_SIZE, 0)
    glyphs = []
    for index, (char, factor) in enumerate(zip(chars, factors)):
        glyph = glyph_alpha(char, 190)
        target_h = round(105 * factor)
        target_w = max(24, round(glyph.width * target_h / max(1, glyph.height) * (1.05 - index * 0.045)))
        glyph = glyph.resize((target_w, target_h), Image.Resampling.LANCZOS)
        glyphs.append(glyph.rotate(rng.uniform(-4.0, 4.0), resample=Image.Resampling.BICUBIC, expand=True))

    gap = 2
    total_width = sum(glyph.width for glyph in glyphs) + gap * (len(glyphs) - 1)
    available_width = CANVAS_SIZE[0] - 32
    if total_width > available_width:
        scale = available_width / total_width
        glyphs = [
            glyph.resize(
                (max(1, round(glyph.width * scale)), max(1, round(glyph.height * scale))),
                Image.Resampling.LANCZOS,
            )
            for glyph in glyphs
        ]
        total_width = sum(glyph.width for glyph in glyphs) + gap * (len(glyphs) - 1)
    x = max(14, (CANVAS_SIZE[0] - total_width) // 2)
    for index, glyph in enumerate(glyphs):
        y = round((CANVAS_SIZE[1] - glyph.height) / 2 + rng.uniform(-8, 8))
        y = max(18, min(CANVAS_SIZE[1] - glyph.height - 18, y))
        canvas.paste(glyph, (x, y), glyph)
        x += glyph.width + gap

    rgba = Image.merge("RGBA", (Image.new("L", canvas.size, 255),) * 3 + (canvas,))
    rgba.save(OUTPUT, "WEBP", lossless=True, method=6)
    print(f"{OUTPUT}: {rgba.width}x{rgba.height}")


if __name__ == "__main__":
    main()
