import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.modules["folder_paths"] = types.SimpleNamespace(get_output_directory=lambda: ".")
module_path = ROOT / "nodes_speech_bubble.py"
spec = importlib.util.spec_from_file_location("speech_bubble_frame_discovery_test", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def write_image(path, size=(32, 32)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, (255, 255, 255, 255)).save(path, format="WEBP", lossless=True)


original_root = module._FRAME_ROOT
original_normalize = module._normalize_discovered_frame_manifest
original_presets = module._FRAME_PRESETS
with tempfile.TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    frame_dir = temporary_root / "test-edge-repeat-frame"
    write_image(frame_dir / "preview.webp")
    write_image(frame_dir / "runtime.webp", (64, 96))
    for filename in (
        "corner_tl.webp", "corner_tr.webp", "corner_bl.webp", "corner_br.webp",
        "edge_top.webp", "edge_bottom.webp", "edge_left.webp", "edge_right.webp",
    ):
        write_image(frame_dir / "parts" / filename)

    payload = {
        "schemaVersion": 1,
        "id": "test-edge-repeat-frame",
        "label": "Test Edge Repeat Frame",
        "renderMode": "edge-repeat",
        "defaultScale": 28,
        "runtimeAsset": "runtime.webp",
        "preview": "preview.webp",
        "parts": {
            "cornerTL": "parts/corner_tl.webp",
            "cornerTR": "parts/corner_tr.webp",
            "cornerBL": "parts/corner_bl.webp",
            "cornerBR": "parts/corner_br.webp",
            "edgeTop": "parts/edge_top.webp",
            "edgeBottom": "parts/edge_bottom.webp",
            "edgeLeft": "parts/edge_left.webp",
            "edgeRight": "parts/edge_right.webp",
        },
        "edgeLayout": {
            "distribution": "space-evenly",
            "preserveAspectRatio": True,
            "maximumTiles": 32,
        },
    }
    (frame_dir / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    module._FRAME_ROOT = temporary_root

    preset = module._normalize_discovered_frame_manifest(payload, frame_dir)
    assert preset["id"] == "test-edge-repeat-frame"
    assert preset["render_mode"] == "edge-repeat"
    assert preset["default_scale"] == 28
    assert preset["layout"]["maximum_tiles"] == 32

    module._FRAME_PRESETS = {preset["id"]: preset}
    catalog = module.get_frame_asset_catalog()
    public = next(frame for frame in catalog["frames"] if frame["id"] == preset["id"])
    assert public["renderMode"] == "edge-repeat"
    assert public["defaultScale"] == 28
    assert len(public["parts"]) == 8

    minimal = dict(payload)
    minimal.pop("runtimeAsset", None)
    minimal["preview"] = "preview.webp"
    minimal_preset = module._normalize_discovered_frame_manifest(minimal, frame_dir)
    assert minimal_preset["asset_src"] == ""
    assert minimal_preset["asset_src_2x"] == ""
    assert minimal_preset["preview_src"].endswith("/preview.webp")
    assert len(minimal_preset["parts"]) == 8

    decorated_dir = temporary_root / "test-decorated-border"
    write_image(decorated_dir / "preview.webp")
    for filename in ("corner_tl.webp", "corner_tr.webp", "corner_bl.webp", "corner_br.webp", "bunny.webp"):
        write_image(decorated_dir / "parts" / filename)
    decorated_payload = {
        "schemaVersion": 1,
        "id": "test-decorated-border",
        "label": "Test Decorated Border",
        "renderMode": "decorated-border",
        "defaultScale": 28,
        "preview": "preview.webp",
        "baseBorder": {
            "shape": "rounded-rectangle",
            "radius": 40,
            "layers": [{"color": "#ffffff", "width": 12, "style": "solid"}],
        },
        "decorations": {
            "corners": {
                "topLeft": "parts/corner_tl.webp", "topRight": "parts/corner_tr.webp",
                "bottomLeft": "parts/corner_bl.webp", "bottomRight": "parts/corner_br.webp",
            },
            "items": {"bunny": "parts/bunny.webp"},
            "edges": {"top": ["bunny"], "bottom": ["bunny"], "left": ["bunny"], "right": ["bunny"]},
            "layout": {"distribution": "space-evenly", "preserveAspectRatio": True},
        },
    }
    decorated = module._normalize_discovered_frame_manifest(decorated_payload, decorated_dir)
    assert decorated["render_mode"] == "decorated-border"
    assert decorated["asset_src"] == ""
    assert decorated["preview_src"].endswith("/preview.webp")
    assert decorated["base_border"]["layers"][0]["style"] == "solid"
    assert decorated["decorated_edges"]["top"] == ["bunny"]

    missing_runtime = dict(minimal)
    missing_runtime["renderMode"] = "full-overlay"
    try:
        module._normalize_discovered_frame_manifest(missing_runtime, frame_dir)
        raise AssertionError("full-overlay must still require runtimeAsset")
    except ValueError as error:
        assert "missing asset path" in str(error)

    unsafe = dict(payload)
    unsafe["runtimeAsset"] = "../outside.webp"
    try:
        module._normalize_discovered_frame_manifest(unsafe, frame_dir)
        raise AssertionError("Path traversal must be rejected")
    except ValueError as error:
        assert "unsafe asset path" in str(error)

    unknown = dict(payload)
    unknown["renderMode"] = "unknown-mode"
    try:
        module._normalize_discovered_frame_manifest(unknown, frame_dir)
        raise AssertionError("Unknown render mode must be rejected")
    except ValueError as error:
        assert "unsupported renderMode" in str(error)

    invalid_root = temporary_root / "invalid"
    (invalid_root / "bad-json").mkdir(parents=True)
    (invalid_root / "bad-json" / "manifest.json").write_text("{", encoding="utf-8")
    (invalid_root / "unknown-mode").mkdir()
    (invalid_root / "unknown-mode" / "manifest.json").write_text(
        json.dumps({"schemaVersion": 1, "id": "unknown", "label": "Unknown", "renderMode": "future"}),
        encoding="utf-8",
    )
    module._FRAME_ROOT = invalid_root
    discovered, warnings = module._discover_frame_assets()
    assert discovered == {}
    assert len(warnings) == 2

    for folder_name in ("duplicate-a", "duplicate-b"):
        folder = invalid_root / folder_name
        folder.mkdir()
        (folder / "manifest.json").write_text("{}", encoding="utf-8")
    module._normalize_discovered_frame_manifest = lambda _payload, _folder: {"id": "duplicate"}
    discovered, warnings = module._discover_frame_assets()
    assert list(discovered) == ["duplicate"]
    assert any("duplicate discovered id" in warning for warning in warnings)

module._FRAME_ROOT = original_root
module._normalize_discovered_frame_manifest = original_normalize
module._FRAME_PRESETS = original_presets

print("frame asset discovery: pass")
