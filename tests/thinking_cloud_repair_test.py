from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "web" / "speech-bubble-editor.html").read_text(encoding="utf-8")
SVG = (ROOT / "web" / "assets" / "shapes" / "bubbles" / "thought-cloud.svg").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "web" / "assets" / "shapes" / "manifest.json").read_text(encoding="utf-8"))

assert "fixedPathPreset" in HTML
assert "isFixedPathItem" in HTML
assert "user_modified_path" in HTML

preset = next(item for item in MANIFEST["presets"] if item["id"] == "base-thought")
assert preset["tuning"]["family"] == "fixed-cloud"
assert preset["fixed_path"] is True
assert preset["allow_morph"] is False
assert preset["allow_path_edit"] is False
assert preset["lock_aspect_ratio"] is True
assert preset["defaults"]["shadow_enabled"] is False

path_data = re.search(r'id="bubble-shape"\s+d="([^"]+)"', SVG).group(1)
assert path_data.count(" C ") >= 10, path_data.count(" C ")
assert "L " not in path_data
assert "Fixed Japanese manga thinking cloud" in SVG
print("thinking cloud repair test passed")
