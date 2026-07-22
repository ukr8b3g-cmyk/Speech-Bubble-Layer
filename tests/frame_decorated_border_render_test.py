import importlib.util
import sys
import types
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.modules["folder_paths"] = types.SimpleNamespace(get_output_directory=lambda: ".")
spec = importlib.util.spec_from_file_location("speech_bubble_decorated_border_test", ROOT / "nodes_speech_bubble.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

preset = module._FRAME_PRESETS.get("pop-animal-decorated-border-v1")
if preset is None:
    print("frame decorated-border rendering: skipped (no decorated frame installed)")
    raise SystemExit(0)
assert preset["render_mode"] == "decorated-border"
assert not preset.get("asset_src")
assert preset.get("preview_src")
assert len(preset["decorated_corners"]) == 4
assert set(preset["decorated_edges"]) == {"top", "bottom", "left", "right"}

# Layout keeps independent assets proportional and inside the canvas.
part_sizes = {
    "corner_tl": (420, 420), "corner_tr": (420, 420),
    "corner_bl": (420, 420), "corner_br": (420, 420),
    "bunny": (320, 320), "cat": (320, 320), "bear": (320, 320),
    "mouse": (320, 320), "dog": (320, 320), "flowers": (300, 260), "stars": (300, 260),
}
placements = module._decorated_border_layout(
    1024, 1536, part_sizes, preset["decorated_edges"], .28, preset["decorated_layout"]
)
assert len(placements) > 12
for key, x, y, width, height in placements:
    assert key in part_sizes
    assert width > 0 and height > 0
    assert x >= -1e-6 and y >= -1e-6
    assert x + width <= 1024 + 1e-6
    assert y + height <= 1536 + 1e-6
    source_ratio = part_sizes[key][0] / part_sizes[key][1]
    draw_ratio = width / height
    assert abs(source_ratio - draw_ratio) < 1e-6

# The procedural border itself is continuous because it is drawn once rather than tiled.
border_only = Image.new("RGBA", (480, 720), (0, 0, 0, 0))
assert module._draw_procedural_base_border(border_only, preset, .28)
alpha = border_only.getchannel("A")
for x in range(12, 468):
    assert any(alpha.getpixel((x, y)) > 0 for y in range(0, 18)), f"top border gap at x={x}"
for y in range(12, 708):
    assert any(alpha.getpixel((x, y)) > 0 for x in range(0, 18)), f"left border gap at y={y}"

# Full Python/Pillow rendering works without runtimeAsset.
layer = Image.new("RGBA", (1024, 1536), (0, 0, 0, 0))
element = {
    "type": "frame",
    "frame_preset_id": preset["id"],
    "frame_mode": "decorated-border",
    "fit_to_canvas": True,
    "frame_scale": 28,
    "frame_inset": 0,
    "opacity": 1,
    "rotation": 0,
}
assert module._draw_frame_asset(layer, element, 1.0, 1024, 1536)
assert layer.getchannel("A").getbbox() is not None
assert layer.getchannel("A").getpixel((512, 768)) == 0

print("frame decorated-border rendering: pass")
