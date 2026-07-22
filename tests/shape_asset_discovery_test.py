import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.modules["folder_paths"] = types.SimpleNamespace(get_output_directory=lambda: ".")
spec = importlib.util.spec_from_file_location("speech_bubble_shape_discovery_test", ROOT / "nodes_speech_bubble.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


original_root = module._SHAPE_ASSET_ROOT
try:
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        (root / "legacy.svg").write_text('<svg viewBox="0 0 10 10"/>', encoding="utf-8")
        (root / "manifest.json").write_text(json.dumps({
            "schemaVersion": 1,
            "presets": [{"id": "shared-shape", "label": "Legacy", "svg": "legacy.svg"}],
        }), encoding="utf-8")
        pack = root / "custom-pack"
        pack.mkdir()
        (pack / "override.svg").write_text('<svg viewBox="0 0 10 10"/>', encoding="utf-8")
        (pack / "manifest.json").write_text(json.dumps({
            "schemaVersion": 1,
            "id": "custom-pack",
            "presets": [{"id": "shared-shape", "label": "Override", "svg": "override.svg"}],
        }), encoding="utf-8")

        module._SHAPE_ASSET_ROOT = root
        module.reload_shape_asset_catalog()
        catalog = module.get_shape_asset_catalog()
        assert catalog["schemaVersion"] == 1
        assert catalog["presets"] == [{
            "id": "shared-shape",
            "label": "Override",
            "svg": "custom-pack/override.svg",
            "packId": "custom-pack",
        }]
        assert any("overridden" in warning for warning in catalog["warnings"])

        (pack / "unsafe.json").write_text("{}", encoding="utf-8")
        bad = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
        bad["presets"].append({"id": "unsafe", "svg": "../unsafe.json"})
        (pack / "manifest.json").write_text(json.dumps(bad), encoding="utf-8")
        module.reload_shape_asset_catalog()
        assert len(module.get_shape_asset_catalog()["presets"]) == 1
finally:
    module._SHAPE_ASSET_ROOT = original_root
    module.reload_shape_asset_catalog()

print("shape asset discovery: pass")
