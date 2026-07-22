# Complete Fix Changelog

## Preview, save, and restore

- Prevented a previous asynchronous image load from overwriting a newer preview.
- Saved editor preview now takes priority over the raw connected input image.
- Added a per-editor `revisionBase`, preventing a reopened editor from sending revisions lower than the node already stores.
- Retained revision checks for live preview and final Save Layout messages.

## Frame system

- Added official `decorated-border` manifest validation, public API serialization, browser rendering, and Python/Pillow rendering.
- Kept `edge-repeat` part assets proportional and un-stretched.
- `edge-repeat` and `decorated-border` no longer require a monolithic `runtimeAsset`.
- Added automatic preview thumbnail support.
- Included an animal decorated-border sample whose line is rendered once and therefore does not break between decorations.

## SVG speech-bubble shapes

- Built-in shape definitions are loaded from `web/assets/shapes/manifest.json` and SVG files.
- Added a second classic oval.
- Revised shape tuning so oval, box, jagged, soft burst, cloud, and heart controls stay within their own shape families.

## Validation

The package includes and passes tests for:

- frame discovery and asset contracts
- edge-repeat browser/Python layout and rendering
- decorated-border browser/Python layout and rendering
- SVG shape assets
- preview lifecycle and persistence
- editor geometry and numeric controls
- frame borders and overlay fit modes
- text tracking
- SFX rendering
- render scheduling and caching
