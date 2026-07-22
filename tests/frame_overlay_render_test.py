import importlib.util
import sys
import types
from pathlib import Path

from PIL import Image


sys.modules["folder_paths"] = types.SimpleNamespace(get_output_directory=lambda: ".")
module_path = Path(__file__).resolve().parents[1] / "nodes_speech_bubble.py"
spec = importlib.util.spec_from_file_location("speech_bubble_overlay_test", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = Image.new("RGBA", (4, 2), (255, 0, 0, 255))
for x in range(2, 4):
    for y in range(2):
        source.putpixel((x, y), (0, 0, 255, 255))

preset_id = "overlay-test"
module._FRAME_PRESETS[preset_id] = {
    "id": preset_id,
    "render_mode": "full-overlay",
    "fit_mode": "cover",
}
module._FRAME_ASSETS[preset_id] = module_path
module._load_cached_rgba = lambda _path: source.copy()


def render(fit_mode):
    layer = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    element = {
        "type": "frame",
        "frame_preset_id": preset_id,
        "frame_mode": "full-overlay",
        "fit_mode": fit_mode,
        "frame_scale": 100,
        "fit_to_canvas": True,
        "opacity": 1,
    }
    assert module._draw_frame_asset(layer, element, 1, 8, 8)
    return layer


cover = render("cover")
assert cover.getchannel("A").getextrema() == (255, 255)

contain = render("contain")
assert contain.getpixel((4, 0))[3] == 0
assert contain.getpixel((4, 4))[3] == 255

stretch = render("stretch")
assert stretch.getchannel("A").getextrema() == (255, 255)

tile = render("tile")
assert tile.getchannel("A").getextrema() == (255, 255)

print("frame overlay fit modes: pass")
