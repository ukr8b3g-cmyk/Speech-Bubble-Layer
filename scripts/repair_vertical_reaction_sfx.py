"""Repair vertical reaction SFX whose old masks collapsed into thin bars."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "web" / "assets" / "sfx"
FONT_PATH = Path(r"C:\Windows\Fonts\epgyobld.ttf")
FONT_INDEX = 0  # Epson 行書体 Bold
CANVAS_SIZE = 512

TARGETS = {
    "uguuu-ellipsis-mask": "うぐぅ...",
    "au-small-tsu-mask": "あぅっ！",
    "kaha-small-tsu-mask": "かはっ！",
    "igu-small-tsu-mask": "イグッ！",
    "aha-small-tsu-mask": "あはっ",
    "aha-katakana-small-tsu-mask": "アハッ",
    "hachun-small-tsu-mask": "ぱちゅんっ",
    "n-small-tsu-ellipsis-mask": "ん゛っ…",
    "u-small-tsu-ellipsis-mask": "うっ…",
    "iccha-mask": "いっちゃ",
    "ii-small-tsu-mask": "いいっ",
    "tehepero-mask": "テヘペロ",
    "iee-small-tsu-mask": "イエーイ！",
    "oke-mask": "オーケー",
    "damee-mask": "ダメぇ",
    "u-dakuten-long-small-tsu-mask": "う゛～っ！",
    "moo-long-small-tsu-mask": "もぉ～～っ！",
    "e-small-tsu-question-mask": "えっ？",
    "yadaa-mask": "やだぁ",
}


def glyph_alpha(char: str, font_size: int) -> Image.Image:
    if char in {".", "…"}:
        side = max(160, font_size * 2)
        layer = Image.new("L", (side, side), 0)
        draw = ImageDraw.Draw(layer)
        radius = max(5, round(font_size * (0.025 if char == "." else 0.020)))
        center_x = side // 2
        if char == ".":
            draw.ellipse((center_x - radius, side // 2 - radius, center_x + radius, side // 2 + radius), fill=255)
        else:
            step = max(radius * 3, round(font_size * 0.19))
            center_y = side // 2 - step
            for _ in range(3):
                draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius), fill=255)
                center_y += step
        bbox = layer.getbbox()
        return layer.crop(bbox) if bbox else Image.new("L", (1, 1), 0)

    if char in {"ー", "～"}:
        # In vertical Japanese lettering these marks rotate with the writing
        # flow. Rendering the font glyph directly leaves a conspicuous
        # horizontal bar, which is exactly the failure mode this repair fixes.
        side = max(160, font_size * 2)
        layer = Image.new("L", (side, side), 0)
        draw = ImageDraw.Draw(layer)
        f = float(font_size)
        if char == "ー":
            points = [
                (f * 0.86, f * 1.70),
                (f * 0.72, f * 1.34),
                (f * 0.77, f * 0.94),
                (f * 1.07, f * 0.34),
            ]
            draw.line(points, fill=255, width=max(12, round(f * 0.19)), joint="curve")
        else:
            points = [
                (f * 0.88, f * 1.72),
                (f * 0.72, f * 1.42),
                (f * 1.08, f * 1.12),
                (f * 0.74, f * 0.83),
                (f * 1.05, f * 0.51),
                (f * 0.86, f * 0.27),
            ]
            draw.line(points, fill=255, width=max(10, round(f * 0.15)), joint="curve")
        bbox = layer.getbbox()
        return layer.crop(bbox) if bbox else Image.new("L", (1, 1), 0)

    font = ImageFont.truetype(str(FONT_PATH), font_size, index=FONT_INDEX)
    probe = Image.new("L", (font_size * 3, font_size * 3), 0)
    box = ImageDraw.Draw(probe).textbbox((0, 0), char, font=font)
    if box[2] <= box[0] or box[3] <= box[1]:
        return Image.new("L", (1, 1), 0)
    layer = Image.new("L", (box[2] - box[0] + 24, box[3] - box[1] + 24), 0)
    ImageDraw.Draw(layer).text((12 - box[0], 12 - box[1]), char, font=font, fill=255)
    bbox = layer.getbbox()
    return layer.crop(bbox) if bbox else Image.new("L", (1, 1), 0)


def render(asset_id: str, text: str) -> Image.Image:
    chars = list(text)
    gap = 7
    usable_height = 432 - gap * (len(chars) - 1)
    # The reference style is deliberately top-heavy: the first glyphs carry
    # the visual impact and the lower glyphs taper toward the end.
    factors = [1.36 - 0.64 * (index / max(1, len(chars) - 1)) for index in range(len(chars))]
    base_height = usable_height / sum(factors)
    rng = random.Random(asset_id)
    canvas = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
    y = 34

    for index, (char, factor) in enumerate(zip(chars, factors)):
        target_h = max(22, round(base_height * factor))
        if char == ".":
            target_h = max(14, round(target_h * 0.24))
        elif char == "…":
            target_h = max(42, round(target_h * 0.48))
        glyph = glyph_alpha(char, max(120, round(target_h * 2.25)))
        aspect = glyph.width / max(1, glyph.height)
        if char in ".…、。":
            target_w = max(12, round(target_h * aspect * 0.78))
        else:
            target_w = max(30, round(target_h * aspect * (1.28 - index * 0.065)))
        glyph = glyph.resize((target_w, target_h), Image.Resampling.LANCZOS)
        # Build weight before the small rotation so narrow strokes do not
        # collapse at thumbnail size. Keep punctuation lighter than glyphs.
        if char in ".…、。":
            glyph = glyph.filter(ImageFilter.MaxFilter(3))
        else:
            weight = 7 if index < max(2, len(chars) // 3) else 5
            glyph = glyph.filter(ImageFilter.MaxFilter(weight))
        glyph = glyph.rotate(rng.uniform(-5.5, 5.5), resample=Image.Resampling.BICUBIC, expand=True)
        x = round((CANVAS_SIZE - glyph.width) / 2 + rng.uniform(-7, 7))
        x = max(16, min(CANVAS_SIZE - glyph.width - 16, x))
        canvas.paste(glyph, (x, y), glyph)
        y += target_h + gap

    return Image.merge("RGBA", (Image.new("L", canvas.size, 255),) * 3 + (canvas,))


def main() -> None:
    if not FONT_PATH.exists():
        raise FileNotFoundError(FONT_PATH)
    for asset_id, text in TARGETS.items():
        output = OUTPUT_DIR / f"{asset_id}.webp"
        image = render(asset_id, text)
        image.save(output, "WEBP", lossless=True, method=6)
        print(f"{asset_id}: {text} -> {image.width}x{image.height}")


if __name__ == "__main__":
    main()
