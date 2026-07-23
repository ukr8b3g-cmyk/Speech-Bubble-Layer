import importlib.util
import sys
import types
from pathlib import Path

from PIL import Image


sys.modules["folder_paths"] = types.SimpleNamespace(get_output_directory=lambda: ".")
sys.modules["torch"] = types.SimpleNamespace()
module_path = Path(__file__).resolve().parents[1] / "nodes_speech_bubble.py"
spec = importlib.util.spec_from_file_location(
    "speech_bubble_emphasis_lines_test",
    module_path,
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


assert module._EMPHASIS_EDGE_OVERSHOOT == 0.035
for preset_id, preset in module._EMPHASIS_PRESETS.items():
    assert preset["line_length"] == 1
    assert preset["length_random"] == 0
    assert preset["inner_random"] == 0.5
    assert preset["taper"] == 1
    source = {**preset, "preset": preset_id, "seed": 1234}
    first = module._generate_emphasis_rays(source, 1024, 1024)
    second = module._generate_emphasis_rays(source, 1024, 1024)
    assert first == second
    assert first
    assert module._validated_emphasis_rays(first)

normalized = module._normalize_emphasis_params({
    **module._EMPHASIS_PRESETS["center"],
    "preset": "center",
    "overshoot": 0.12,
})
assert normalized["overshoot"] == module._EMPHASIS_EDGE_OVERSHOOT

source = {
    **module._EMPHASIS_PRESETS["center"],
    "preset": "center",
    "seed": 987654321,
    "inner_random": 0.0,
    "line_length": 1.0,
    "length_random": 0.0,
}
flat_rays = module._generate_emphasis_rays(source, 1024, 1024)
random_rays = module._generate_emphasis_rays(
    {**source, "inner_random": 0.5},
    1024,
    1024,
)
assert len(flat_rays) == len(random_rays)
assert all(
    flat[1] == random[1] and flat[2] == random[2]
    for flat, random in zip(flat_rays, random_rays)
)
assert any(
    flat[0] != random[0] or flat[3] != random[3]
    for flat, random in zip(flat_rays, random_rays)
)

stored_rays = [[
    [0.45, 0.45],
    [1.05, 0.35],
    [1.05, 0.65],
    [0.45, 0.55],
]]
element = {
    "type": "emphasis_lines",
    "preset": "center",
    "x": 0,
    "y": 0,
    "w": 256,
    "h": 256,
    "color": "#e53935",
    "opacity": 0.75,
    "rays": stored_rays,
}
layer = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
module._draw_emphasis_lines(layer, element, 1)
assert layer.getbbox() is not None
assert module._validated_emphasis_rays(element["rays"]) == stored_rays

overlay = module._render_layer(
    256,
    256,
    {
        "version": 1,
        "canvas": {"width": 256, "height": 256},
        "elements": [element],
    },
    "",
    2,
)
assert overlay.getbbox() is not None

fallback = {
    "type": "emphasis_lines",
    "preset": "side",
    **module._EMPHASIS_PRESETS["side"],
    "seed": 5,
    "x": 0,
    "y": 0,
    "w": 256,
    "h": 256,
    "color": "#000000",
    "opacity": 1,
}
layer = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
module._draw_emphasis_lines(layer, fallback, 1)
assert layer.getbbox() is not None

print("emphasis lines renderer: pass")
