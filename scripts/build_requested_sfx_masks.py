"""Build readable requested SFX and symbol masks with stable local glyph geometry."""

from __future__ import annotations

import random
import unicodedata
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "assets" / "sfx"
STYLE_DIR = ROOT / "tmp" / "imagegen" / "20260718"
FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\epgyobld.ttf"),
    Path(r"C:\Windows\Fonts\YuGothB.ttc"),
    Path(r"C:\Windows\Fonts\meiryo.ttc"),
]


TEXT_TARGETS = {
    # Previous missing list: horizontal additions.
    "icchauyo-horizontal-mask": ("イっちゃうよ！", "horizontal"),
    "hahi-horizontal-mask": ("はひっ！", "horizontal"),
    "iya-horizontal-mask": ("イヤぁっ！", "horizontal"),
    "are-horizontal-mask": ("あれ？", "horizontal"),
    "ogu-horizontal-mask": ("おぐっ！", "horizontal"),
    "uso-horizontal-mask": ("うそ？", "horizontal"),
    "moo-horizontal-mask": ("もぉ～～っ！", "horizontal"),
    "tehepero-horizontal-mask": ("テヘペロ", "horizontal"),
    "kuu-horizontal-mask": ("くぅっ…", "horizontal"),
    "nigai-horizontal-mask": ("にがい…", "horizontal"),
    "daisuki-horizontal-mask": ("だいすき", "horizontal"),
    # Additional reaction words.
    "dokkunn-katakana-mask": ("ドックン", "horizontal"),
    "dokkunn-hiragana-mask": ("どっくん", "horizontal"),
    # Previous missing vertical list.
    "u-dakuten-a-vertical-mask": ("ゔぁ", "vertical"),
    "u-dakuten-small-tsu-vertical-mask": ("ゔっ！", "vertical"),
    "o-dakuten-small-tsu-vertical-mask": ("お゙っ！", "vertical"),
    "u-dakuten-e-vertical-mask": ("ゔぇ", "vertical"),
}


# GPT Image supplies the brush texture. The local glyph mask remains
# authoritative for exact text shape and legibility across the full list.
HYBRID_TEXT_TARGETS = {
    **{
        asset_id: (
            text,
            orientation,
            "vertical-brush-style-v3.png"
            if orientation == "vertical"
            else "horizontal-brush-style-v3.png",
        )
        for asset_id, (text, orientation) in TEXT_TARGETS.items()
    },
    "oke-mask": ("オーケー", "horizontal", "horizontal-brush-style-v4.png"),
}


HYBRID_SYMBOL_TARGETS = {
    "filled-heart-mask": "heart-style-v3.png",
    "anger-mark-small-mask": "anger-style.png",
    "suit-heart-mask": "heart-style-v3.png",
    "suit-club-mask": "clover-style-v2.png",
    "arrow-handdrawn-right-mask": "arrow-handdrawn-style-v2.png",
    "arrow-curved-right-mask": "curved-arrow-style-v2.png",
    "emphasis-lines-mask": "emphasis-style-v2.png",
    "breath-puff-mask": "breath-style-v2.png",
    "music-notes-mask": "music-notes-style-v2.png",
    "lightning-zap-mask": "lightning-style-v2.png",
    "sleep-zzz-mask": "zzz-style-v2.png",
    "motion-swish-mask": "motion-style-v2.png",
    "shock-lines-mask": "shock-style-v2.png",
    "worry-squiggle-mask": "worry-style-v2.png",
    "dizzy-spiral-mask": "spiral-style-v2.png",
    "sparkle-radiant-mask": "radiant-style-v2.png",
    "hot-spring-mask": "hot-spring-style-v2.png",
    "bandage-mask": "bandage-style-v2.png",
}


def font_for(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise FileNotFoundError("No Japanese-capable Windows font was found")


def glyph(text: str, size: int) -> Image.Image:
    has_dakuten = "\u3099" in text or "\u309B" in text
    base_text = "".join(char for char in text if char not in {"\u3099", "\u309B"})
    font = font_for(size)
    probe = Image.new("L", (size * 4, size * 4), 0)
    box = ImageDraw.Draw(probe).textbbox((0, 0), base_text, font=font, stroke_width=2)
    layer = Image.new("L", (max(16, box[2] - box[0] + 32), max(16, box[3] - box[1] + 32)), 0)
    draw = ImageDraw.Draw(layer)
    draw.text(
        (16 - box[0], 16 - box[1]),
        base_text,
        font=font,
        fill=255,
        stroke_width=2,
        stroke_fill=255,
    )
    if has_dakuten:
        # Some Windows brush fonts map decomposed U+3099 to tofu. Draw the
        # two dakuten strokes explicitly while keeping the base glyph exact.
        left = max(8, layer.width // 2 - size // 7)
        top = max(3, 16 - box[1] - size // 5)
        width = max(5, size // 13)
        height = max(8, size // 8)
        draw.rounded_rectangle((left, top, left + width, top + height), radius=width // 2, fill=255)
        draw.rounded_rectangle((left + width * 2, top - size // 24, left + width * 3, top + height - size // 24), radius=width // 2, fill=255)
    bbox = layer.getbbox()
    return layer.crop(bbox) if bbox else Image.new("L", (1, 1), 0)


def render_text(asset_id: str, text: str, orientation: str) -> Image.Image:
    rng = random.Random(asset_id)
    text = unicodedata.normalize("NFD", text)
    if orientation == "vertical":
        canvas = Image.new("L", (512, 512), 0)
        chars = graphemes(text)
        gap = 7
        factors = [1.34 - 0.60 * (i / max(1, len(chars) - 1)) for i in range(len(chars))]
        usable = 438 - gap * max(0, len(chars) - 1)
        base = usable / max(1, sum(factors))
        y = 32
        for index, (char, factor) in enumerate(zip(chars, factors)):
            target_h = max(20, round(base * factor))
            if char in "….":
                target_h = max(14, round(target_h * 0.35))
            src = glyph(char, max(120, round(target_h * 2.15)))
            target_w = max(18, round(target_h * (src.width / max(1, src.height)) * (1.24 - index * .04)))
            src = src.resize((target_w, target_h), Image.Resampling.LANCZOS)
            src = src.filter(ImageFilter.MaxFilter(5 if char not in "…." else 3))
            src = src.rotate(rng.uniform(-6, 6), Image.Resampling.BICUBIC, expand=True)
            x = round((512 - src.width) / 2 + rng.uniform(-6, 6))
            x = max(14, min(512 - src.width - 14, x))
            canvas.paste(src, (x, y), src)
            y += target_h + gap
        return Image.merge("RGBA", (Image.new("L", canvas.size, 255),) * 3 + (canvas,))

    canvas = Image.new("L", (1024, 512), 0)
    chars = graphemes(text)
    factors = [1.25 - .42 * (i / max(1, len(chars) - 1)) for i in range(len(chars))]
    widths = []
    for char, factor in zip(chars, factors):
        src = glyph(char, round(190 * factor))
        widths.append((char, src, factor))
    gap = 8
    total = sum(max(24, src.width) for _, src, _ in widths) + gap * max(0, len(widths) - 1)
    x = max(20, (1024 - total) // 2)
    for index, (char, src, factor) in enumerate(widths):
        target_h = max(40, round(src.height * (1.0 + .14 * (1 - index / max(1, len(widths) - 1)))))
        target_w = max(24, round(src.width * (1.10 + .08 * (1 - index / max(1, len(widths) - 1)))))
        src = src.resize((target_w, target_h), Image.Resampling.LANCZOS)
        src = src.filter(ImageFilter.MaxFilter(5))
        src = src.rotate(rng.uniform(-4.5, 4.5), Image.Resampling.BICUBIC, expand=True)
        y = max(24, (512 - src.height) // 2 + round(rng.uniform(-8, 8)))
        canvas.paste(src, (x, y), src)
        x += target_w + gap
    return Image.merge("RGBA", (Image.new("L", canvas.size, 255),) * 3 + (canvas,))


def render_clean_text(text: str, orientation: str) -> Image.Image:
    """Render stable, readable glyph geometry before applying GPT texture."""
    canvas = Image.new("L", (512, 512), 0)
    chars = graphemes(unicodedata.normalize("NFD", text))
    if orientation == "vertical":
        factors = [1.05 - 0.12 * (i / max(1, len(chars) - 1)) for i in range(len(chars))]
        gap = 8
        usable = 448 - gap * max(0, len(chars) - 1)
        base = usable / max(1, sum(factors))
        y = 30
        for char, factor in zip(chars, factors):
            target_h = max(18, round(base * factor))
            if char in "….":
                target_h = max(14, round(target_h * 0.36))
            src = glyph(char, max(120, round(target_h * 2.0)))
            scale = target_h / max(1, src.height)
            target_w = max(16, round(src.width * scale))
            src = src.resize((target_w, target_h), Image.Resampling.LANCZOS)
            x = max(14, min(512 - target_w - 14, round((512 - target_w) / 2)))
            canvas.paste(src, (x, y), src)
            y += target_h + gap
    else:
        font_size = 178
        rendered = [(char, glyph(char, font_size)) for char in chars]
        gap = 8
        raw_width = sum(max(18, image.width) for _, image in rendered) + gap * max(0, len(rendered) - 1)
        raw_height = max((image.height for _, image in rendered), default=1)
        scale = min(448 / max(1, raw_width), 220 / max(1, raw_height))
        resized = [
            (char, image.resize((max(16, round(image.width * scale)), max(16, round(image.height * scale))), Image.Resampling.LANCZOS))
            for char, image in rendered
        ]
        total_width = sum(image.width for _, image in resized) + gap * max(0, len(resized) - 1)
        x = max(16, round((512 - total_width) / 2))
        for _, image in resized:
            y = max(16, round((512 - image.height) / 2))
            canvas.paste(image, (x, y), image)
            x += image.width + gap
    return Image.merge("RGBA", (Image.new("L", canvas.size, 255),) * 3 + (canvas,))


def chroma_alpha(path: Path) -> Image.Image:
    """Extract the foreground from the flat magenta GPT source."""
    source = Image.open(path).convert("RGB")
    pixels = []
    for red, green, blue in source.getdata():
        distance = max(abs(red - 255), abs(green), abs(blue - 255))
        alpha = max(0, min(255, round((distance - 18) * 255 / 60)))
        pixels.append(alpha)
    result = Image.new("L", source.size, 0)
    result.putdata(pixels)
    return result


def hybrid_text(asset_id: str, text: str, orientation: str, style_name: str) -> Image.Image:
    """Keep exact glyph geometry while borrowing GPT brush texture."""
    exact = render_clean_text(text, orientation).getchannel("A")
    style = chroma_alpha(STYLE_DIR / style_name)
    style = style.point(lambda value: value if value >= 96 else 0)
    bbox = style.getbbox()
    if bbox:
        style = style.crop(bbox)
    texture = ImageOps.fit(style, exact.size, method=Image.Resampling.LANCZOS)
    texture = ImageOps.autocontrast(texture).filter(ImageFilter.GaussianBlur(0.8))
    # Avoid accidental holes from the unrelated GPT source composition while
    # retaining its broad ink-density variation.
    texture = texture.point(lambda value: max(190, value))
    alpha = ImageChops.multiply(exact, texture)
    alpha = ImageChops.lighter(alpha, exact.point(lambda value: round(value * 0.84)))
    return Image.merge("RGBA", (Image.new("L", exact.size, 255),) * 3 + (alpha,))


def hybrid_symbol(style_name: str) -> Image.Image:
    """Use the GPT-generated symbol silhouette as a recolorable white mask."""
    alpha = chroma_alpha(STYLE_DIR / style_name)
    # GPT flat-color sources can leave faint magenta compression noise at the
    # canvas edges. Remove it before calculating the foreground bounding box.
    alpha = alpha.point(lambda value: value if value >= 96 else 0)
    if style_name == "bandage-style-v2.png":
        # The source's pad and perforations are detail, not separate layers.
        # Fill enclosed holes so one bandage remains a single recolorable mark.
        background = ImageOps.invert(alpha)
        exterior = Image.new("L", alpha.size, 0)
        ImageDraw.floodfill(exterior, (0, 0), 255)
        holes = ImageChops.subtract(background, exterior)
        alpha = ImageChops.lighter(alpha, holes)
    bbox = alpha.getbbox()
    if bbox:
        alpha = alpha.crop(bbox)
    canvas = Image.new("L", (512, 512), 0)
    if alpha.width and alpha.height:
        scale = min(430 / alpha.width, 430 / alpha.height)
        size = (max(1, round(alpha.width * scale)), max(1, round(alpha.height * scale)))
        alpha = alpha.resize(size, Image.Resampling.LANCZOS)
        canvas.paste(alpha, ((512 - alpha.width) // 2, (512 - alpha.height) // 2), alpha)
    return Image.merge("RGBA", (Image.new("L", canvas.size, 255),) * 3 + (canvas,))


def graphemes(text: str) -> list[str]:
    clusters: list[str] = []
    for char in text:
        if unicodedata.combining(char) and clusters:
            clusters[-1] += char
        else:
            clusters.append(char)
    return clusters


def render_suit(name: str) -> Image.Image:
    canvas = Image.new("L", (512, 512), 0)
    draw = ImageDraw.Draw(canvas)
    if name == "heart":
        draw.ellipse((74, 55, 260, 255), fill=255)
        draw.ellipse((252, 55, 438, 255), fill=255)
        draw.polygon([(68, 170), (444, 170), (256, 452)], fill=255)
    elif name == "diamond":
        draw.polygon([(256, 42), (456, 256), (256, 470), (56, 256)], fill=255)
    elif name == "spade":
        draw.ellipse((66, 70, 272, 300), fill=255)
        draw.ellipse((240, 70, 446, 300), fill=255)
        draw.polygon([(58, 210), (454, 210), (256, 424)], fill=255)
        draw.polygon([(224, 390), (288, 390), (274, 476), (238, 476)], fill=255)
    elif name == "club":
        draw.ellipse((62, 78, 270, 286), fill=255)
        draw.ellipse((242, 78, 450, 286), fill=255)
        draw.ellipse((154, 190, 358, 394), fill=255)
        draw.polygon([(224, 338), (288, 338), (274, 474), (238, 474)], fill=255)
    return Image.merge("RGBA", (Image.new("L", canvas.size, 255),) * 3 + (canvas,))


def save(image: Image.Image, asset_id: str) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT / f"{asset_id}.webp", "WEBP", lossless=True, method=6)


def main() -> None:
    for asset_id, (text, orientation) in TEXT_TARGETS.items():
        save(render_text(asset_id, text, orientation), asset_id)
    for asset_id, (text, orientation, style_name) in HYBRID_TEXT_TARGETS.items():
        save(hybrid_text(asset_id, text, orientation, style_name), asset_id)
    for name in ("heart", "spade", "diamond", "club"):
        save(render_suit(name), f"suit-{name}-mask")
    for asset_id, style_name in HYBRID_SYMBOL_TARGETS.items():
        save(hybrid_symbol(style_name), asset_id)


if __name__ == "__main__":
    main()
