import importlib.util
import sys
import types
from pathlib import Path

from PIL import Image


sys.modules["folder_paths"] = types.SimpleNamespace(get_output_directory=lambda: ".")
module_path = Path(__file__).resolve().parents[1] / "nodes_speech_bubble.py"
spec = importlib.util.spec_from_file_location("speech_bubble_preset_test", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

layer = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
module._draw_bubble(
    layer,
    {
        "type": "bubble",
        "shape": "oval",
        "x": 170,
        "y": 110,
        "w": 170,
        "h": 260,
        "fill": "#ffffff",
        "stroke": "#111111",
        "stroke_width": 2,
        "decoration_style": "radiant",
    },
    1,
)

bounds = layer.getchannel("A").getbbox()
assert bounds is not None
assert bounds[0] < 170 or bounds[1] < 110 or bounds[2] > 340 or bounds[3] > 370
assert layer.getpixel((255, 240))[3] > 0

opaque = module._render_layer(
    512,
    512,
    {"elements": [{"type": "bubble", "shape": "oval", "x": 160, "y": 120, "w": 190, "h": 220, "fill": "#ffffff", "stroke": "#111111", "stroke_width": 2, "opacity": 1}]},
    "",
    1,
)
transparent = module._render_layer(
    512,
    512,
    {"elements": [{"type": "bubble", "shape": "oval", "x": 160, "y": 120, "w": 190, "h": 220, "fill": "#ffffff", "stroke": "#111111", "stroke_width": 2, "opacity": 0.35}]},
    "",
    1,
)
assert transparent.getchannel("A").getextrema()[1] < opaque.getchannel("A").getextrema()[1]

solid = module._render_layer(
    256,
    256,
    {"elements": [{"type": "bubble", "shape": "oval", "x": 48, "y": 48, "w": 160, "h": 140, "fill": "#ffffff", "stroke": "#111111", "stroke_width": 4, "stroke_style": "solid"}]},
    "",
    1,
)
for removed_style in ("dashed", "dotted"):
    legacy = module._render_layer(
        256,
        256,
        {"elements": [{"type": "bubble", "shape": "oval", "x": 48, "y": 48, "w": 160, "h": 140, "fill": "#ffffff", "stroke": "#111111", "stroke_width": 4, "stroke_style": removed_style}]},
        "",
        1,
    )
    assert legacy.tobytes() == solid.tobytes()

print("special bubble preset rendering: pass")
