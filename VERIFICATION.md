# Verification

This package was built from the supplied `ComfyUI-Speech-Bubble(5).zip` and verified before packaging.

## Checks

- Python syntax compilation for the node modules
- JavaScript syntax checks for the editor and ComfyUI extension
- All Python tests under `tests/`
- All JavaScript tests under `tests/`
- Frame discovery and manifest validation
- `edge-repeat` browser/Pillow layout and rendering
- `decorated-border` browser/Pillow layout and rendering
- SVG shape loading and path conversion
- preview revision, save, restore and stale-load protection

Generated caches and development-only directories are excluded from the ZIP.
