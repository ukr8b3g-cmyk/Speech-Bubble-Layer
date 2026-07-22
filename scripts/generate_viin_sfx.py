"""Generate the horizontal Japanese SFX mask for ヴィ～ン."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "assets" / "sfx" / "viin-mask.webp"
FONT_PATH = Path(r"C:\Windows\Fonts\HGRGY.TTC")
FONT_INDEX = 1  # HGP行書体


def main() -> None:
    if not FONT_PATH.exists():
        raise FileNotFoundError(FONT_PATH)

    text = "ヴィ～ン"
    font = ImageFont.truetype(str(FONT_PATH), 154, index=FONT_INDEX)
    probe = Image.new("L", (1200, 300), 0)
    draw = ImageDraw.Draw(probe)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=2)
    layer = Image.new("L", (bbox[2] - bbox[0] + 48, bbox[3] - bbox[1] + 48), 0)
    ImageDraw.Draw(layer).text(
        (24 - bbox[0], 24 - bbox[1]),
        text,
        font=font,
        fill=255,
        stroke_width=2,
        stroke_fill=255,
    )
    content = layer.crop(layer.getbbox())
    # Keep the broad horizontal silhouette, but leave a transparent breathing
    # margin so the editor's tint/outline pass remains clean.
    margin_x, margin_y = 22, 20
    canvas = Image.new("L", (content.width + margin_x * 2, content.height + margin_y * 2), 0)
    canvas.paste(content, (margin_x, margin_y))
    rgba = Image.merge("RGBA", (Image.new("L", canvas.size, 255),) * 3 + (canvas,))
    rgba.save(OUTPUT, "WEBP", lossless=True, method=6)
    print(f"{OUTPUT}: {rgba.width}x{rgba.height}")


if __name__ == "__main__":
    main()
