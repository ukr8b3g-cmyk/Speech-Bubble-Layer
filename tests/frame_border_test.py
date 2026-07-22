import importlib.util
import sys
import types
from pathlib import Path

from PIL import Image


sys.modules["folder_paths"] = types.SimpleNamespace(get_output_directory=lambda: ".")
module_path = Path(__file__).resolve().parents[1] / "nodes_speech_bubble.py"
spec = importlib.util.spec_from_file_location("speech_bubble_frame_test", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def render_frame(**overrides):
    element = {
        "type": "frame",
        "fit_to_canvas": True,
        "border_color": "#ffffff",
        "border_width": 20,
        "inner_stroke_color": "#111111",
        "inner_stroke_width": 4,
        "corner_radius": 0,
        "opacity": 1,
    }
    element.update(overrides)
    return module._render_layer(200, 140, {"elements": [element]}, "", 1)


frame = render_frame()
assert frame.getpixel((5, 70)) == (255, 255, 255, 255)
assert frame.getpixel((20, 70))[:3] == (17, 17, 17)
assert frame.getpixel((30, 70))[3] == 0
assert frame.getpixel((100, 70))[3] == 0

transparent = render_frame(opacity=0.5)
assert 120 <= transparent.getchannel("A").getextrema()[1] <= 128

manual = render_frame(
    fit_to_canvas=False,
    x=30,
    y=20,
    w=100,
    h=80,
    border_width=10,
    inner_stroke_width=0,
    corner_radius=12,
)
assert manual.getpixel((0, 0))[3] == 0
assert manual.getpixel((30, 32))[3] > 0
assert manual.getpixel((80, 60))[3] == 0

axis_widths = render_frame(
    border_width_x=30,
    border_width_y=10,
    inner_stroke_width=0,
)
assert axis_widths.getpixel((20, 70))[3] > 0
assert axis_widths.getpixel((100, 20))[3] == 0
assert axis_widths.getpixel((100, 5))[3] > 0

print("frame border rendering: pass")
