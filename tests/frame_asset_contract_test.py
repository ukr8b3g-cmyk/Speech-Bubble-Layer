import importlib.util
import json
import sys
import types
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
FRAME_ROOT = ROOT / "web" / "assets" / "frames"
LEGACY_MANIFEST = json.loads((FRAME_ROOT / "manifest.json").read_text(encoding="utf-8"))

contract = LEGACY_MANIFEST["asset_contract"]
assert contract["nine_slice_raster"]["minimum_short_side"] == 1024
assert contract["nine_slice_raster"]["warn_scale"] == 1.25
assert contract["nine_slice_raster"]["replace_scale"] == 1.5
assert set(contract["full_overlay_raster"]["fit_modes"]) == {"cover", "contain", "stretch", "tile"}
assert set(contract["svg"]["require"]) == {"width", "height", "viewBox"}

sys.modules["folder_paths"] = types.SimpleNamespace(get_output_directory=lambda: ".")
module_path = ROOT / "nodes_speech_bubble.py"
spec = importlib.util.spec_from_file_location("speech_bubble_frame_contract_test", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

catalog = module.get_frame_asset_catalog()
assert catalog["schemaVersion"] == 1
ids = [frame["id"] for frame in catalog["frames"]]
assert len(ids) == len(set(ids)), "Frame ids must be unique"
assert "frame-border" in ids and "black-border" in ids

local_manifests = sorted(FRAME_ROOT.glob("*/manifest.json"))
for manifest_path in local_manifests:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schemaVersion"] in {1, 2, 3}
    preset = module._normalize_discovered_frame_manifest(payload, manifest_path.parent)
    assert preset["id"] in ids
    for source in [preset.get("asset_src"), preset.get("asset_src_2x"), preset.get("preview_src")]:
        if source:
            assert module._frame_asset_path(source)
    if preset.get("asset_src"):
        runtime_path = Path(module._frame_asset_path(preset["asset_src"]))
        with Image.open(runtime_path) as image:
            assert image.mode == "RGBA"
            assert preset["source_size"] == {"width": image.width, "height": image.height}
            assert min(image.size) >= 1024
    if preset["render_mode"] == "edge-repeat":
        expected = {
            "corner_tl", "corner_tr", "corner_bl", "corner_br",
            "edge_top", "edge_bottom", "edge_left", "edge_right",
        }
        assert set(preset["parts"]) == expected
        assert preset["layout"]["distribution"] == "space-evenly"
        assert preset["layout"]["preserve_aspect_ratio"] is True
        for source in preset["parts"].values():
            part_path = Path(module._frame_asset_path(source))
            assert part_path.is_file()
            with Image.open(part_path) as part:
                assert part.mode == "RGBA"
    if preset["render_mode"] == "decorated-border":
        assert preset["asset_src"] == ""
        assert preset["preview_src"]
        if preset["base_border"].get("enabled", True):
            assert preset["base_border"]["layers"]
        assert set(preset["decorated_corners"]) == {"corner_tl", "corner_tr", "corner_bl", "corner_br"}
        assert set(preset["decorated_edges"]) == {"top", "bottom", "left", "right"}
        for source in [*preset["decorated_corners"].values(), *preset["decorated_items"].values()]:
            if not source:
                continue
            part_path = Path(module._frame_asset_path(source))
            assert part_path.is_file()
            with Image.open(part_path) as part:
                assert part.mode == "RGBA"

print("frame asset contract: pass")
