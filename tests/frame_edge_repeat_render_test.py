import importlib.util
import sys
import tempfile
import types
from pathlib import Path

from PIL import Image


sys.modules["folder_paths"] = types.SimpleNamespace(get_output_directory=lambda: ".")
module_path = Path(__file__).resolve().parents[1] / "nodes_speech_bubble.py"
spec = importlib.util.spec_from_file_location("speech_bubble_edge_repeat_test", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

preset_id = "test-edge-repeat-frame"
part_sizes = {
    "corner_tl": (320, 320),
    "corner_tr": (320, 320),
    "corner_bl": (320, 320),
    "corner_br": (320, 320),
    "edge_top": (220, 320),
    "edge_bottom": (220, 320),
    "edge_left": (320, 220),
    "edge_right": (320, 220),
}

expected_counts = {
    (832, 1216): {"edge_top": 13, "edge_bottom": 13, "edge_left": 21, "edge_right": 21},
    (1024, 1024): {"edge_top": 13, "edge_bottom": 13, "edge_left": 13, "edge_right": 13},
    (1024, 1536): {"edge_top": 13, "edge_bottom": 13, "edge_left": 22, "edge_right": 22},
}

with tempfile.TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    parts = {}
    for key, size in part_sizes.items():
        path = temporary_root / f"{key}.webp"
        Image.new("RGBA", size, (255, 255, 255, 255)).save(path, format="WEBP", lossless=True)
        parts[key] = str(path)

    module._FRAME_PRESETS[preset_id] = {
        "id": preset_id,
        "render_mode": "edge-repeat",
        "default_scale": 28,
        "source_size": {"width": 1024, "height": 1536},
        "parts": parts,
        "layout": {
            "distribution": "space-evenly",
            "preserve_aspect_ratio": True,
            "minimum_tiles": 1,
            "maximum_tiles": 32,
        },
    }
    original_asset_path = module._frame_asset_path
    module._frame_asset_path = lambda source: source

    for width, height in expected_counts:
        part_scale = min(width, height) / 1024 * 0.28
        placements = module._edge_repeat_layout(width, height, part_sizes, part_scale)
        assert placements
        assert {placement[0] for placement in placements} == set(part_sizes)
        for edge, expected in expected_counts[(width, height)].items():
            assert sum(placement[0] == edge for placement in placements) == expected
        for key, x, y, draw_width, draw_height in placements:
            source_width, source_height = part_sizes[key]
            assert abs(draw_width / draw_height - source_width / source_height) < 1e-6
            assert x >= -1e-6 and y >= -1e-6
            assert x + draw_width <= width + 1e-6
            assert y + draw_height <= height + 1e-6

        layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        element = {
            "type": "frame",
            "frame_preset_id": preset_id,
            "frame_mode": "edge-repeat",
            "frame_scale": 28,
            "fit_to_canvas": True,
            "opacity": 1,
        }
        assert module._draw_frame_asset(layer, element, 1, width, height)
        assert layer.getchannel("A").getbbox() is not None
        center = layer.getpixel((width // 2, height // 2))
        assert center[3] == 0, f"Center must remain transparent at {width}x{height}"

    module._frame_asset_path = original_asset_path

limited = module._edge_repeat_layout(
    1024,
    1536,
    part_sizes,
    0.28,
    {"minimum_tiles": 1, "maximum_tiles": 2},
)
for edge in ("edge_top", "edge_bottom", "edge_left", "edge_right"):
    assert sum(placement[0] == edge for placement in limited) <= 2

oversized_edges = dict(part_sizes)
for edge in ("edge_top", "edge_bottom"):
    oversized_edges[edge] = (2000, 320)
for edge in ("edge_left", "edge_right"):
    oversized_edges[edge] = (320, 2000)
corners_only = module._edge_repeat_layout(1024, 1024, oversized_edges, 1)
assert {placement[0] for placement in corners_only} == {
    "corner_tl", "corner_tr", "corner_bl", "corner_br",
}

print("frame edge-repeat render: pass")
