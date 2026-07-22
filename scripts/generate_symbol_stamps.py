from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw


SIZE = 512
SCALE = 4
CANVAS = SIZE * SCALE
WHITE = (255, 255, 255, 255)
OUT_DIR = Path(__file__).resolve().parents[1] / "web" / "assets" / "sfx"


def sc(value: float) -> int:
    return round(value * SCALE)


def points(values):
    return [(sc(x), sc(y)) for x, y in values]


def canvas():
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image)


def save(name: str, image: Image.Image):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image.resize((SIZE, SIZE), Image.Resampling.LANCZOS).save(
        OUT_DIR / name, "WEBP", lossless=True, method=6
    )


def line(draw, coords, width=18, joint="curve"):
    draw.line(points(coords), fill=WHITE, width=sc(width), joint=joint)


def polygon(draw, coords):
    draw.polygon(points(coords), fill=WHITE)


def bezier(p0, p1, p2, p3, count=48):
    result = []
    for index in range(count + 1):
        t = index / count
        u = 1 - t
        result.append(
            (
                u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
            )
        )
    return result


def arrow_head(draw, tip, direction, length=92, spread=54, filled=True, width=16):
    angle = math.atan2(direction[1], direction[0])
    back = (tip[0] - math.cos(angle) * length, tip[1] - math.sin(angle) * length)
    left = (back[0] + math.cos(angle + math.pi / 2) * spread, back[1] + math.sin(angle + math.pi / 2) * spread)
    right = (back[0] + math.cos(angle - math.pi / 2) * spread, back[1] + math.sin(angle - math.pi / 2) * spread)
    if filled:
        polygon(draw, [tip, left, right])
    else:
        line(draw, [left, tip, right], width)


def thick_arrow():
    image, draw = canvas()
    polygon(draw, [(54, 206), (302, 206), (302, 130), (468, 256), (302, 382), (302, 306), (54, 306)])
    return image


def thin_arrow():
    image, draw = canvas()
    line(draw, [(58, 256), (444, 256)], 15)
    arrow_head(draw, (454, 256), (1, 0), 105, 64, False, 15)
    return image


def handdrawn_arrow():
    image, draw = canvas()
    line(draw, [(60, 270), (145, 258), (232, 266), (332, 250), (442, 260)], 21)
    line(draw, [(64, 278), (152, 267), (238, 274), (336, 258), (442, 267)], 8)
    arrow_head(draw, (456, 261), (1, 0), 105, 66, False, 20)
    return image


def curved_arrow():
    image, draw = canvas()
    curve = bezier((76, 352), (110, 92), (360, 82), (426, 232))
    line(draw, curve, 20)
    tangent = (curve[-1][0] - curve[-4][0], curve[-1][1] - curve[-4][1])
    arrow_head(draw, curve[-1], tangent, 92, 56, True)
    return image


def wavy_arrow():
    image, draw = canvas()
    curve = []
    for index in range(81):
        x = 52 + index * 4.9
        y = 256 + math.sin(index / 8.2) * 70
        curve.append((x, y))
    line(draw, curve, 20)
    arrow_head(draw, curve[-1], (1, math.cos(80 / 8.2) * 70 / 4.9 / 8.2), 92, 55, True)
    return image


def loop_arrow():
    image, draw = canvas()
    curve = bezier((120, 330), (35, 100), (430, 38), (390, 270)) + bezier((390, 270), (365, 430), (170, 430), (135, 300))[1:]
    line(draw, curve[:-8], 18)
    tangent = (curve[-9][0] - curve[-13][0], curve[-9][1] - curve[-13][1])
    arrow_head(draw, curve[-9], tangent, 84, 50, True)
    return image


def double_arrow():
    image, draw = canvas()
    line(draw, [(86, 256), (426, 256)], 18)
    arrow_head(draw, (452, 256), (1, 0), 90, 52, True)
    arrow_head(draw, (60, 256), (-1, 0), 90, 52, True)
    return image


def star_points(cx, cy, outer, inner, count=5, rotation=-math.pi / 2):
    return [
        (
            cx + math.cos(rotation + index * math.pi / count) * (outer if index % 2 == 0 else inner),
            cy + math.sin(rotation + index * math.pi / count) * (outer if index % 2 == 0 else inner),
        )
        for index in range(count * 2)
    ]


def star_outline():
    image, draw = canvas()
    coords = star_points(256, 256, 190, 84)
    line(draw, coords + [coords[0]], 22)
    return image


def star_filled():
    image, draw = canvas()
    polygon(draw, star_points(256, 256, 190, 83))
    return image


def sparkle_four():
    image, draw = canvas()
    polygon(draw, [(256, 38), (286, 218), (474, 256), (286, 294), (256, 474), (226, 294), (38, 256), (226, 218)])
    return image


def sparkle_cluster():
    image, draw = canvas()
    for cx, cy, outer in [(218, 236, 154), (382, 130, 64), (378, 364, 78), (92, 356, 52)]:
        inner = outer * 0.16
        polygon(draw, [(cx, cy - outer), (cx + inner, cy - inner), (cx + outer, cy), (cx + inner, cy + inner), (cx, cy + outer), (cx - inner, cy + inner), (cx - outer, cy), (cx - inner, cy - inner)])
    return image


def radiant_star():
    image, draw = canvas()
    polygon(draw, star_points(256, 256, 92, 40, 8))
    for angle in range(0, 360, 30):
        radians = math.radians(angle)
        line(draw, [(256 + math.cos(radians) * 126, 256 + math.sin(radians) * 126), (256 + math.cos(radians) * 210, 256 + math.sin(radians) * 210)], 12)
    return image


def rough_circle(double=False):
    image, draw = canvas()
    random.seed(73 if double else 41)
    for loop_index in range(2 if double else 1):
        coords = []
        for index in range(97):
            angle = index / 96 * math.tau
            radius_x = 174 + loop_index * 10 + random.uniform(-8, 8)
            radius_y = 145 + loop_index * 8 + random.uniform(-7, 7)
            coords.append((256 + math.cos(angle) * radius_x, 256 + math.sin(angle) * radius_y))
        line(draw, coords, 12 if double else 17)
    return image


def scribble_ball():
    image, draw = canvas()
    random.seed(91)
    for loop_index in range(13):
        cx = 256 + random.uniform(-34, 34)
        cy = 256 + random.uniform(-30, 30)
        rx = random.uniform(105, 180)
        ry = random.uniform(90, 165)
        rotation = random.uniform(-0.8, 0.8)
        coords = []
        for index in range(49):
            angle = index / 48 * math.tau
            x, y = math.cos(angle) * rx, math.sin(angle) * ry
            coords.append((cx + x * math.cos(rotation) - y * math.sin(rotation), cy + x * math.sin(rotation) + y * math.cos(rotation)))
        line(draw, coords, 8)
    return image


def rough_underline():
    image, draw = canvas()
    line(draw, [(52, 278), (135, 263), (224, 271), (318, 247), (460, 259)], 25)
    line(draw, [(84, 312), (182, 301), (285, 308), (420, 286)], 10)
    return image


def anger_small():
    image, draw = canvas()
    line(draw, [(256, 58), (256, 186), (326, 116)], 28)
    line(draw, [(454, 256), (326, 256), (396, 326)], 28)
    line(draw, [(256, 454), (256, 326), (186, 396)], 28)
    line(draw, [(58, 256), (186, 256), (116, 186)], 28)
    return image


def drop_shape(draw, cx, cy, width, height):
    coords = bezier((cx, cy - height / 2), (cx + width * 0.54, cy - height * 0.05), (cx + width * 0.6, cy + height * 0.36), (cx, cy + height / 2), 30)
    coords += bezier((cx, cy + height / 2), (cx - width * 0.6, cy + height * 0.36), (cx - width * 0.54, cy - height * 0.05), (cx, cy - height / 2), 30)[1:]
    polygon(draw, coords)


def sweat(single=False):
    image, draw = canvas()
    drop_shape(draw, 240 if single else 172, 256, 145, 280)
    if not single:
        drop_shape(draw, 350, 300, 92, 190)
    return image


def emphasis_lines():
    image, draw = canvas()
    line(draw, [(104, 154), (218, 256)], 22)
    line(draw, [(256, 92), (272, 224)], 22)
    line(draw, [(408, 134), (314, 244)], 22)
    return image


def shock_lines():
    image, draw = canvas()
    for angle in [-62, -30, 0, 30, 62]:
        radians = math.radians(angle)
        start = (256 + math.sin(radians) * 104, 348 - math.cos(radians) * 42)
        end = (256 + math.sin(radians) * 205, 256 - math.cos(radians) * 190)
        line(draw, [start, end], 17)
    return image


def tension_lines():
    image, draw = canvas()
    for index, x in enumerate([120, 182, 250, 322, 392]):
        top = 70 + (index % 2) * 36
        bottom = 440 - ((index + 1) % 2) * 42
        line(draw, [(x, top), (x + (-8 if index % 2 else 8), bottom)], 16)
    return image


def worry_squiggle():
    image, draw = canvas()
    coords = []
    for index in range(91):
        x = 50 + index * 4.55
        y = 256 + math.sin(index / 5.2) * 52 + math.sin(index / 2.1) * 13
        coords.append((x, y))
    line(draw, coords, 18)
    return image


def breath_puff():
    image, draw = canvas()
    for cx, cy, radius in [(184, 278, 88), (250, 230, 105), (330, 270, 96), (392, 252, 70)]:
        draw.ellipse((sc(cx - radius), sc(cy - radius), sc(cx + radius), sc(cy + radius)), fill=WHITE)
    line(draw, [(100, 330), (48, 374)], 18)
    return image


def dizzy_spiral():
    image, draw = canvas()
    coords = []
    for index in range(181):
        angle = index / 18
        radius = 7 + index * 0.92
        coords.append((256 + math.cos(angle) * radius, 256 + math.sin(angle) * radius))
    line(draw, coords, 17)
    return image


def hot_spring():
    image, draw = canvas()
    for offset in [-92, 0, 92]:
        curve = bezier((256 + offset, 92), (205 + offset, 160), (310 + offset, 210), (256 + offset, 284))
        line(draw, curve, 20)
    line(draw, [(74, 338), (438, 338)], 22)
    line(draw, [(102, 382), (410, 382)], 22)
    return image


def bandage():
    image, _ = canvas()
    strip = Image.new("RGBA", (sc(360), sc(112)), (0, 0, 0, 0))
    strip_draw = ImageDraw.Draw(strip)
    strip_draw.rounded_rectangle((0, 0, strip.width - 1, strip.height - 1), radius=sc(38), fill=WHITE)
    for x in range(sc(72), sc(290), sc(44)):
        strip_draw.ellipse((x, sc(44), x + sc(10), sc(54)), fill=(0, 0, 0, 0))
    first = strip.rotate(42, resample=Image.Resampling.BICUBIC, expand=True)
    second = strip.rotate(-42, resample=Image.Resampling.BICUBIC, expand=True)
    image.alpha_composite(first, ((CANVAS - first.width) // 2, (CANVAS - first.height) // 2))
    image.alpha_composite(second, ((CANVAS - second.width) // 2, (CANVAS - second.height) // 2))
    return image


def music_notes():
    image, draw = canvas()
    draw.ellipse((sc(72), sc(310), sc(212), sc(430)), fill=WHITE)
    draw.ellipse((sc(298), sc(274), sc(438), sc(394)), fill=WHITE)
    line(draw, [(190, 358), (190, 116)], 30)
    line(draw, [(416, 322), (416, 80)], 30)
    line(draw, [(190, 116), (416, 80)], 35)
    return image


def sleep_zzz():
    image, draw = canvas()
    for x, y, size in [(72, 304, 150), (218, 210, 116), (334, 110, 82)]:
        line(draw, [(x, y), (x + size, y), (x, y + size), (x + size, y + size)], max(16, size * 0.14))
    return image


def lightning():
    image, draw = canvas()
    polygon(draw, [(288, 38), (112, 286), (236, 280), (176, 474), (416, 210), (286, 214)])
    return image


def motion_swish():
    image, draw = canvas()
    for offset, width in [(0, 24), (58, 17), (112, 12)]:
        curve = bezier((52, 362 - offset), (168, 120 - offset * 0.25), (360, 140 + offset * 0.2), (460, 272 + offset * 0.15))
        line(draw, curve, width)
    return image


ASSETS = {
    "arrow-thick-right-mask.webp": thick_arrow,
    "arrow-thin-right-mask.webp": thin_arrow,
    "arrow-handdrawn-right-mask.webp": handdrawn_arrow,
    "arrow-curved-right-mask.webp": curved_arrow,
    "arrow-wavy-right-mask.webp": wavy_arrow,
    "arrow-loop-mask.webp": loop_arrow,
    "arrow-double-mask.webp": double_arrow,
    "star-outline-mask.webp": star_outline,
    "star-filled-mask.webp": star_filled,
    "sparkle-four-mask.webp": sparkle_four,
    "sparkle-cluster-mask.webp": sparkle_cluster,
    "sparkle-radiant-mask.webp": radiant_star,
    "rough-circle-mask.webp": lambda: rough_circle(False),
    "rough-double-circle-mask.webp": lambda: rough_circle(True),
    "scribble-ball-mask.webp": scribble_ball,
    "rough-underline-mask.webp": rough_underline,
    "anger-mark-small-mask.webp": anger_small,
    "sweat-drop-mask.webp": lambda: sweat(True),
    "sweat-drops-mask.webp": lambda: sweat(False),
    "emphasis-lines-mask.webp": emphasis_lines,
    "shock-lines-mask.webp": shock_lines,
    "tension-lines-mask.webp": tension_lines,
    "worry-squiggle-mask.webp": worry_squiggle,
    "breath-puff-mask.webp": breath_puff,
    "dizzy-spiral-mask.webp": dizzy_spiral,
    "hot-spring-mask.webp": hot_spring,
    "bandage-mask.webp": bandage,
    "music-notes-mask.webp": music_notes,
    "sleep-zzz-mask.webp": sleep_zzz,
    "lightning-zap-mask.webp": lightning,
    "motion-swish-mask.webp": motion_swish,
}


if __name__ == "__main__":
    for filename, factory in ASSETS.items():
        save(filename, factory())
    print(f"generated {len(ASSETS)} symbol stamps in {OUT_DIR}")
